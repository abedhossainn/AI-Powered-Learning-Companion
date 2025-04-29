import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import topicService from '../../services/topicService';
import api from '../../services/api';

function TopicDetail() {
  const { topicId } = useParams();
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  
  const [topic, setTopic] = useState(null);
  const [quizzes, setQuizzes] = useState([]);
  const [studyMaterials, setStudyMaterials] = useState([]);
  const [userProgress, setUserProgress] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchTopicData = async () => {
      try {
        setIsLoading(true);
        
        // Fetch topic details using topicService
        const topicData = await topicService.getTopic(topicId);
        setTopic(topicData);
        
        // Fetch quizzes for this topic
        const quizzesResponse = await api.get(`/quizzes/?topic_id=${topicId}`);
        setQuizzes(quizzesResponse.data);
        
        // Fetch study materials for this topic
        try {
          const materialsResponse = await api.get(`/topics/${topicId}/content`);
          setStudyMaterials(materialsResponse.data || []);
        } catch (materialErr) {
          console.error('Error fetching study materials:', materialErr);
          // Non-critical error, continue without study materials
          setStudyMaterials([]);
        }
        
        // Fetch user's progress for this topic if user is logged in
        if (currentUser) {
          const progressData = await topicService.getUserProgress();
          const topicProgress = progressData.find(p => p.topic_id === topicId);
          setUserProgress(topicProgress || { mastery_level: 0 });
        } else {
          setUserProgress({ mastery_level: 0 });
        }
        
      } catch (err) {
        console.error('Error fetching topic data:', err);
        setError('Failed to load topic data. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchTopicData();
  }, [topicId, currentUser]);
  
  const handleStartAdaptiveQuiz = () => {
    // Check if there's an adaptive quiz
    const adaptiveQuiz = quizzes.find(q => q.is_adaptive);
    
    if (adaptiveQuiz) {
      navigate(`/quiz/${adaptiveQuiz.id}`);
    } else {
      setError('No adaptive quiz available for this topic.');
    }
  };
  
  const masteryPercentage = userProgress ? Math.round(userProgress.mastery_level * 100) : 0;
  
  // Function to get mastery status text and color
  const getMasteryStatus = () => {
    if (masteryPercentage >= 80) return { text: 'Mastered', color: 'bg-green-500' };
    if (masteryPercentage >= 50) return { text: 'Practicing', color: 'bg-yellow-500' };
    if (masteryPercentage > 0) return { text: 'Learning', color: 'bg-orange-500' };
    return { text: 'Not Started', color: 'bg-gray-300' };
  };
  
  const masteryStatus = getMasteryStatus();

  return (
    <div>
      <nav className="mb-4">
        <Link to="/topics" className="text-indigo-600 hover:text-indigo-800 flex items-center">
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Topics
        </Link>
      </nav>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4" role="alert">
          <span className="block sm:inline">{error}</span>
        </div>
      )}
      
      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
        </div>
      ) : topic ? (
        <div className="space-y-6">
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-2xl font-bold">{topic.name}</h1>
                <div className="flex items-center mt-2">
                  <div className={`w-3 h-3 rounded-full ${masteryStatus.color} mr-2`}></div>
                  <span className="text-sm text-gray-600">{masteryStatus.text}</span>
                </div>
              </div>
              <button
                onClick={handleStartAdaptiveQuiz}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition"
              >
                Start Adaptive Quiz
              </button>
            </div>
            
            <div className="mt-4">
              <h3 className="font-medium">Description</h3>
              <p className="text-gray-600 mt-1">{topic.description || 'No description available.'}</p>
            </div>
            
            <div className="mt-6">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Mastery Level</span>
                <span>{masteryPercentage}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className={`h-2.5 rounded-full ${masteryStatus.color}`}
                  style={{ width: `${masteryPercentage}%` }}
                ></div>
              </div>
            </div>
          </div>
          
          {/* Study Materials */}
          {studyMaterials.length > 0 && (
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Study Materials</h2>
              <div className="space-y-4">
                {studyMaterials.map(material => (
                  <div key={material.id} className="border border-gray-200 rounded-lg p-4 hover:border-indigo-300 transition">
                    <h3 className="font-medium">{material.title}</h3>
                    <div className="flex items-center mt-2">
                      <span className="text-sm text-gray-500 mr-2">
                        Difficulty: {Math.round(material.difficulty_level * 100)}%
                      </span>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {material.content_type}
                      </span>
                    </div>
                    <Link
                      to={`/content/${material.id}`}
                      className="mt-3 px-3 py-1 bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200 transition inline-flex items-center"
                    >
                      View Material
                      <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                      </svg>
                    </Link>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Available Quizzes */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Available Quizzes</h2>
            
            {quizzes.length === 0 ? (
              <p className="text-gray-600">No quizzes available for this topic yet.</p>
            ) : (
              <div className="space-y-4">
                {quizzes.map(quiz => (
                  <div key={quiz.id} className="border border-gray-200 rounded-lg p-4 hover:border-indigo-300 transition">
                    <div className="flex justify-between items-center">
                      <div>
                        <h3 className="font-medium">{quiz.title}</h3>
                        <p className="text-sm text-gray-600 mt-1">{quiz.description || 'No description available.'}</p>
                        <div className="flex items-center mt-2">
                          {quiz.is_adaptive && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 mr-2">
                              Adaptive
                            </span>
                          )}
                          <span className="text-sm text-gray-500">
                            Difficulty: {Math.round(quiz.difficulty_level * 100)}%
                          </span>
                        </div>
                      </div>
                      <Link
                        to={`/quiz/${quiz.id}`}
                        className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200 transition flex items-center"
                      >
                        Start Quiz
                        <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                        </svg>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          {/* Generate Custom Content */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Generate Custom Study Material</h2>
            <p className="text-gray-600 mb-4">
              Need additional study materials for this topic? Use our AI to generate custom content.
            </p>
            <Link
              to={`/generate?topic=${topicId}`}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition inline-block"
            >
              Create Custom Content
            </Link>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <p className="text-lg text-red-600">Topic not found</p>
          <Link to="/topics" className="text-indigo-600 hover:text-indigo-800 mt-4 inline-block">
            Return to Topics List
          </Link>
        </div>
      )}
    </div>
  );
}

export default TopicDetail;