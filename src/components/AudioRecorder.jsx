// n:\Work\temp\Speech-to-Text Knowledge Assistant\frontend\src\components\AudioRecorder.jsx
import React, { useState, useEffect } from 'react';
import { Mic, Square, Play, Pause, RotateCcw } from 'lucide-react';
import { motion } from 'framer-motion';

const AudioRecorder = ({ onAudioSubmit }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);

  // Mock timer
  useEffect(() => {
    let interval;
    if (isRecording) {
      interval = setInterval(() => setDuration(prev => prev + 1), 1000);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleToggleRecording = () => {
    if (isRecording) {
      // Stop recording (mock)
      setIsRecording(false);
      setAudioBlob(new Blob(['mock-audio'], { type: 'audio/wav' }));
    } else {
      // Start recording
      setIsRecording(true);
      setDuration(0);
      setAudioBlob(null);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-lg border border-slate-100 dark:border-slate-700">
      <div className="flex flex-col items-center gap-6">
        {/* Visualization Area */}
        <div className="h-24 w-full bg-slate-50 dark:bg-slate-900 rounded-xl flex items-center justify-center gap-1 overflow-hidden relative">
          {isRecording ? (
            // Animated Waveform
            Array.from({ length: 20 }).map((_, i) => (
              <motion.div
                key={i}
                className="w-1.5 bg-primary-500 rounded-full"
                animate={{
                  height: [10, Math.random() * 60 + 20, 10],
                }}
                transition={{
                  repeat: Infinity,
                  duration: 0.5,
                  delay: i * 0.05,
                }}
              />
            ))
          ) : (
            <span className="text-slate-400 text-sm">
              {audioBlob ? "Audio captured ready for processing" : "Ready to record"}
            </span>
          )}
        </div>

        {/* Controls */}
        <div className="flex items-center gap-6">
          {audioBlob && !isRecording && (
            <button 
              onClick={() => { setAudioBlob(null); setDuration(0); }}
              className="p-3 rounded-full text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
            >
              <RotateCcw className="w-5 h-5" />
            </button>
          )}

          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={handleToggleRecording}
            className={`p-6 rounded-full shadow-xl transition-all duration-300 ${
              isRecording 
                ? 'bg-red-500 hover:bg-red-600 shadow-red-500/30' 
                : 'bg-primary-600 hover:bg-primary-700 shadow-primary-500/30'
            }`}
          >
            {isRecording ? (
              <Square className="w-8 h-8 text-white fill-current" />
            ) : (
              <Mic className="w-8 h-8 text-white" />
            )}
          </motion.button>

          <div className="w-16 text-center font-mono text-slate-600 dark:text-slate-300">
            {formatTime(duration)}
          </div>
        </div>

        {audioBlob && (
          <motion.button
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            onClick={() => onAudioSubmit(audioBlob)}
            className="w-full py-3 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl font-semibold hover:opacity-90 transition-opacity"
          >
            Process Audio Question
          </motion.button>
        )}
      </div>
    </div>
  );
};

export default AudioRecorder;
