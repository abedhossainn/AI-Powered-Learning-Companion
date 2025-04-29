import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import ReactMarkdown from 'react-markdown';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

function Dashboard() {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [recentQuizzes, setRecentQuizzes] = useState([]);

  // Content Generation states
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedContent, setGeneratedContent] = useState(null);
  
  // Interactive quiz states
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [quizResults, setQuizResults] = useState(null);
  const [isSubmittingQuiz, setIsSubmittingQuiz] = useState(false);
  
  // Add state for flashcards
  const [flippedCards, setFlippedCards] = useState({});
  
  // Form states
  const [contentType, setContentType] = useState('questions');
  const [context, setContext] = useState('');
  const [quantity, setQuantity] = useState(contentType === 'questions' ? 3 : 5);
  const [concept, setConcept] = useState('');
  const [difficulty, setDifficulty] = useState('intermediate');
  
  // Add a function to handle toggling a flashcard
  const toggleFlashcard = (index) => {
    setFlippedCards(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Reset quiz state when generating new content
  useEffect(() => {
    if (generatedContent) {
      setSelectedAnswers({});
      setQuizSubmitted(false);
      setQuizResults(null);
    }
  }, [generatedContent]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setIsLoading(true);
        
        // Fetch recent quiz attempts
        const quizzesResponse = await api.get('/quizzes/attempts/user');
        setRecentQuizzes(quizzesResponse.data.slice(0, 5)); // Get the 5 most recent attempts
        
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchDashboardData();
  }, [quizResults]); // Refresh when new quiz results are available

  // Handle selecting an answer for a question
  const handleAnswerSelect = (questionIndex, option) => {
    if (quizSubmitted) return; // Don't allow changes after submission
    
    setSelectedAnswers(prev => ({
      ...prev,
      [questionIndex]: option.charAt(0) // Store just the letter (A, B, C, D)
    }));
  };

  // Submit quiz for grading
  const handleQuizSubmit = async () => {
    if (isSubmittingQuiz || !generatedContent || generatedContent.type !== 'questions') return;
    
    setIsSubmittingQuiz(true);
    
    try {
      // Calculate results
      const totalQuestions = generatedContent.data.length;
      let correctAnswers = 0;
      
      const results = generatedContent.data.map((question, index) => {
        const isCorrect = selectedAnswers[index] === question.correct_answer.charAt(0);
        if (isCorrect) correctAnswers++;
        
        return {
          question: question.text,
          selected_option: selectedAnswers[index],
          correct_answer: question.correct_answer.charAt(0),
          is_correct: isCorrect,
          explanation: question.explanation
        };
      });
      
      const score = correctAnswers / totalQuestions;
      
      // Create a record of this quiz attempt
      const attemptData = {
        quiz_type: 'practice',
        score,
        questions: results
      };
      
      // Save the attempt to the server
      const response = await api.post('/quizzes/practice/attempt', attemptData);
      
      // Update local state
      setQuizResults({
        id: response.data.attempt_id,
        score,
        questions: results
      });
      
      setQuizSubmitted(true);
      
      // Add this attempt to recent quizzes for immediate feedback
      setRecentQuizzes(prev => [
        {
          id: response.data.attempt_id,
          quiz_id: 'practice-' + Date.now(),
          score: score
        },
        ...prev.slice(0, 4) // Keep only 5 most recent
      ]);
      
    } catch (err) {
      console.error('Error submitting quiz:', err);
      setError('Failed to submit quiz. Please try again.');
    } finally {
      setIsSubmittingQuiz(false);
    }
  };

  // Try again with the same questions
  const handleTryAgain = () => {
    setSelectedAnswers({});
    setQuizSubmitted(false);
    setQuizResults(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setGeneratedContent(null);
    setIsGenerating(true);
    
    try {
      let response;
      
      switch (contentType) {
        case 'questions':
          response = await api.post('/generate/questions', {
            context,
            num_questions: Number(quantity)
          });
          setGeneratedContent({
            type: 'questions',
            data: response.data
          });
          break;
          
        case 'flashcards':
          response = await api.post('/generate/flashcards', {
            context,
            num_cards: Number(quantity)
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
      setIsGenerating(false);
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
            
            <div className="mb-4">
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
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              {quizSubmitted ? 'Quiz Results' : 'Quiz Questions'}
            </h3>
            
            {/* Quiz Score Summary (if submitted) */}
            {quizSubmitted && quizResults && (
              <div className="mb-6 p-4 rounded-lg bg-gray-50 border border-gray-200">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="text-lg font-medium">Your Score</h4>
                  <span className="text-xl font-bold">{Math.round(quizResults.score * 100)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div 
                    className={`h-2.5 rounded-full ${
                      quizResults.score >= 0.7 ? 'bg-green-600' : 
                      quizResults.score >= 0.4 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${quizResults.score * 100}%` }}
                  ></div>
                </div>
              </div>
            )}
            
            <div className="space-y-8">
              {generatedContent.data.map((question, index) => {
                const questionId = `question-${index}`;
                const userAnswer = selectedAnswers[index];
                const isCorrect = quizSubmitted && userAnswer === question.correct_answer.charAt(0);
                const isIncorrect = quizSubmitted && userAnswer && userAnswer !== question.correct_answer.charAt(0);
                
                return (
                  <div 
                    key={index} 
                    className={`rounded-lg p-4 border ${
                      !quizSubmitted ? 'border-gray-200' :
                      isCorrect ? 'border-green-200 bg-green-50' :
                      isIncorrect ? 'border-red-200 bg-red-50' :
                      'border-gray-200'
                    }`}
                  >
                    <p className="font-medium mb-4">{`${index + 1}. ${question.text}`}</p>
                    
                    <div className="space-y-2 mb-4">
                      {question.options.map((option, optIndex) => {
                        const optionLetter = option.charAt(0);
                        const isUserSelection = userAnswer === optionLetter;
                        const isCorrectAnswer = question.correct_answer.charAt(0) === optionLetter;
                        
                        return (
                          <div 
                            key={optIndex} 
                            className={`p-3 rounded-md border cursor-pointer ${
                              !quizSubmitted && isUserSelection ? 'border-indigo-400 bg-indigo-50' :
                              quizSubmitted && isCorrectAnswer ? 'border-green-400 bg-green-50' :
                              quizSubmitted && isUserSelection ? 'border-red-400 bg-red-50' :
                              'border-gray-200 hover:border-indigo-300'
                            }`}
                            onClick={() => handleAnswerSelect(index, option)}
                          >
                            <div className="flex items-center">
                              <div className={`h-5 w-5 mr-3 flex items-center justify-center rounded-full border ${
                                !quizSubmitted && isUserSelection ? 'border-indigo-600 bg-indigo-600 text-white' :
                                quizSubmitted && isCorrectAnswer ? 'border-green-600 bg-green-600 text-white' :
                                quizSubmitted && isUserSelection ? 'border-red-600 bg-red-600 text-white' :
                                'border-gray-400'
                              }`}>
                                <span className="text-sm">
                                  {optionLetter}
                                </span>
                              </div>
                              <span className={`${
                                quizSubmitted && isCorrectAnswer ? 'font-medium' : ''
                              }`}>
                                {option.substring(option.indexOf(')') + 1).trim()}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    
                    {/* Explanation (only show after submission) */}
                    {quizSubmitted && question.explanation && (
                      <div className="mt-4 p-3 bg-indigo-50 border border-indigo-100 rounded-md">
                        <h5 className="text-sm font-semibold text-indigo-800 mb-1">Explanation:</h5>
                        <p className="text-sm text-indigo-700">{question.explanation}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            
            {/* Submit or Try Again buttons */}
            <div className="mt-6 flex justify-end">
              {!quizSubmitted ? (
                <button
                  onClick={handleQuizSubmit}
                  disabled={Object.keys(selectedAnswers).length < generatedContent.data.length || isSubmittingQuiz}
                  className={`px-4 py-2 rounded-md ${
                    Object.keys(selectedAnswers).length < generatedContent.data.length || isSubmittingQuiz
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-indigo-600 text-white hover:bg-indigo-700'
                  }`}
                >
                  {isSubmittingQuiz ? 'Submitting...' : 'Submit Quiz'}
                </button>
              ) : (
                <button
                  onClick={handleTryAgain}
                  className="px-4 py-2 rounded-md bg-indigo-100 text-indigo-700 hover:bg-indigo-200"
                >
                  Try Again
                </button>
              )}
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
    <div className="bg-gray-100 min-h-screen">
      {/* Header */}
      <header className="bg-indigo-800 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-xl font-semibold text-white">AI Learning Companion</h1>
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <div className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center text-white">
                {currentUser?.username?.charAt(0)?.toUpperCase() || (currentUser?.email?.charAt(0)?.toUpperCase() || 'U')}
              </div>
              <span className="ml-2 text-white">{currentUser?.username || currentUser?.email}</span>
            </div>
            <button 
              onClick={handleLogout} 
              className="text-white hover:text-indigo-200"
            >
              Logout
            </button>
          </div>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Welcome, {currentUser?.username || currentUser?.email?.split('@')[0]}!</h2>
        </div>
        
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4" role="alert">
            <span className="block sm:inline">{error}</span>
          </div>
        )}
        
        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Recent Quiz Activity */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Recent Quiz Activities</h3>
              
              {recentQuizzes.length === 0 ? (
                <div className="text-center py-8">
                  <p>No quiz attempts yet.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={recentQuizzes.map((quiz, index) => {
                          // Format date if available
                          let dateLabel = '';
                          if (quiz.started_at) {
                            const date = new Date(quiz.started_at);
                            dateLabel = `(${date.getMonth() + 1}/${date.getDate()})`;
                          }
                          
                          // Label most recent as "Latest Quiz", others as "Quiz 2", "Quiz 3", etc.
                          const quizLabel = index === 0 
                            ? `Latest Quiz ${dateLabel}`
                            : `Quiz ${recentQuizzes.length - index} ${dateLabel}`;
                            
                          return { 
                            name: quizLabel, 
                            score: Math.round(quiz.score * 100) 
                          };
                        })}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis domain={[0, 100]} />
                        <Tooltip />
                        <Bar dataKey="score" fill="#8884d8" name="Score %" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  
                  <ul className="divide-y divide-gray-200">
                    {recentQuizzes.map(quiz => (
                      <li key={quiz.id} className="py-2">
                        <Link to={`/quiz/results/${quiz.id}`} className="hover:text-indigo-600 flex justify-between items-center">
                          <div className="flex items-center">
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span>Quiz {quiz.quiz_id.slice(0, 8)}...</span>
                          </div>
                          <span className="font-medium">{Math.round(quiz.score * 100)}%</span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            
            {/* Content Generator */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">AI Content Generator</h3>
              
              <div className="mb-6">
                <h4 className="text-md font-medium text-gray-700 mb-3">What would you like to generate?</h4>
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
              
              <form onSubmit={handleSubmit}>
                {renderForm()}
                
                <div className="mt-6">
                  <button
                    type="submit"
                    disabled={isGenerating}
                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    {isGenerating ? (
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
            
            {/* Generated Content */}
            {renderGeneratedContent()}
          </div>
        )}
      </main>
    </div>
  );
}

export default Dashboard;