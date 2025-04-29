import axios from 'axios';
import { auth, getFreshIdToken } from './firebaseService';

// Detect if we're running on the Cloudflare domain
const isCloudflare = window.location.hostname === 'ailearning.cbtbags.com';

// Use the proper backend endpoint depending on environment
const API_BASE_URL = isCloudflare
  ? ''  // Use empty string for relative URL in production
  : (import.meta.env.VITE_API_BASE_URL || 'http://10.0.0.10:8001');

// API version path - needed for both local and Cloudflare access
const API_VERSION = import.meta.env.VITE_API_VERSION || '/api/v1';

// In Cloudflare production, we'll use /api-proxy to route to the backend
const BASE_URL = isCloudflare
  ? `/api-proxy${API_VERSION}`  // Use proxy path in production
  : `${API_BASE_URL}${API_VERSION}`;  // Use full URL in development

// Create an axios instance with default config
const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for CORS with credentials
  timeout: 15000, // Increased timeout for production environment
});

// Request interceptor for adding Firebase auth token
api.interceptors.request.use(
  async (config) => {
    try {
      // Check if user is authenticated with Firebase
      const currentUser = auth.currentUser;
      if (currentUser) {
        try {
          // Always get a fresh token to ensure it's not expired
          const token = await currentUser.getIdToken(true);
          config.headers['Authorization'] = `Bearer ${token.trim()}`;
          localStorage.setItem('firebaseToken', token); // Keep localStorage in sync
        } catch (tokenError) {
          console.error('Error getting fresh Firebase token:', tokenError);
          
          // Fall back to cached token if available
          const cachedToken = localStorage.getItem('firebaseToken');
          if (cachedToken) {
            config.headers['Authorization'] = `Bearer ${cachedToken.trim()}`;
          }
        }
      } else {
        // Try to get cached token from localStorage as fallback
        const cachedToken = localStorage.getItem('firebaseToken');
        if (cachedToken) {
          config.headers['Authorization'] = `Bearer ${cachedToken.trim()}`;
        }
      }
    } catch (error) {
      console.warn('Error setting auth token on request:', error);
    }
    
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.code === 'ECONNABORTED') {
      console.error('Request timeout - API server may be down or unreachable');
    } else if (error.response) {
      console.error(`API Error: ${error.response.status} - ${error.response.statusText}`);
      
      // Handle authentication errors
      if (error.response.status === 401) {
        localStorage.removeItem('firebaseToken');
        
        // Only redirect to login if not already on login page
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
      }
    } 
    // Handle CORS and network errors
    else if (error.message) {
      if (error.message.includes('Network Error')) {
        console.error(`CORS or Network Error: ${error.message}`);
      } else {
        console.error(`API request error: ${error.message}`);
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;