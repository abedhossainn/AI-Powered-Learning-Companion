# AI-Powered Learning Companion

## Table of Contents
- [Project Description](#project-description)
- [Features](#features)
- [AI Techniques and Models](#ai-techniques-and-models)
- [Project Structure](#project-structure)
- [Architecture & Tools](#architecture--tools)
- [Installation & Setup](#installation--setup)
- [API Keys Setup](#api-keys-setup)
- [Login Instructions](#login-instructions)
- [Current Limitations & Future Work](#current-limitations--future-work)
- [Team Members](#team-members)
- [References](#references)

## Project Description
The AI-Powered Learning Companion provides adaptive and personalized learning experiences. Leveraging artificial intelligence, it dynamically adjusts educational content to match individual learning patterns and automates the creation of learning materials.

## Features
- **Adaptive Learning:** Dynamically adjusts quiz and question difficulties based on user performance using models like IRT, RL, and Collaborative Filtering.
- **Automated Content Generation:** Uses Google's Gemini AI for automatic quiz, flashcard, and explanation generation.
- **Personalized Recommendations:** Suggests study paths and content based on user mastery and learning history.
- **User Dashboard:** Visualizes progress, mastery, and personalized recommendations.
- **Topic Management:** Create, update, and organize educational topics and content.

## AI Techniques and Models
- **Item Response Theory (IRT):** Personalizes learning by adjusting quiz difficulty based on user responses.
- **Reinforcement Learning (RL):** Selects optimal quiz progression paths to maximize learning outcomes.
- **Collaborative Filtering:** Recommends personalized study paths based on similar user performance.
- **Google Gemini AI:** Generates educational content, quizzes, and explanations.

## Project Structure
```
AI-Powered-Learning-Companion/
├── backend/                     # Python FastAPI backend
│   ├── app/                     # Main application folder
│   │   ├── api/                 # API routes definition
│   │   │   └── routes/          # API endpoint implementations
│   │   ├── core/                # Core configuration
│   │   ├── db/                  # Database models and configuration
│   │   └── services/            # Business logic services
│   ├── requirements.txt         # Python dependencies
│   └── learning_companion.db    # SQLite database 
├── frontend/                    # React frontend
│   ├── public/                  # Static assets
│   ├── src/                     # Source code
│   │   ├── components/          # React components
│   │   ├── context/             # React contexts
│   │   └── services/            # API services
│   ├── index.html               # Entry HTML file
│   └── package.json             # Node.js dependencies
├── dataconnect/                 # Firebase data connection configuration
└── firebase.json                # Firebase configuration
```

## Architecture & Tools
- **Backend:**
  - Python (FastAPI, SQLAlchemy, Pydantic)
  - AI: Google Generative AI (Gemini)
  - Database: SQLite (default), easily swappable
  - Key dependencies: `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `google-generativeai`, `bcrypt`, `pyjwt`
- **Frontend:**
  - React (Vite, TailwindCSS, Recharts)
  - API integration via Axios
  - React Router for navigation
  - Authentication with Firebase
- **Dev Tools:**
  - ESLint, PostCSS, TailwindCSS
  - Python virtual environment (venv)

## Installation & Setup
1. **Clone the repository:**
   ```
   git clone [repository-url]
   cd AI-Powered-Learning-Companion
   ```

2. **Backend Setup:**
   - Install Python 3.11+
   - Set up and activate virtual environment:
     ```
     cd backend
     python -m venv venv
     source venv/bin/activate  # On Windows: venv\Scripts\activate
     ```
   - Install dependencies:
     ```
     pip install -r requirements.txt
     ```
   - Configure API keys as described in the [API Keys Setup](#api-keys-setup) section
   - Initialize the database:
     ```
     python init_db.py
     ```
   - Start the backend server:
     ```
     uvicorn app.main:app --reload
     ```
   - (Optional) For CORS issues during development:
     ```
     python simple_cors_proxy.py
     ```

3. **Frontend Setup:**
   - Navigate to frontend directory:
     ```
     cd frontend
     ```
   - Install Node.js dependencies:
     ```
     npm install
     ```
   - Start the development server:
     ```
     npm run dev
     ```
   - Build for production:
     ```
     npm run build
     ```

## API Keys Setup
This project uses Google's Gemini AI APIs for content generation. You'll need to set up API keys:

1. **Create a `.env` file in the backend directory** with the following content:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

2. **How to get API keys:**
   - For Gemini: Visit [Google AI Studio](https://ai.google.dev/) to get a Gemini API key

3. **Configuration Options:**
   - You can choose which model to use in the config.py file
   - Model versions can be configured through environment variables: `CONTENT_GENERATION_MODEL` and `GEMINI_MODEL`

**Note:** The application will still run without API keys, but content generation features won't work correctly.

## Login Instructions
After setting up the project:

1. **Firebase Authentication:**
   - The application uses Firebase Authentication for user management
   - Register for a new account using email/password through the application interface
   - Or use social login options if configured in your Firebase project

2. **Access the Application:**
   - Frontend: http://localhost:5173 (or the port specified by your Vite configuration)
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs

3. **API Authentication:**
   - API requests requiring authentication should include the Firebase ID token
   - The frontend automatically handles token management through firebaseService.js
   - Example: `Authorization: Bearer [Firebase-ID-Token]`

4. **Firebase Setup:**
   - Ensure your Firebase configuration is correctly set up in `firebaseService.js`
   - The application expects Firebase Authentication to be enabled in your Firebase project

## Current Limitations & Future Work
- **Planned Enhancements:**
  - Improved adaptive feedback and mastery visualization
  - More robust error handling and user guidance
  - Enhanced content generation capabilities
  - Integration of knowledge tracing algorithms
  - Mobile-responsive UI improvements

## Team Members
- **Syed Abed Hossain** (DV68018, syedabh1@umbc.edu)
- **Shourya Rami** (AD39491, ad39491@umbc.edu)

## References
- Google Gemini AI for content generation
- Recommendation systems: Collaborative Filtering
- Learning adaptation frameworks: IRT, RL
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/)

*Last Updated: April 30, 2025*

