import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../services/api';
import { 
  auth,
  loginWithEmailPassword, 
  registerWithEmailPassword,
  logoutFirebase,
  getCurrentUser,
  resetPassword
} from '../services/firebaseService';
import { onAuthStateChanged } from 'firebase/auth';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export const AuthProvider = ({ children }) => {
  const [firebaseUser, setFirebaseUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Debug environment
  const isCloudflare = window.location.hostname === 'ailearning.cbtbags.com';
  console.log('AuthContext - Running on Cloudflare domain:', isCloudflare);

  // Function to handle login with Firebase Authentication
  const login = async (email, password) => {
    try {
      console.log(`AuthContext: Login attempt with email: ${email}`);
      const user = await loginWithEmailPassword(email, password);
      
      if (user) {
        console.log('AuthContext: Firebase login successful, getting token');
        // Get Firebase ID token for API requests
        try {
          const idToken = await user.getIdToken(true);
          localStorage.setItem('firebaseToken', idToken);
          console.log('AuthContext: Token stored successfully');
          return true;
        } catch (tokenError) {
          console.error('AuthContext: Error getting Firebase token:', tokenError);
          throw tokenError;
        }
      }
      return false;
    } catch (error) {
      console.error('AuthContext: Firebase login error:', error);
      // Important: Rethrow the error so it can be handled by the login component
      throw error;
    }
  };

  // Function to handle registration with Firebase
  const register = async (email, password, displayName) => {
    try {
      console.log(`AuthContext: Registration attempt for email: ${email}`);
      const user = await registerWithEmailPassword(email, password, displayName);
      
      if (user) {
        console.log('AuthContext: Registration successful, getting token');
        try {
          const idToken = await user.getIdToken();
          localStorage.setItem('firebaseToken', idToken);
          return true;
        } catch (tokenError) {
          console.error('AuthContext: Error getting token after registration:', tokenError);
        }
      }
      return false;
    } catch (error) {
      console.error('AuthContext: Registration error:', error);
      throw error;
    }
  };

  // Function to handle password reset
  const handleResetPassword = async (email) => {
    try {
      console.log(`AuthContext: Password reset attempt for email: ${email}`);
      await resetPassword(email);
      return true;
    } catch (error) {
      console.error('AuthContext: Password reset error:', error);
      throw error;
    }
  };

  // Function to handle logout
  const logout = async () => {
    try {
      console.log('AuthContext: Logout attempt');
      await logoutFirebase();
      
      // Clear local storage
      localStorage.removeItem('firebaseToken');
      console.log('AuthContext: Logout successful');
      return true;
    } catch (error) {
      console.error('AuthContext: Firebase logout error:', error);
      return false;
    }
  };

  // Check if user is authenticated on load
  useEffect(() => {
    console.log('AuthContext: Initializing auth state listener');
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      console.log('AuthContext: Auth state changed, user:', user ? `${user.email} (${user.uid})` : 'null');
      setFirebaseUser(user);
      
      if (user) {
        // Refresh token on auth state change
        try {
          console.log('AuthContext: Getting fresh token');
          const idToken = await user.getIdToken(true);
          localStorage.setItem('firebaseToken', idToken);
          console.log('AuthContext: Fresh token stored');
          
          // Verify token works with backend
          try {
            const response = await api.get('/users/me');
            console.log('AuthContext: API verification successful', response.data);
          } catch (apiError) {
            console.error('AuthContext: API verification failed:', apiError);
          }
        } catch (error) {
          console.error('AuthContext: Error getting fresh token:', error);
        }
      } else {
        localStorage.removeItem('firebaseToken');
        console.log('AuthContext: Removed token from storage');
      }
      
      setLoading(false);
    }, (error) => {
      console.error('AuthContext: Auth state change error:', error);
      setLoading(false);
    });
    
    // Clean up subscription
    return () => {
      console.log('AuthContext: Cleaning up auth state listener');
      unsubscribe();
    };
  }, []);

  const value = {
    currentUser: firebaseUser,
    login,
    logout,
    register,
    resetPassword: handleResetPassword,
    isAuthenticated: !!firebaseUser
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};