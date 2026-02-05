// n:\Work\temp\Speech-to-Text Knowledge Assistant\frontend\src\App.jsx
import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import QueryPage from './pages/QueryPage';
import DocumentsPage from './pages/DocumentsPage';
import { checkBackendConnection } from './services/api';

const App = () => {
  // Prevent default drag behavior to stop browser from opening dropped files
  useEffect(() => {
    const handleDragOver = (e) => e.preventDefault();
    const handleDrop = (e) => e.preventDefault();

    window.addEventListener('dragover', handleDragOver);
    window.addEventListener('drop', handleDrop);

    return () => {
      window.removeEventListener('dragover', handleDragOver);
      window.removeEventListener('drop', handleDrop);
    };
  }, []);

  // Check backend connection on mount
  useEffect(() => {
    const verifyConnection = async () => {
      const isConnected = await checkBackendConnection();
      if (isConnected) {
        console.log('✅ Backend connected successfully');
      } else {
        console.warn('⚠️ Backend not reachable (Running in mock mode)');
      }
    };
    verifyConnection();
  }, []);

  return (
    <Router>
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-50 transition-colors duration-300 font-sans selection:bg-primary-500/30">
        {/* Background Gradients */}
        <div className="fixed inset-0 z-0 pointer-events-none">
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-primary-500/10 blur-[100px]" />
          <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-purple-500/10 blur-[100px]" />
        </div>

        {/* Main Content */}
        <div className="relative z-10 flex flex-col min-h-screen">
          <Navbar />
          
          <main className="flex-1 pt-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/query" element={<QueryPage />} />
              <Route path="/documents" element={<DocumentsPage />} />
            </Routes>
          </main>

          <footer className="py-6 text-center text-sm text-slate-500 dark:text-slate-400">
            <p>© 2024 RAG Assistant. Built with React & Tailwind.</p>
          </footer>
        </div>

        {/* Toast Notifications */}
        <Toaster 
          position="bottom-right"
          toastOptions={{
            className: 'dark:bg-slate-800 dark:text-white border dark:border-slate-700',
            style: {
              background: 'var(--tw-bg-opacity)',
              color: 'var(--tw-text-opacity)',
            },
          }}
        />
      </div>
    </Router>
  );
};

export default App;
