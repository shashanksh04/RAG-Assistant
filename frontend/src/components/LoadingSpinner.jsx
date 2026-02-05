import React from 'react';

const LoadingSpinner = () => {
  return (
    <div className="flex justify-center items-center p-2">
      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
    </div>
  );
};

export default LoadingSpinner;