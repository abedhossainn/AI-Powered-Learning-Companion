import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { 
  getAuth, 
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged,
  sendPasswordResetEmail,
  updateProfile,
  connectAuthEmulator,
  setPersistence,
  browserLocalPersistence
} from "firebase/auth";

// Detect environment
const isCloudflare = window.location.hostname === 'ailearning.cbtbags.com';

// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCqGKOe12KGo91UK30qZ4t9RqTSYwhenAo",
  authDomain: "ailearningcompanion-2f9ee.firebaseapp.com",
  projectId: "ailearningcompanion-2f9ee",
  storageBucket: "ailearningcompanion-2f9ee.firebasestorage.app",
  messagingSenderId: "803566445969",
  appId: "1:803566445969:web:6042b21bb1274175672630",
  measurementId: "G-4N6T96H8R8"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = isCloudflare ? getAnalytics(app) : null;
const auth = getAuth(app);

// Set auth persistence to local (this helps with page refreshes)
setPersistence(auth, browserLocalPersistence).catch((error) => {
  console.error('Error setting persistence:', error);
});

// Firebase authentication functions
export const registerWithEmailPassword = async (email, password, displayName) => {
  try {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    // Update the user profile with display name
    if (displayName) {
      await updateProfile(userCredential.user, { displayName });
    }
    
    // Get and store the Firebase ID token
    try {
      const idToken = await userCredential.user.getIdToken(true);
      localStorage.setItem('firebaseToken', idToken);
    } catch (tokenError) {
      console.error('Error getting token after registration:', tokenError);
    }
    
    return userCredential.user;
  } catch (error) {
    console.error("Firebase registration error:", error);
    throw error;
  }
};

export const loginWithEmailPassword = async (email, password) => {
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    
    // Get and store the Firebase ID token
    try {
      const idToken = await userCredential.user.getIdToken(true);
      localStorage.setItem('firebaseToken', idToken);
    } catch (tokenError) {
      console.error('Error getting token after login:', tokenError);
    }
    
    return userCredential.user;
  } catch (error) {
    console.error("Firebase login error:", error.code, error.message);
    throw error;
  }
};

export const logoutFirebase = async () => {
  try {
    await signOut(auth);
    localStorage.removeItem('firebaseToken');
    return true;
  } catch (error) {
    console.error("Firebase logout error:", error);
    throw error;
  }
};

export const resetPassword = async (email) => {
  try {
    await sendPasswordResetEmail(auth, email);
    return true;
  } catch (error) {
    console.error("Password reset error:", error);
    throw error;
  }
};

export const getCurrentUser = () => {
  return new Promise((resolve, reject) => {
    const unsubscribe = onAuthStateChanged(auth, 
      (user) => {
        unsubscribe();
        if (user) {
          // Refresh token when getting current user
          user.getIdToken(true)
            .then(idToken => {
              localStorage.setItem('firebaseToken', idToken);
            })
            .catch(error => {
              console.error('Error refreshing token:', error);
            });
        }
        resolve(user);
      },
      (error) => {
        reject(error);
      }
    );
  });
};

// Function to get a fresh Firebase token
export const getFreshIdToken = async () => {
  const currentUser = auth.currentUser;
  if (currentUser) {
    try {
      const token = await currentUser.getIdToken(true);
      localStorage.setItem('firebaseToken', token);
      return token;
    } catch (error) {
      console.error('Error getting fresh token:', error);
      return null;
    }
  }
  return null;
};

export { auth, app };