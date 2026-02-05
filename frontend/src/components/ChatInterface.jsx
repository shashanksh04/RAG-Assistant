// n:\Work\temp\Speech-to-Text Knowledge Assistant\frontend\src\components\ChatInterface.jsx
import React, { useRef, useEffect } from 'react';
import { Send, Copy, Bot, User, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import LoadingSpinner from './LoadingSpinner';
import toast from 'react-hot-toast';

const MessageBubble = ({ message, isAi }) => {
  const copyToClipboard = () => {
    navigator.clipboard.writeText(message.text);
    toast.success('Copied to clipboard');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className={`flex gap-4 ${isAi ? 'flex-row' : 'flex-row-reverse'}`}
    >
      {/* Avatar */}
      <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-md ${
        isAi 
          ? 'bg-gradient-to-br from-primary-500 to-purple-600 text-white' 
          : 'bg-white dark:bg-slate-700 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-600'
      }`}>
        {isAi ? <Bot className="w-6 h-6" /> : <User className="w-6 h-6" />}
      </div>

      {/* Bubble */}
      <div className={`group relative max-w-[80%] p-4 rounded-2xl shadow-sm ${
        isAi 
          ? 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-tl-none border border-slate-100 dark:border-slate-700' 
          : 'bg-primary-600 text-white rounded-tr-none'
      }`}>
        <p className="leading-relaxed whitespace-pre-wrap">{message.text}</p>
        
        {/* Metadata & Actions */}
        <div className={`flex items-center gap-2 mt-2 text-xs ${isAi ? 'text-slate-400' : 'text-primary-200'}`}>
          <span>{new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          {isAi && (
            <button 
              onClick={copyToClipboard}
              className="opacity-0 group-hover:opacity-100 transition-opacity hover:text-primary-500"
              title="Copy response"
            >
              <Copy className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
};

const ChatInterface = ({ messages, isLoading, onSendMessage }) => {
  const messagesEndRef = useRef(null);
  const [input, setInput] = React.useState('');

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages, isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    onSendMessage(input);
    setInput('');
  };

  return (
    <div className="flex flex-col h-full bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm rounded-2xl border border-white/20 dark:border-slate-700 shadow-xl overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-800/80 flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-primary-500" />
        <h2 className="font-semibold text-slate-800 dark:text-white">AI Assistant</h2>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 text-center p-8">
            <Bot className="w-16 h-16 mb-4 opacity-20" />
            <p className="text-lg font-medium">How can I help you today?</p>
            <p className="text-sm opacity-70">Ask me anything about your documents.</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} isAi={msg.role === 'assistant'} />
          ))
        )}
        
        {isLoading && (
          <div className="flex gap-4">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div className="bg-white dark:bg-slate-800 p-4 rounded-2xl rounded-tl-none border border-slate-100 dark:border-slate-700">
              <LoadingSpinner size="sm" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700">
        <form onSubmit={handleSubmit} className="relative flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your question..."
            className="w-full pl-4 pr-12 py-3 rounded-xl bg-slate-100 dark:bg-slate-900 border-none focus:ring-2 focus:ring-primary-500 text-slate-900 dark:text-white placeholder-slate-500"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-2 p-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
