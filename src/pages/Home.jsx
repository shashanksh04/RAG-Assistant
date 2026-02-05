// n:\Work\temp\Speech-to-Text Knowledge Assistant\frontend\src\pages\Home.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { MessageSquare, FileText, Mic, ArrowRight, Zap, Shield, Database } from 'lucide-react';

const FeatureCard = ({ icon: Icon, title, description, delay }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay, duration: 0.5 }}
    className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm p-6 rounded-2xl border border-white/20 dark:border-slate-700 shadow-lg hover:shadow-xl transition-all hover:-translate-y-1"
  >
    <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-purple-600 rounded-xl flex items-center justify-center mb-4 shadow-lg shadow-primary-500/20">
      <Icon className="w-6 h-6 text-white" />
    </div>
    <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">{title}</h3>
    <p className="text-slate-600 dark:text-slate-400 leading-relaxed">{description}</p>
  </motion.div>
);

const Home = () => {
  return (
    <div className="min-h-[calc(100vh-80px)] flex flex-col justify-center">
      {/* Hero Section */}
      <div className="text-center max-w-4xl mx-auto space-y-8 py-12">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="inline-block px-4 py-1.5 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-sm font-semibold mb-4 border border-primary-200 dark:border-primary-700/50"
        >
          ✨ Next-Gen Knowledge Assistant
        </motion.div>
        
        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-5xl md:text-7xl font-extrabold tracking-tight text-slate-900 dark:text-white"
        >
          Talk to your <br />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary-600 via-purple-600 to-accent-500 animate-gradient">
            Knowledge Base
          </span>
        </motion.h1>

        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto"
        >
          Upload documents, ask questions via voice or text, and get instant, accurate answers powered by RAG technology.
        </motion.p>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Link 
            to="/query"
            className="px-8 py-4 rounded-xl bg-primary-600 hover:bg-primary-700 text-white font-bold text-lg shadow-lg shadow-primary-500/30 transition-all hover:scale-105 flex items-center gap-2"
          >
            Start Asking <ArrowRight className="w-5 h-5" />
          </Link>
          <Link 
            to="/documents"
            className="px-8 py-4 rounded-xl bg-white dark:bg-slate-800 text-slate-700 dark:text-white font-bold text-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
          >
            Manage Docs
          </Link>
        </motion.div>
      </div>

      {/* Features Grid */}
      <div className="grid md:grid-cols-3 gap-6 mt-16">
        <FeatureCard 
          icon={Mic}
          title="Voice Interaction"
          description="Speak naturally to your assistant. Advanced speech-to-text converts your voice queries instantly."
          delay={0.3}
        />
        <FeatureCard 
          icon={Database}
          title="Smart Context"
          description="RAG technology retrieves the most relevant information from your uploaded documents."
          delay={0.4}
        />
        <FeatureCard 
          icon={Shield}
          title="Secure & Private"
          description="Your documents are processed locally or securely in the cloud with enterprise-grade encryption."
          delay={0.5}
        />
      </div>
    </div>
  );
};

export default Home;
