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
  const [timeRemaining, setTimeRemaining] = useState(null);
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
        // Set time limit (10 min default or 1 min per question, whichever is greater)
        const timeLimit = Math.max(10 * 60, response.data.questions.length * 60);
        setTimeRemaining(timeLimit);
      } catch (err) {
        console.error('Error fetching quiz:', err);
        setError('Failed to load quiz. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchQuiz();
  }, [quizId]);

  // Timer countdown
  useEffect(() => {
    if (!timeRemaining || timeRemaining <= 0) return;
    
    const timer = setInterval(() => {
      setTimeRemaining(prevTime => {
        if (prevTime <= 1) {
          clearInterval(timer);
          handleSubmitQuiz();
          return 0;
        }
        return prevTime - 1;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, [timeRemaining]);

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

  // Format time to MM:SS
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
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
                <div className="flex items-center space-x-4">
                  <div className="text-sm text-gray-500">
                    Question {currentQuestionIndex + 1} of {quiz.questions.length}
                  </div>
                  {timeRemaining !== null && (
                    <div className={`font-mono text-lg ${timeRemaining < 60 ? 'text-red-600' : 'text-gray-700'}`}>
                      {formatTime(timeRemaining)}
                    </div>
                  )}
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
                  
                  <div className="space-y-2">
                    {quiz.questions[currentQuestionIndex].options.map((option, index) => {
                      const optionValue = option.substring(0, 2); // Extract "A)", "B)", etc.
                      const optionLetter = optionValue.charAt(0);
                      const isSelected = selectedAnswers[quiz.questions[currentQuestionIndex].id] === optionLetter;
                      const uniqueId = `option-${currentQuestionIndex}-${index}`;
                      
                      return (
                        <div key={index} 
                             className={`flex items-center p-2 rounded cursor-pointer ${isSelected ? 'bg-indigo-50 border border-indigo-200' : 'hover:bg-gray-50'}`}
                             onClick={() => handleAnswerSelect(quiz.questions[currentQuestionIndex].id, optionLetter)}>
                          <input
                            type="radio"
                            id={uniqueId}
                            name={`question-${quiz.questions[currentQuestionIndex].id}`}
                            value={optionLetter}
                            checked={isSelected}
                            onChange={() => {}} // Empty handler since we're handling click on the div
                            className="w-4 h-4 text-indigo-600 border-gray-300 focus:ring-indigo-500"
                          />
                          <label htmlFor={uniqueId} className="ml-2 block w-full cursor-pointer text-sm text-gray-700">
                            {option}
                          </label>
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
                    {index + 1}
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