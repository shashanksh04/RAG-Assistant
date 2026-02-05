// n:\Work\temp\Speech-to-Text Knowledge Assistant\frontend\src\pages\QueryPage.jsx
import React, { useState } from 'react';
import ChatInterface from '../components/ChatInterface';
import AudioRecorder from '../components/AudioRecorder';
import SourceDisplay from '../components/SourceDisplay';
import { motion } from 'framer-motion';
import { askQuestion, askFromAudio } from '../services/api';

const QueryPage = () => {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Hello! I am ready to answer questions about your documents.', timestamp: new Date() }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [sources, setSources] = useState([]);

  const handleSendMessage = async (text) => {
    // Add user message
    const userMsg = { role: 'user', text, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await askQuestion(text);
      
      const aiMsg = { 
        role: 'assistant', 
        text: response.answer, 
        timestamp: new Date() 
      };
      setMessages(prev => [...prev, aiMsg]);
      setSources(response.sources || []);
    } catch (error) {
      console.error("API Error:", error);
      const errorMsg = { 
        role: 'assistant', 
        text: "I'm sorry, I couldn't connect to the server. Please ensure the backend is running.", 
        timestamp: new Date() 
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAudioSubmit = async (audioBlob) => {
    // For audio, we might not know the text immediately, so we show a placeholder or handle it differently
    // If your backend returns the transcribed text, you could update this message later.
    // For now, we'll just send the audio directly to the RAG endpoint.
    
    // Note: If you want to see the text first, you would call a transcribe endpoint, 
    // then call handleSendMessage with the result. 
    // Assuming /ask-audio handles everything:
    
    // We reuse the logic but we can't display the user text immediately without transcription
    // So we might just trigger the same flow if we had the text, or create a specific audio handler.
    // Let's try to transcribe first if possible, or just send it.
    
    // Since we don't have a separate transcribe flow in the UI yet, let's assume direct audio-to-answer
    const userMsg = { role: 'user', text: "🎤 Audio Message", timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await askFromAudio(audioBlob);
      
      const aiMsg = { 
        role: 'assistant', 
        text: response.answer, 
        timestamp: new Date() 
      };
      setMessages(prev => [...prev, aiMsg]);
      setSources(response.sources || []);
    } catch (error) {
      console.error("Audio API Error:", error);
      const errorMsg = { 
        role: 'assistant', 
        text: "Error processing audio query.", 
        timestamp: new Date() 
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-[calc(100vh-100px)] grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Left Column: Chat */}
      <div className="lg:col-span-8 h-full flex flex-col gap-4">
        <ChatInterface 
          messages={messages} 
          isLoading={isLoading} 
          onSendMessage={handleSendMessage} 
        />
      </div>

      {/* Right Column: Tools & Sources */}
      <div className="lg:col-span-4 flex flex-col gap-6 overflow-y-auto pr-2">
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-4">Voice Input</h3>
          <AudioRecorder onAudioSubmit={handleAudioSubmit} />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
        >
          <SourceDisplay sources={sources} />
        </motion.div>
      </div>
    </div>
  );
};

export default QueryPage;
