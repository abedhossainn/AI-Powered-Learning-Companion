import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';

function QuizAttempt() {
  const { quizId } = useParams();
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  
  const [quiz, setQuiz] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Fetch quiz data
  useEffect(() => {
    const fetchQuiz = async () => {
      try {
        setIsLoading(true);
        
        // Check if this is a practice quiz by looking for the "practice-" prefix
        let response;
        if (quizId.startsWith('practice-')) {
          // Use the practice quiz endpoint
          const practiceId = quizId.replace('practice-', '');
          response = await api.get(`/quizzes/practice/${quizId}`);
        } else {
          // Regular quiz endpoint
          response = await api.get(`/quizzes/${quizId}`);
        }
        
        setQuiz(response.data);
      } catch (err) {
        console.error('Error fetching quiz:', err);
        setError('Failed to load quiz. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchQuiz();
  }, [quizId]);

  const handleAnswerSelect = (questionId, answer) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const handleNextQuestion = () => {
    if (currentQuestionIndex < quiz.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const handleSubmitQuiz = async () => {
    if (isSubmitting) return;
    
    try {
      setIsSubmitting(true);
      
      const response = await api.post('/quizzes/attempt', {
        quiz_id: quizId,
        responses: selectedAnswers
      });
      
      // Navigate to results page with the attempt ID
      navigate(`/quiz/results/${response.data.attempt_id}`);
      
    } catch (err) {
      console.error('Error submitting quiz:', err);
      setError('Failed to submit quiz. Please try again.');
      setIsSubmitting(false);
    }
  };

  // Update cleanOptionText implementation to handle different option formats
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

  return (
    <div className="bg-gray-100 min-h-screen">
      {/* Header */}
      <header className="bg-indigo-800 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <Link to="/" className="text-white hover:text-indigo-200 flex items-center">
                <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                <span className="font-semibold">Return to Dashboard</span>
              </Link>
            </div>
            <h1 className="text-xl font-semibold text-white">Quiz</h1>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
          </div>
        ) : error ? (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded" role="alert">
            <p className="font-bold">Error</p>
            <p>{error}</p>
            <div className="mt-4">
              <Link to="/" className="text-indigo-600 hover:text-indigo-800">
                Return to Dashboard
              </Link>
            </div>
          </div>
        ) : !quiz ? (
          <div>Quiz not found</div>
        ) : (
          <>
            <div className="bg-white shadow rounded-lg p-6">
              <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold">{quiz.title}</h1>
                <div className="text-sm text-gray-500">
                  Question {currentQuestionIndex + 1} of {quiz.questions.length}
                </div>
              </div>
              
              {/* Progress bar */}
              <div className="w-full bg-gray-200 rounded-full h-2.5 mb-6">
                <div 
                  className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300"
                  style={{ width: `${(Object.keys(selectedAnswers).length / quiz.questions.length) * 100}%` }}
                ></div>
              </div>
              
              {/* Question */}
              {quiz.questions.length > 0 && (
                <div className="mb-6">
                  <h2 className="text-lg font-medium mb-4">{quiz.questions[currentQuestionIndex].text}</h2>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {quiz.questions[currentQuestionIndex].options.map((option, index) => {
                      const optionText = typeof option === 'string' ? cleanOptionText(option) : `Option ${index+1}`;
                      const optionLabels = ['A', 'B', 'C', 'D'];
                      const isSelected = selectedAnswers[quiz.questions[currentQuestionIndex].id] === option;
                      
                      return (
                        <div 
                          key={index} 
                          onClick={() => handleAnswerSelect(quiz.questions[currentQuestionIndex].id, option)}
                          className={`
                            border rounded-lg p-4 cursor-pointer transition-all 
                            ${isSelected ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-indigo-300 hover:bg-indigo-50/30'}
                          `}
                        >
                          <div className="flex items-start">
                            <div className={`
                              flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mr-3 font-medium text-sm
                              ${isSelected ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700'}
                            `}>
                              {optionLabels[index]}
                            </div>
                            <div className="flex-1">
                              <span className="block w-full cursor-pointer text-sm text-gray-700">
                                {optionText || `Option ${index+1}`}
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
              
              {/* Navigation buttons */}
              <div className="flex justify-between">
                <button
                  onClick={handlePreviousQuestion}
                  disabled={currentQuestionIndex === 0}
                  className={`px-4 py-2 rounded ${
                    currentQuestionIndex === 0 
                      ? 'bg-gray-200 text-gray-500 cursor-not-allowed' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Previous
                </button>
                
                {currentQuestionIndex < quiz.questions.length - 1 ? (
                  <button
                    onClick={handleNextQuestion}
                    disabled={!selectedAnswers[quiz.questions[currentQuestionIndex].id]}
                    className={`px-4 py-2 rounded ${
                      !selectedAnswers[quiz.questions[currentQuestionIndex].id]
                        ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                        : 'bg-indigo-600 text-white hover:bg-indigo-700'
                    }`}
                  >
                    Next
                  </button>
                ) : (
                  <button
                    onClick={handleSubmitQuiz}
                    disabled={isSubmitting || Object.keys(selectedAnswers).length < quiz.questions.length}
                    className={`px-4 py-2 rounded ${
                      isSubmitting || Object.keys(selectedAnswers).length < quiz.questions.length
                        ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                        : 'bg-green-600 text-white hover:bg-green-700'
                    }`}
                  >
                    {isSubmitting ? 'Submitting...' : 'Submit Quiz'}
                  </button>
                )}
              </div>
            </div>
            
            {/* Question navigation */}
            <div className="bg-white shadow rounded-lg mt-6 p-6">
              <h3 className="text-sm font-medium text-gray-700 mb-4">Question Navigation</h3>
              <div className="flex flex-wrap gap-2">
                {quiz.questions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentQuestionIndex(index)}
                    className={`w-10 h-10 rounded-full flex items-center justify-center text-sm
                      ${currentQuestionIndex === index
                        ? 'bg-indigo-600 text-white'
                        : selectedAnswers[question.id]
                          ? 'bg-green-100 text-green-700 border border-green-300'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                  >
                  </button>
                ))}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default QuizAttempt;