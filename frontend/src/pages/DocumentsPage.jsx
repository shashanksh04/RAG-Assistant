// n:\Work\temp\Speech-to-Text Knowledge Assistant\frontend\src\pages\DocumentsPage.jsx
import React from 'react';
import DocumentUpload from '../components/DocumentUpload';
import { motion } from 'framer-motion';

const DocumentsPage = () => {
  return (
    <div className="max-w-5xl mx-auto py-8">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Knowledge Base</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-2">
          Manage the documents your assistant uses to answer questions.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-xl rounded-3xl p-8 border border-white/20 dark:border-slate-700 shadow-xl"
      >
        <DocumentUpload />
      </motion.div>
    </div>
  );
};

export default DocumentsPage;
