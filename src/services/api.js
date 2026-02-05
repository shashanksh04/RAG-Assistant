import axios from 'axios';

// Default to localhost:8000, or use environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const checkBackendConnection = async () => {
  try {
    // Tries to hit the root or health endpoint
    await api.get('/');
    return true;
  } catch (error) {
    // If we get a 404, the server IS reachable, just the route is missing.
    if (error.response && error.response.status === 404) {
      return true;
    }
    return false;
  }
};

export const askQuestion = async (query, conversationId = null) => {
  const response = await api.post('/ask', { query, conversation_id: conversationId });
  return response.data;
};

export const askFromAudio = async (audioBlob) => {
  const formData = new FormData();
  // Append the audio blob with a filename so the backend recognizes it as a file
  formData.append('audio', audioBlob, 'recording.wav');
  
  const response = await api.post('/ask-audio', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export default api;