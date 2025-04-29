import api from './api';

export const contentService = {
  // Generate learning content
  generateContent: async (topicId, prompt) => {
    const response = await api.post('/content/generate', {
      topic_id: topicId,
      prompt: prompt
    });
    return response.data;
  },
  
  // Generate a quiz for a topic
  generateQuiz: async (topicId, difficulty = 0.5, questionCount = 5) => {
    const response = await api.post('/content/generate-quiz', {
      topic_id: topicId,
      difficulty_level: difficulty,
      question_count: questionCount
    });
    return response.data;
  },
  
  // Generate an explanation
  generateExplanation: async (conceptText, difficulty = 0.5) => {
    const response = await api.post('/content/explain', {
      concept_text: conceptText,
      difficulty_level: difficulty
    });
    return response.data;
  },
  
  // Get personalized learning recommendations
  getRecommendations: async () => {
    const response = await api.get('/content/recommendations');
    return response.data;
  }
};

export default contentService;