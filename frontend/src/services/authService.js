import api from './api';

export const authService = {
  // Register new user
  register: async (userData) => {
    const response = await api.post('/users/register', userData);
    return response.data;
  },

  // Login user and get token
  login: async (credentials) => {
    try {
      // Create form data for token endpoint
      const formData = new URLSearchParams();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);
      
      console.log('Attempting login with credentials:', {
        username: credentials.username,
        password: '********' // masked for security
      });
      
      // Use specific content type for token endpoint
      const response = await api.post('/users/token', formData.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      console.log('Login successful, token received');
      
      // Store token in localStorage
      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        console.log('Token stored in localStorage');
      }
      
      return response.data;
    } catch (error) {
      console.error('Login failed:', error.message);
      if (error.response) {
        console.error('Response data:', error.response.data);
        console.error('Response status:', error.response.status);
      }
      throw error;
    }
  },

  // Get current user
  getCurrentUser: async () => {
    try {
      const response = await api.get('/users/me');
      return response.data;
    } catch (error) {
      console.error('Error getting current user:', error);
      throw error;
    }
  },

  // Log out user
  logout: () => {
    localStorage.removeItem('token');
    console.log('User logged out, token removed');
  },
  
  // Check if user is logged in
  isAuthenticated: () => {
    return !!localStorage.getItem('token');
  }
};

export default authService;