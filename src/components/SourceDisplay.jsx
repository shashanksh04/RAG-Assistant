// n:\Work\temp\Speech-to-Text Knowledge Assistant\frontend\src\components\SourceDisplay.jsx
import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const SourceCard = ({ source, index }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden bg-white dark:bg-slate-800/50"
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
            <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="text-left">
            <h4 className="font-medium text-slate-900 dark:text-slate-100 text-sm">{source.filename}</h4>
            <p className="text-xs text-slate-500 dark:text-slate-400">Page {source.page} • Score: {(source.score * 100).toFixed(0)}%</p>
          </div>
        </div>
        {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            className="overflow-hidden"
          >
            <div className="p-4 pt-0 border-t border-slate-100 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/50">
              <p className="text-sm text-slate-600 dark:text-slate-300 italic leading-relaxed">
                "...{source.content}..."
              </p>
              <div className="mt-3 flex justify-end">
                <button className="text-xs flex items-center gap-1 text-primary-600 dark:text-primary-400 hover:underline">
                  Jump to document <ExternalLink className="w-3 h-3" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

const SourceDisplay = ({ sources }) => {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
        Sources & Citations
      </h3>
      <div className="space-y-3">
        {sources.map((source, idx) => (
          <SourceCard key={idx} source={source} index={idx} />
        ))}
      </div>
    </div>
  );
};

export default SourceDisplay;
