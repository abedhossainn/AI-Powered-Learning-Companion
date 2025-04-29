import api from './api';

export const quizService = {
  // Get all quizzes
  getQuizzes: async (topicId = null, skip = 0, limit = 100) => {
    const params = new URLSearchParams();
    if (topicId) params.append('topic_id', topicId);
    params.append('skip', skip);
    params.append('limit', limit);
    
    const response = await api.get(`/quizzes/?${params.toString()}`);
    return response.data;
  },
  
  // Get quiz details by ID
  getQuizDetails: async (quizId) => {
    const response = await api.get(`/quizzes/${quizId}`);
    return response.data;
  },
  
  // Create a new quiz (for instructors)
  createQuiz: async (quizData) => {
    const response = await api.post('/quizzes/', quizData);
    return response.data;
  },
  
  // Submit a quiz attempt
  submitQuizAttempt: async (attemptData) => {
    const response = await api.post('/quizzes/attempt', attemptData);
    return response.data;
  },
  
  // Get user's quiz attempts
  getUserQuizAttempts: async () => {
    const response = await api.get('/quizzes/attempts/user');
    return response.data;
  }
};

export default quizService;