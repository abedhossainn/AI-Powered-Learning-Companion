import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import ReactMarkdown from 'react-markdown';

function ContentGenerator() {
  const { currentUser } = useAuth();
  const [topics, setTopics] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [generatedContent, setGeneratedContent] = useState(null);
  
  // Form states
  const [contentType, setContentType] = useState('questions');
  const [context, setContext] = useState('');
  const [selectedTopic, setSelectedTopic] = useState('');
  const [quantity, setQuantity] = useState(contentType === 'questions' ? 3 : 5);
  const [concept, setConcept] = useState('');
  const [difficulty, setDifficulty] = useState('intermediate');
  
  // Add state for tracking which flashcards are flipped
  const [flippedCards, setFlippedCards] = useState({});

  // Add function to handle toggling a flashcard
  const toggleFlashcard = (index) => {
    setFlippedCards(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };
  
  // Function to clean option text by removing any prefixes
  const cleanOptionText = (option) => {
    // If option is not a string, return empty string
    if (typeof option !== 'string') {
      return '';
    }
    
    // Check if option contains newlines (which happens when letter and text are separated)
    if (option.includes('\n')) {
      // Get everything after the first newline
      return option.split('\n').slice(1).join('\n').trim();
    }
    
    // Remove any leading alphanumeric characters followed by a delimiter and space
    return option.replace(/^[A-Za-z0-9]+[)\.:\-]?\s*/, '').trim();
  };
  
  // Fetch available topics
  useEffect(() => {
    const fetchTopics = async () => {
      try {
        const response = await api.get('/topics/');
        setTopics(response.data);
      } catch (err) {
        console.error('Error fetching topics:', err);
        setError('Failed to load topics. Please try again later.');
      }
    };
    
    fetchTopics();
  }, []);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setGeneratedContent(null);
    setIsLoading(true);
    
    try {
      let response;
      
      switch (contentType) {
        case 'questions':
          response = await api.post('/generate/questions', {
            context,
            num_questions: Number(quantity),
            topic_id: selectedTopic || undefined
          });
          setGeneratedContent({
            type: 'questions',
            data: response.data
          });
          break;
          
        case 'flashcards':
          response = await api.post('/generate/flashcards', {
            context,
            num_cards: Number(quantity),
            topic_id: selectedTopic || undefined
          });
          setGeneratedContent({
            type: 'flashcards',
            data: response.data
          });
          break;
          
        case 'explanation':
          response = await api.post('/generate/explanation', {
            concept,
            difficulty
          });
          setGeneratedContent({
            type: 'explanation',
            data: response.data
          });
          break;
          
        default:
          setError('Invalid content type selected');
      }
    } catch (err) {
      console.error('Error generating content:', err);
      setError(err.response?.data?.detail || 'Failed to generate content. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Render appropriate form based on content type
  const renderForm = () => {
    switch (contentType) {
      case 'questions':
      case 'flashcards':
        return (
          <>
            <div className="mb-4">
              <label htmlFor="context" className="block text-sm font-medium text-gray-700 mb-1">
                Input Text
              </label>
              <textarea
                id="context"
                rows={6}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter the educational text you want to generate content from..."
                value={context}
                onChange={(e) => setContext(e.target.value)}
                required
              />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label htmlFor="quantity" className="block text-sm font-medium text-gray-700 mb-1">
                  Number of {contentType === 'questions' ? 'Questions' : 'Flashcards'}
                </label>
                <input
                  type="number"
                  id="quantity"
                  min="1"
                  max="10"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                />
              </div>
              
              <div>
                <label htmlFor="topic" className="block text-sm font-medium text-gray-700 mb-1">
                  Topic (Optional)
                </label>
                <select
                  id="topic"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  value={selectedTopic}
                  onChange={(e) => setSelectedTopic(e.target.value)}
                >
                  <option value="">-- Select a topic --</option>
                  {topics.map((topic) => (
                    <option key={topic.id} value={topic.id}>
                      {topic.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </>
        );
        
      case 'explanation':
        return (
          <>
            <div className="mb-4">
              <label htmlFor="concept" className="block text-sm font-medium text-gray-700 mb-1">
                Concept to Explain
              </label>
              <input
                type="text"
                id="concept"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter the concept you want explained..."
                value={concept}
                onChange={(e) => setConcept(e.target.value)}
                required
              />
            </div>
            
            <div className="mb-4">
              <label htmlFor="difficulty" className="block text-sm font-medium text-gray-700 mb-1">
                Difficulty Level
              </label>
              <select
                id="difficulty"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>
          </>
        );
        
      default:
        return null;
    }
  };
  
  // Render generated content based on type
  const renderGeneratedContent = () => {
    if (!generatedContent) return null;
    
    switch (generatedContent.type) {
      case 'questions':
        return (
          <div className="bg-white shadow rounded-lg p-6 mt-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Generated Questions</h3>
            <div className="space-y-6">
              {generatedContent.data.map((question, index) => (
                <div key={index} className="border-l-4 border-indigo-500 pl-4">
                  <p className="font-medium mb-2">{question.text}</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    {question.options.map((option, optIndex) => {
                      const optionText = cleanOptionText(option);
                      const optionLabels = ['A', 'B', 'C', 'D'];
                      const isCorrect = option.startsWith(question.correct_answer);
                      
                      return (
                        <div 
                          key={optIndex} 
                          className={`
                            border rounded-lg p-4 transition-all
                            ${isCorrect ? 'border-green-500 bg-green-50' : 'border-gray-200'}
                          `}
                        >
                          <div className="flex items-start">
                            <div className={`
                              flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mr-3 font-medium text-sm
                              ${isCorrect ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700'}
                            `}>
                              {optionLabels[optIndex]}
                            </div>
                            <div className="flex-1 break-words">
                              <span className={`block text-sm ${isCorrect ? "text-green-700 font-medium" : "text-gray-700"}`}>
                                {optionText}
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  {question.explanation && (
                    <div className="mt-4 p-3 bg-indigo-50 border border-indigo-100 rounded-md">
                      <h5 className="text-sm font-semibold text-indigo-800 mb-1">Explanation:</h5>
                      <p className="text-sm text-indigo-700">{question.explanation}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
        
      case 'flashcards':
        return (
          <div className="bg-white shadow rounded-lg p-6 mt-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Generated Flashcards</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {generatedContent.data.map((flashcard, index) => (
                <div key={index} className="border border-gray-200 rounded-lg cursor-pointer" onClick={() => toggleFlashcard(index)}>
                  <div className="bg-gray-50 p-4 rounded-t-lg">
                    <p className="font-medium">{flashcard.front}</p>
                  </div>
                  {flippedCards[index] && (
                    <div className="p-4 bg-white border-t border-gray-200">
                      <p>{flashcard.back}</p>
                    </div>
                  )}
                  <div className="px-4 py-2 text-center text-sm text-indigo-600">
                    {flippedCards[index] ? 'Click to hide answer' : 'Click to reveal answer'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
        
      case 'explanation':
        return (
          <div className="bg-white shadow rounded-lg p-6 mt-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Explanation of "{concept}"</h3>
            <div className="prose max-w-none">
              <ReactMarkdown>{generatedContent.data}</ReactMarkdown>
            </div>
          </div>
        );
        
      default:
        return null;
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">AI Content Generator</h2>
      
      <div className="bg-white shadow rounded-lg p-6">
        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-3">What would you like to generate?</h3>
          <div className="flex flex-wrap gap-3">
            <button
              className={`px-4 py-2 rounded-full ${contentType === 'questions' ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-800'}`}
              onClick={() => setContentType('questions')}
            >
              Quiz Questions
            </button>
            <button
              className={`px-4 py-2 rounded-full ${contentType === 'flashcards' ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-800'}`}
              onClick={() => setContentType('flashcards')}
            >
              Flashcards
            </button>
            <button
              className={`px-4 py-2 rounded-full ${contentType === 'explanation' ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-800'}`}
              onClick={() => setContentType('explanation')}
            >
              Detailed Explanation
            </button>
          </div>
        </div>
        
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4" role="alert">
            <span className="block sm:inline">{error}</span>
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          {renderForm()}
          
          <div className="mt-6">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Generating...
                </>
              ) : (
                `Generate ${contentType === 'questions' ? 'Quiz Questions' : contentType === 'flashcards' ? 'Flashcards' : 'Explanation'}`
              )}
            </button>
          </div>
        </form>
      </div>
      
      {renderGeneratedContent()}
    </div>
  );
}

export default ContentGenerator;