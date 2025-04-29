import React, { useState } from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function Layout() {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className={`${isSidebarOpen ? 'w-64' : 'w-20'} bg-indigo-800 text-white transition-all duration-300 ease-in-out`}>
        <div className="p-4 flex items-center justify-between">
          {isSidebarOpen ? (
            <h1 className="text-xl font-semibold">Learning Companion</h1>
          ) : (
            <h1 className="text-xl font-semibold">LC</h1>
          )}
          <button onClick={toggleSidebar} className="text-white">
            {isSidebarOpen ? (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              </svg>
            )}
          </button>
        </div>

        <nav className="mt-6">
          <div className="px-4 py-2">
            <Link to="/" className="flex items-center py-2 px-4 text-white hover:bg-indigo-700 rounded-md">
              <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              {isSidebarOpen && <span>Dashboard</span>}
            </Link>
          </div>

          <div className="px-4 py-2">
            <Link to="/topics" className="flex items-center py-2 px-4 text-white hover:bg-indigo-700 rounded-md">
              <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              {isSidebarOpen && <span>Learning Topics</span>}
            </Link>
          </div>

          <div className="px-4 py-2">
            <Link to="/generate" className="flex items-center py-2 px-4 text-white hover:bg-indigo-700 rounded-md">
              <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
              {isSidebarOpen && <span>Generate Content</span>}
            </Link>
          </div>
        </nav>

        {/* User profile at bottom of sidebar */}
        <div className="absolute bottom-0 w-full p-4">
          {currentUser && (
            <div className={`flex ${isSidebarOpen ? 'justify-between' : 'justify-center'} items-center`}>
              <div className="flex items-center">
                <div className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center">
                  {currentUser.username.charAt(0).toUpperCase()}
                </div>
                {isSidebarOpen && (
                  <span className="ml-2 text-sm">{currentUser.username}</span>
                )}
              </div>
              {isSidebarOpen && (
                <button 
                  onClick={handleLogout} 
                  className="text-sm hover:text-indigo-300"
                >
                  Logout
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-auto">
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
            <h1 className="text-lg font-semibold text-gray-900">AI-Powered Learning Companion</h1>
          </div>
        </header>
        <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default Layout;