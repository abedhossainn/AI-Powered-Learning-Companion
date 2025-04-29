import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const { login, currentUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Debug environment
  const isCloudflare = window.location.hostname === 'ailearning.cbtbags.com';
  console.log('Login component - Running on Cloudflare domain:', isCloudflare);

  // Redirect if already logged in
  useEffect(() => {
    if (currentUser) {
      console.log('User already logged in, redirecting to dashboard');
      navigate('/');
    }
  }, [currentUser, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }
    
    try {
      setIsLoading(true);
      setError('');
      
      console.log(`Login attempt - email: ${email}, environment: ${isCloudflare ? 'cloudflare' : 'local'}`);
      const success = await login(email, password);
      
      if (success) {
        console.log('Login successful, redirecting to dashboard');
        // Use a short timeout to allow state to update
        setTimeout(() => {
          navigate('/', { replace: true });
        }, 100);
      } else {
        console.error('Login returned false, but no error was thrown');
        setError('Failed to login. Authentication unsuccessful.');
      }
    } catch (err) {
      console.error('Login error details:', err);
      
      // Handle Firebase-specific error codes
      if (err.code) {
        console.error(`Firebase error code: ${err.code}`);
        switch (err.code) {
          case 'auth/invalid-email':
            setError('Invalid email address format.');
            break;
          case 'auth/user-disabled':
            setError('This account has been disabled.');
            break;
          case 'auth/user-not-found':
            setError('No account found with this email.');
            break;
          case 'auth/wrong-password':
            setError('Incorrect password for this account.');
            break;
          case 'auth/too-many-requests':
            setError('Too many failed login attempts. Please try again later.');
            break;
          case 'auth/network-request-failed':
            setError('Network error. Please check your internet connection and try again.');
            break;
          default:
            setError(`Authentication error: ${err.message}`);
        }
      } else if (err.response) {
        console.error('Non-Firebase error response:', err.response);
        setError(`Login failed: ${err.response.data.detail || 'Unknown error'}`);
      } else {
        console.error('Generic error:', err);
        setError('An error occurred during login. Please check your network connection.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            AI-Powered Learning Companion
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Sign in to your account
          </p>
          {isCloudflare && (
            <p className="mt-1 text-center text-xs text-blue-600">
              Using Cloudflare domain
            </p>
          )}
        </div>
        
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
            <span className="block sm:inline">{error}</span>
          </div>
        )}
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">Email address</label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">Password</label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="text-sm">
              <Link to="/reset-password" className="font-medium text-indigo-600 hover:text-indigo-500">
                Forgot your password?
              </Link>
            </div>
            <div className="text-sm">
              <Link to="/register" className="font-medium text-indigo-600 hover:text-indigo-500">
                Register new account
              </Link>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export default Login;