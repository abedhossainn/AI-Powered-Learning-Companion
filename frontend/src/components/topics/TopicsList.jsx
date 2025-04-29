import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import topicService from '../../services/topicService';

function TopicsList() {
  const { currentUser } = useAuth();
  const [topics, setTopics] = useState([]);
  const [userProgress, setUserProgress] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        
        // Fetch all topics using topicService
        const topicsData = await topicService.getAllTopics();
        setTopics(topicsData);
        
        // Fetch user progress for topics if user is logged in
        if (currentUser) {
          const progressData = await topicService.getUserProgress();
          
          // Convert progress array to object with topic_id as key for easier lookup
          const progressMap = {};
          progressData.forEach(progress => {
            progressMap[progress.topic_id] = progress.mastery_level;
          });
          setUserProgress(progressMap);
        }
      } catch (err) {
        console.error('Error fetching topics:', err);
        setError('Failed to load topics. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, [currentUser]);
  
  // Function to get progress color class based on mastery level
  const getProgressColorClass = (topicId) => {
    const mastery = userProgress[topicId] || 0;
    
    if (mastery >= 0.8) return 'bg-green-500';
    if (mastery >= 0.5) return 'bg-yellow-500';
    if (mastery > 0) return 'bg-orange-500';
    return 'bg-gray-300';
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Learning Topics</h2>
        <div className="flex items-center space-x-2 text-sm">
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-green-500 mr-1"></div>
            <span>Mastered</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-yellow-500 mr-1"></div>
            <span>Practicing</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-orange-500 mr-1"></div>
            <span>Learning</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-gray-300 mr-1"></div>
            <span>Not Started</span>
          </div>
        </div>
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
      ) : topics.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <p className="text-lg text-gray-600">No topics available yet.</p>
          <p className="text-gray-500 mt-2">Check back later for new content.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {topics.map(topic => {
            const masteryLevel = userProgress[topic.id] || 0;
            const masteryPercentage = Math.round(masteryLevel * 100);
            
            return (
              <Link 
                to={`/topics/${topic.id}`}
                key={topic.id}
                className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow duration-300"
              >
                <div className="p-6">
                  <div className="flex justify-between items-start">
                    <h3 className="text-lg font-bold">{topic.name}</h3>
                    <div className="flex items-center">
                      <div className={`w-3 h-3 rounded-full ${getProgressColorClass(topic.id)}`}></div>
                    </div>
                  </div>
                  
                  <p className="text-gray-600 mt-2 line-clamp-2">
                    {topic.description || 'No description available.'}
                  </p>
                  
                  <div className="mt-4">
                    <div className="flex justify-between text-sm text-gray-600 mb-1">
                      <span>Mastery Level</span>
                      <span>{masteryPercentage}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                      <div 
                        className={`h-2.5 rounded-full ${getProgressColorClass(topic.id)}`}
                        style={{ width: `${masteryPercentage}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  <div className="mt-4 flex justify-between items-center">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                      {masteryLevel === 0 ? 'Start Learning' : 'Continue Learning'}
                    </span>
                    <svg className="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default TopicsList;