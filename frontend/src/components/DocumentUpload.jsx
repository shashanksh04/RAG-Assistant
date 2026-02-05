// n:\Work\temp\Speech-to-Text Knowledge Assistant\frontend\src\components\DocumentUpload.jsx
import React, { useCallback, useState, useEffect, useRef } from 'react';
import { UploadCloud, File, X, CheckCircle, Trash2, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import LoadingSpinner from './LoadingSpinner';

const DocumentUpload = () => {
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState([]);

  // Fetch existing documents from backend on mount
  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/documents');
        if (response.ok) {
          const data = await response.json();
          setFiles(data.map(doc => ({
            name: doc.filename,
            size: `${doc.chunk_count} chunks`,
            status: 'completed'
          })));
        }
      } catch (error) {
        console.error("Failed to fetch documents:", error);
      }
    };
    fetchDocuments();
  }, []);

  const handleUploadFiles = async (fileList) => {
    const newFiles = fileList.map(file => ({
      name: file.name,
      size: `${(file.size / 1024 / 1024).toFixed(2)} MB`,
      status: 'uploading'
    }));

    setFiles(prev => [...prev, ...newFiles]);

    for (const file of fileList) {
      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await fetch('http://localhost:8000/api/v1/ingest', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Upload failed');
        }

        const result = await response.json();
        
        setFiles(prev => prev.map(f => 
          f.name === file.name 
            ? { ...f, status: 'completed', size: `${result.chunks_ingested} chunks` } 
            : f
        ));
        toast.success(`${file.name} uploaded successfully`);
      } catch (error) {
        console.error(error);
        setFiles(prev => prev.map(f => 
          f.name === file.name ? { ...f, status: 'error' } : f
        ));
        toast.error(`Failed to upload ${file.name}`);
      }
    }
  };

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    if (droppedFiles.length > 0) {
      handleUploadFiles(droppedFiles);
    }
  }, []);

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleUploadFiles(Array.from(e.target.files));
    }
  };

  const removeFile = (fileName) => {
    setFiles(files.filter(f => f.name !== fileName));
    toast.success('Document removed');
  };

  return (
    <div className="space-y-8">
      {/* Drop Zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-3xl p-12 text-center transition-all duration-300
          ${isDragging 
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 scale-[1.02]' 
            : 'border-slate-300 dark:border-slate-600 hover:border-primary-400 bg-white/50 dark:bg-slate-800/50'
          }
        `}
      >
        <div className="flex flex-col items-center gap-4">
          <div className={`p-4 rounded-full ${isDragging ? 'bg-primary-100 text-primary-600' : 'bg-slate-100 dark:bg-slate-700 text-slate-500'}`}>
            <UploadCloud className="w-10 h-10" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-800 dark:text-white">
              Drag & Drop your PDFs here
            </h3>
            <p className="text-slate-500 dark:text-slate-400 mt-2">
              or <button 
                onClick={() => fileInputRef.current?.click()}
                className="text-primary-600 font-semibold hover:underline"
              >
                browse files
              </button> from your computer
            </p>
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              multiple 
              accept=".pdf" 
              onChange={handleFileSelect} 
            />
          </div>
          <p className="text-xs text-slate-400">Supported formats: PDF, TXT (Max 10MB)</p>
        </div>
      </div>

      {/* File List */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-slate-800 dark:text-white">Uploaded Documents</h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <AnimatePresence>
            {files.map((file) => (
              <motion.div
                key={file.name}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                layout
                className="group relative bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-red-50 dark:bg-red-900/20 rounded-lg">
                      <File className="w-6 h-6 text-red-500" />
                    </div>
                    <div>
                      <p className="font-medium text-slate-900 dark:text-slate-100 truncate max-w-[150px]" title={file.name}>
                        {file.name}
                      </p>
                      <p className="text-xs text-slate-500">{file.size}</p>
                    </div>
                  </div>
                  <button 
                    onClick={() => removeFile(file.name)}
                    className="text-slate-400 hover:text-red-500 transition-colors p-1"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                
                {/* Status Indicator */}
                <div className="mt-4 flex items-center gap-2 text-xs">
                  {file.status === 'completed' ? (
                    <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 px-2 py-1 rounded-full">
                      <CheckCircle className="w-3 h-3" /> Ready
                    </span>
                  ) : file.status === 'error' ? (
                    <span className="flex items-center gap-1 text-red-600 bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded-full">
                      <AlertCircle className="w-3 h-3" /> Failed
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-primary-600 bg-primary-50 px-2 py-1 rounded-full">
                      <LoadingSpinner size="sm" /> Uploading...
                    </span>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;
