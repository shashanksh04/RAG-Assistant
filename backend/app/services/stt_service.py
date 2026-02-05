import os
import tempfile
import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Any, Union

import torch
import whisper
import numpy as np
import soundfile as sf
import noisereduce as nr
from loguru import logger

from app.core.config import settings

class WhisperSTTService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_size = settings.WHISPER_MODEL_SIZE
        self.cache_file = Path(settings.BASE_DIR) / "data" / "transcription_cache.json"
        self._load_cache()
        logger.info(f"Loading Whisper model '{self.model_size}' on {self.device}...")
        
        try:
            self.model = whisper.load_model(self.model_size, device=self.device)
            logger.info("Whisper model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise RuntimeError(f"Could not load Whisper model: {e}")

    def _load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
            except json.JSONDecodeError:
                self.cache = {}
        else:
            self.cache = {}

    def _save_cache(self):
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def _compute_file_hash(self, file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def preprocess_audio(self, audio_path: Union[str, Path]) -> str:
        """
        Preprocesses audio: converts to 16kHz mono WAV and applies noise reduction.
        Returns path to the processed temporary file.
        """
        audio_path = str(audio_path)
        logger.info(f"Preprocessing audio: {audio_path}")
        
        try:
            # 1. Format Conversion (Standardize to 16kHz Mono WAV)
            # Export to temp file for processing
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                temp_wav_path = temp_wav.name
            
            # Use FFmpeg to convert to 16kHz mono WAV
            command = [
                "ffmpeg", "-y", "-v", "error", "-i", audio_path,
                "-ar", "16000", "-ac", "1", "-f", "wav", temp_wav_path
            ]
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 2. Noise Reduction
            data, rate = sf.read(temp_wav_path)
            # Apply stationary noise reduction
            reduced_noise = nr.reduce_noise(y=data, sr=rate, stationary=True, prop_decrease=0.75)
            
            # Save processed audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as processed_file:
                processed_path = processed_file.name
            sf.write(processed_path, reduced_noise, rate)
            
            # Cleanup intermediate file
            os.remove(temp_wav_path)
            
            return processed_path
            
        except Exception as e:
            logger.warning(f"Preprocessing failed, using original audio: {e}")
            return audio_path

    def _transcribe_chunked(self, audio_path: str, total_duration: float) -> Dict[str, Any]:
        """
        Helper to handle long audio files by splitting them into 10-minute chunks.
        """
        logger.info(f"Audio duration ({total_duration:.2f}s) exceeds threshold. Using chunking strategy.")
        
        # Read the preprocessed wav file
        data, samplerate = sf.read(audio_path)
        chunk_length_samples = 10 * 60 * samplerate  # 10 minutes in samples
        
        full_text = []
        all_segments = []
        confidences = []
        detected_language = "unknown"
        
        # Calculate number of chunks
        num_chunks = int(np.ceil(len(data) / chunk_length_samples))
        
        for i in range(num_chunks):
            start = i * chunk_length_samples
            end = min((i + 1) * chunk_length_samples, len(data))
            chunk_data = data[start:end]
            
            logger.info(f"Processing chunk {i+1}/{num_chunks}...")
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_chunk:
                chunk_path = temp_chunk.name
            
            try:
                sf.write(chunk_path, chunk_data, samplerate)
                
                # Transcribe chunk
                result = self.model.transcribe(chunk_path, fp16=(self.device == "cuda"))
                
                if i == 0:
                    detected_language = result.get("language", "unknown")
                
                text = result.get("text", "").strip()
                if text:
                    full_text.append(text)
                
                # Adjust timestamps and collect segments
                time_offset = start / float(samplerate)
                for segment in result.get("segments", []):
                    segment["start"] += time_offset
                    segment["end"] += time_offset
                    
                    # Collect confidence
                    logprob = segment.get("avg_logprob", -100.0)
                    confidences.append(torch.exp(torch.tensor(logprob)).item())
                    
                    all_segments.append(segment)
                    
            finally:
                if os.path.exists(chunk_path):
                    os.remove(chunk_path)
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        combined_text = " ".join(full_text)
        
        logger.info(f"Chunked transcription complete. Confidence: {avg_confidence:.2f}")
        
        return {
            "text": combined_text,
            "language": detected_language,
            "confidence": avg_confidence,
            "duration": total_duration,
            "segments": all_segments
        }

    def transcribe_audio(self, audio_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Transcribes an audio file to text.
        
        Args:
            audio_path: Path to the audio file.
            
        Returns:
            Dictionary containing text, language, confidence, and segments.
        """
        audio_path = str(audio_path)
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # 1. Check Cache
        file_hash = self._compute_file_hash(audio_path)
        if file_hash in self.cache:
            logger.info(f"Returning cached transcription for {audio_path}")
            return self.cache[file_hash]

        # Preprocess audio (convert format + reduce noise)
        processed_path = self.preprocess_audio(audio_path)
        logger.info(f"Starting transcription for: {processed_path}")
        
        try:
            # Check duration to decide on chunking
            info = sf.info(processed_path)
            duration = info.duration
            
            if duration > 600:  # If longer than 10 minutes
                result = self._transcribe_chunked(processed_path, duration)
                self.cache[file_hash] = result
                self._save_cache()
                return result

            # Whisper handles loading audio and resampling to 16kHz internally
            result = self.model.transcribe(
                processed_path,
                fp16=(self.device == "cuda")
            )
            
            text = result.get("text", "").strip()
            language = result.get("language", "unknown")
            segments = result.get("segments", [])
            
            # Calculate average confidence from segments
            avg_confidence = 0.0
            if segments:
                # avg_logprob is log base e
                logprobs = [s.get("avg_logprob", -100.0) for s in segments]
                # Convert to probability: exp(logprob)
                probs = [torch.exp(torch.tensor(lp)).item() for lp in logprobs]
                avg_confidence = sum(probs) / len(probs)
            
            logger.info(f"Transcription complete. Language: {language}, Confidence: {avg_confidence:.2f}")
            
            return {
                "text": text,
                "language": language,
                "confidence": avg_confidence,
                "duration": duration,
                "segments": segments
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise RuntimeError(f"Transcription failed: {e}")
        finally:
            # Cleanup processed file if it was created
            if processed_path != str(audio_path) and os.path.exists(processed_path):
                os.remove(processed_path)

    def detect_language(self, audio_path: Union[str, Path]) -> str:
        """
        Detects the language of the audio file.
        """
        audio_path = str(audio_path)
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        # load audio and pad/trim it to fit 30 seconds
        audio = whisper.load_audio(audio_path)
        audio = whisper.pad_or_trim(audio)

        # make log-Mel spectrogram and move to the same device as the model
        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)

        # detect the spoken language
        _, probs = self.model.detect_language(mel)
        detected_lang = max(probs, key=probs.get)
        
        logger.info(f"Detected language: {detected_lang}")
        return detected_lang