import api from './api';

export const topicService = {
  // Get all topics
  getAllTopics: async (skip = 0, limit = 100) => {
    const response = await api.get(`/topics/?skip=${skip}&limit=${limit}`);
    return response.data;
  },
  
  // Get a specific topic by ID
  getTopic: async (topicId) => {
    const response = await api.get(`/topics/${topicId}`);
    return response.data;
  },
  
  // Create a new topic (admin only)
  createTopic: async (topicData) => {
    const response = await api.post('/topics/', topicData);
    return response.data;
  },
  
  // Get user's progress across topics
  getUserProgress: async () => {
    const response = await api.get('/topics/progress/');
    return response.data;
  }
};

export default topicService;