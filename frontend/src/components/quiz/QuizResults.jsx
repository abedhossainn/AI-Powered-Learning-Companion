import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { PieChart, Pie, Cell, Label, ResponsiveContainer } from 'recharts';

function QuizResults() {
  const { attemptId } = useParams();
  const { currentUser } = useAuth();
  
  const [quizAttempt, setQuizAttempt] = useState(null);
  const [quiz, setQuiz] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setIsLoading(true);
        
        // Get the attempt data
        const attemptResponse = await api.get(`/quizzes/attempts/${attemptId}`);
        setQuizAttempt(attemptResponse.data);
        
        // Check if this is a practice quiz by looking for the "practice-" prefix in quiz_id
        const quizId = attemptResponse.data.quiz_id;
        let quizResponse;
        
        if (quizId.startsWith('practice-')) {
          // Use our new practice quiz endpoint
          quizResponse = await api.get(`/quizzes/practice/${quizId}`);
        } else {
          // Use standard quiz endpoint
          quizResponse = await api.get(`/quizzes/${quizId}`);
        }
        
        setQuiz(quizResponse.data);
        
      } catch (err) {
        console.error('Error fetching quiz results:', err);
        setError('Failed to load quiz results. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchResults();
  }, [attemptId]);

  // Calculate statistics
  const calculateStatistics = () => {
    if (!quizAttempt || !quiz) return { score: 0, numCorrect: 0, numIncorrect: 0 };
    
    const score = Math.round(quizAttempt.score * 100);
    
    // Check if questions array exists in quizAttempt
    if (!quizAttempt.questions) {
      // For practice quizzes, the questions might be in quiz_metadata or in the quiz response
      if (quizAttempt.quiz_id.startsWith('practice-') && quiz && quiz.questions) {
        // Get questions from the practice quiz object
        return {
          score,
          numCorrect: Math.round(quizAttempt.score * quiz.questions.length),
          numIncorrect: Math.round((1 - quizAttempt.score) * quiz.questions.length)
        };
      }
      
      // Default if no questions array found
      return { score, numCorrect: 0, numIncorrect: 0 };
    }
    
    // Normal case when questions array exists
    const numCorrect = quizAttempt.questions.filter(q => q.is_correct).length;
    const numIncorrect = quizAttempt.questions.length - numCorrect;
    
    return { score, numCorrect, numIncorrect };
  };
  
  const { score, numCorrect, numIncorrect } = calculateStatistics();
  
  const chartData = [
    { name: 'Correct', value: numCorrect },
    { name: 'Incorrect', value: numIncorrect }
  ];
  const COLORS = ['#10B981', '#EF4444'];
  
  // Get feedback based on score
  const getFeedbackMessage = () => {
    if (score >= 90) return "Excellent work! You've mastered this topic!";
    if (score >= 80) return "Great job! You have a strong understanding of this material.";
    if (score >= 70) return "Good work! You're making good progress.";
    if (score >= 60) return "Not bad! With a little more study, you'll improve.";
    return "Keep practicing! Review the material and try again.";
  };

  // Get a recommended next step
  const getNextStepRecommendation = () => {
    if (!quiz) return { message: "", action: "Return to dashboard", link: "/" };
    
    if (score >= 80) {
      return {
        message: "Ready for more advanced material!",
        action: "Return to dashboard",
        link: "/"
      };
    } else if (score >= 60) {
      return {
        message: "You're making good progress, but should review some concepts.",
        action: "Generate study materials",
        link: "/"
      };
    } else {
      return {
        message: "Let's review this material more thoroughly.",
        action: "Try another quiz",
        link: "/"
      };
    }
  };
  
  const nextStep = getNextStepRecommendation();

  // Function to determine color class based on correct/incorrect
  const getAnswerColorClass = (isCorrect) => {
    return isCorrect ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50';
  };

  // Function to format an answer without re-adding numbering
  const formatAnswer = (answer) => {
    if (!answer) return '';
    
    // Just clean the prefix without re-adding it
    return answer.replace(/^[A-Za-z0-9][\s\)\.\:\-]+\s*/, '').trim();
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
            <h1 className="text-xl font-semibold text-white">Quiz Results</h1>
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
        ) : !quizAttempt || !quiz ? (
          <div>Quiz results not found</div>
        ) : (
          <>
            <div className="bg-white shadow rounded-lg p-6 mb-6">
              <h1 className="text-2xl font-bold mb-2">{quiz.title} - Results</h1>
              <p className="text-gray-600">{quiz.description}</p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
                {/* Score display */}
                <div className="bg-gray-50 p-4 rounded-lg text-center">
                  <h3 className="text-lg font-medium text-gray-700 mb-2">Your Score</h3>
                  <div className="h-32">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={chartData}
                          cx="50%"
                          cy="50%"
                          innerRadius={40}
                          outerRadius={60}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          {chartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index]} />
                          ))}
                          <Label
                            value={`${score}%`}
                            position="center"
                            fill="#111827"
                            style={{ fontSize: '24px', fontWeight: 'bold' }}
                          />
                        </Pie>
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="flex justify-around mt-4 text-sm">
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-green-500 mr-1"></div>
                      <span>Correct: {numCorrect}</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-red-500 mr-1"></div>
                      <span>Incorrect: {numIncorrect}</span>
                    </div>
                  </div>
                </div>
                
                {/* Feedback */}
                <div className="md:col-span-2 bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-lg font-medium text-gray-700 mb-2">Feedback</h3>
                  <p className="text-gray-600 mb-4">{getFeedbackMessage()}</p>
                  
                  <div className="border-t border-gray-200 pt-4">
                    <h4 className="font-medium text-gray-700">Recommended Next Step:</h4>
                    <p className="text-gray-600 mb-2">{nextStep.message}</p>
                    <Link 
                      to={nextStep.link}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition inline-flex items-center"
                    >
                      {nextStep.action}
                      <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                      </svg>
                    </Link>
                  </div>
                  
                  {quizAttempt.mastery_update && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <h4 className="font-medium text-gray-700">Mastery Progress:</h4>
                      <p className="text-gray-600">
                        Your mastery level is now 
                        <span className="font-medium"> {Math.round(quizAttempt.mastery_update * 100)}%</span>
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            {/* Question Review */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Question Review</h2>
              {!quizAttempt.questions && (
                <p className="text-gray-600">Question details are not available for this attempt.</p>
              )}
              {quizAttempt.questions && (
                <div className="space-y-8">
                  {quizAttempt.questions.map((question, index) => {
                    // Practice quiz questions have a different structure
                    const isPracticeQuestion = quizAttempt.quiz_id.startsWith('practice-');
                    const questionText = isPracticeQuestion ? question.question : question.text;
                    const isCorrect = isPracticeQuestion ? question.is_correct : question.is_correct;
                    const userAnswer = isPracticeQuestion ? question.selected_option : question.user_answer;
                    const correctAnswer = isPracticeQuestion ? question.correct_answer : question.correct_answer;
                    const explanation = question.explanation;
                    
                    // Format answers with consistent numbering
                    const formattedUserAnswer = formatAnswer(userAnswer);
                    const formattedCorrectAnswer = formatAnswer(correctAnswer);
                    
                    return (
                      <div 
                        key={question.question_id || `question-${index}`}
                        className={`border-l-4 ${
                          isCorrect ? 'border-green-500' : 'border-red-500'
                        } pl-4`}
                      >
                        <div className="flex justify-between">
                          <h3 className="font-medium">Question {index + 1}</h3>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            isCorrect 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {isCorrect ? 'Correct' : 'Incorrect'}
                          </span>
                        </div>
                        <p className="my-2">{questionText}</p>
                        
                        {/* Show user's answer and correct answer */}
                        <div className="mt-2 space-y-2">
                          <div className={`p-2 border rounded ${getAnswerColorClass(isCorrect)}`}>
                            <p className="text-sm font-medium">Your Answer:</p>
                            <p className={isCorrect ? 'text-green-700' : 'text-red-700'}>
                              {formattedUserAnswer}
                            </p>
                          </div>
                          
                          {!isCorrect && (
                            <div className="p-2 border rounded border-green-200 bg-green-50">
                              <p className="text-sm font-medium">Correct Answer:</p>
                              <p className="text-green-700">{formattedCorrectAnswer}</p>
                            </div>
                          )}
                          
                          {explanation && (
                            <div className="p-2 border rounded border-blue-200 bg-blue-50 mt-2">
                              <p className="text-sm font-medium">Explanation:</p>
                              <p className="text-blue-700">{explanation}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default QuizResults;