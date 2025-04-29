# AI-Powered Learning Companion

## Table of Contents
- [Project Description](#project-description)
- [Features](#features)
- [AI Techniques and Models](#ai-techniques-and-models)
- [Data Sources](#data-sources)
- [Architecture & Tools](#architecture--tools)
- [Installation & Setup](#installation--setup)
- [API Keys Setup](#api-keys-setup)
- [Login Instructions](#login-instructions)
- [Current Limitations & Future Work](#current-limitations--future-work)
- [Team Members](#team-members)
- [References](#references)

## Project Description
The AI-Powered Learning Companion provides adaptive and automated personalized learning experiences. Leveraging artificial intelligence, it dynamically adjusts educational content to match individual learning patterns and automates the creation of learning materials.

## Features
- **Adaptive Learning:** Dynamically adjusts quiz and question difficulties based on user performance using models like IRT, RL, and Collaborative Filtering.
- **Automated Content Generation:** Uses NLP models (T5) and semantic similarity (Sentence-BERT) for automatic quiz, flashcard, and explanation generation.
- **Knowledge Graph Integration:** Fetches supplementary educational materials and maintains pedagogically sound quiz content through hybrid recommenders.
- **Personalized Recommendations:** Suggests study paths and content based on user mastery and learning history.
- **User Dashboard:** (In progress) Visualizes progress, mastery, and personalized recommendations.

## AI Techniques and Models
- **Item Response Theory (IRT):** Personalizes learning by adjusting quiz difficulty based on user responses.
- **Reinforcement Learning (RL):** Selects optimal quiz progression paths to maximize learning outcomes.
- **Collaborative Filtering:** Recommends personalized study paths based on similar user performance.
- **Bayesian Knowledge Tracing (BKT):** Tracks learner's mastery of concepts to adapt content accordingly.
- **Deep Knowledge Tracing (DKT):** Uses neural networks to predict learning outcomes with rich datasets.
- **NLP Models:**
  - **T5** (via Hugging Face Transformers)
  - **Sentence-BERT** (semantic similarity)

## Data Sources
- **Kaggle Educational Datasets:** Diverse educational data for model training and validation.

## Architecture & Tools
- **Backend:**
  - Python (FastAPI, SQLAlchemy, Pydantic)
  - AI/NLP: Hugging Face Transformers, Sentence-Transformers
  - Database: SQLite (default), easily swappable
  - Key dependencies: `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `transformers`, `sentence-transformers`, `torch`, `scikit-learn`, `pandas`
- **Frontend:**
  - React (Vite, TailwindCSS, Recharts)
  - API integration via Axios
- **Dev Tools:**
  - ESLint, PostCSS, Prettier
  - Python virtual environment (venv)

## Installation & Setup
1. **Backend:**
   - Install Python 3.11+
   - `cd backend`
   - `python -m venv venv-311 && venv-311\Scripts\activate`
   - `pip install -r requirements.txt`
   - Configure API keys as described in the [API Keys Setup](#api-keys-setup) section
   - Initialize the database: `python init_db.py`
   - Start the backend server: `uvicorn app.main:app --reload`
   - (Optional) For CORS issues during development: `python simple_cors_proxy.py`
2. **Frontend:**
   - `cd frontend`
   - `npm install`
   - `npm run dev`

## API Keys Setup
This project uses Google's Gemini AI APIs for content generation. You'll need to set up API keys:

1. **Create a `.env` file in the backend directory** with the following content:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

2. **How to get API keys:**
   - For Gemini: Visit [Google AI Studio](https://ai.google.dev/) to get a Gemini API key

3. **Configuration Options:**
   - You can choose which model to use by setting `USE_GEMINI=True` (default) in the config.py file
   - Model versions can be configured through environment variables: `CONTENT_GENERATION_MODEL` and `GEMINI_MODEL`

**Note:** The application will still run without API keys, but content generation features won't work correctly.

## Login Instructions
After setting up the project:

1. **Create Admin User (if not already done):**
   ```
   cd backend
   python create_first_user.py
   ```

2. **Default Admin Credentials:**
   - Username: `admin`
   - Password: `admin123`

3. **Access the Application:**
   - Frontend: http://localhost:5173 (or the port specified by your Vite configuration)
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

4. **API Authentication:**
   - API requests requiring authentication should include the Bearer token received after login
   - Example: `Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

## Current Limitations & Future Work
- **Flashcards, Quiz, and Dashboard pages are not fully functional.**
  - These features are the main targets for future implementation.
- **Planned Enhancements:**
  - Improved adaptive feedback and mastery visualization
  - More robust error handling and user guidance

## Team Members
- **Syed Abed Hossain** (DV68018, syedabh1@umbc.edu)
- **Shourya Rami** (AD39491, ad39491@umbc.edu)

## References
- NLP and semantic similarity frameworks: T5, Sentence-BERT
- Recommendation systems: Collaborative Filtering, Knowledge Graphs
- Learning adaptation frameworks: IRT, RL, BKT, DKT
- [OpenEduCat ERP](https://github.com/openeducat/openeducat_erp)

For detailed references and methodologies, see the project documentation.

