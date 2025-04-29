import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'

// Page components
import Login from './components/auth/Login'
import Register from './components/auth/Register'
import ResetPassword from './components/auth/ResetPassword'
import Dashboard from './components/Dashboard' 
import QuizAttempt from './components/quiz/QuizAttempt'
import QuizResults from './components/quiz/QuizResults'

// Protected route wrapper
const ProtectedRoute = ({ children }) => {
  const { currentUser, isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    console.log("Not authenticated, redirecting to login");
    return <Navigate to="/login" replace />;
  }
  
  // Show loading state while authentication state is being determined
  if (currentUser === null) {
    console.log("Authentication state is loading");
    return <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
    </div>;
  }
  
  return children;
};

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      
      {/* Protected routes - simplified navigation */}
      <Route path="/" element={
        <ProtectedRoute>
          <Dashboard />
        </ProtectedRoute>
      } />
      
      {/* Keep quiz routes for functionality */}
      <Route path="/quiz/:quizId" element={
        <ProtectedRoute>
          <QuizAttempt />
        </ProtectedRoute>
      } />
      <Route path="/quiz/results/:attemptId" element={
        <ProtectedRoute>
          <QuizResults />
        </ProtectedRoute>
      } />
    </Routes>
  );
}

export default App;