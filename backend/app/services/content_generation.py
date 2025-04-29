from typing import List, Dict, Any, Optional, Tuple
import os
import json
import random
import asyncio
import logging
import aiohttp
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Import Google's official Genai client
try:
    import google.generativeai as genai
except ImportError:
    logging.warning("Google Genai library not available. Please install with 'pip install google-generativeai'")

# Import transformers conditionally to avoid errors if not used
use_local_models = os.environ.get("USE_LOCAL_MODELS", "False").lower() == "true"
try:
    if use_local_models:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
    # Temporarily commenting out sentence_transformers to avoid version conflict
    # from sentence_transformers import SentenceTransformer, util
except ImportError:
    if use_local_models:
        logging.warning("Transformers library not available. Local models will not work.")

from ..core.config import settings
from ..db.models import Topic, Quiz, Question, User, Concept, ContentItem
from .knowledge_tracing import KnowledgeTracingService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gemini API client implementation
class GeminiClient:
    """Client for Google's Gemini API using the official Google Genai SDK"""
    
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        
        # Configure the Genai client
        try:
            genai.configure(api_key=self.api_key)
            self.genai_model = genai.GenerativeModel(self.model)
            logger.info(f"Initialized Gemini client with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
            raise
    
    async def chat_completions_create(self, messages, temperature=0.7, max_tokens=None, response_format=None):
        """
        Generate a completion from the Gemini API in a format compatible with OpenAI's API.
        
        Args:
            messages: List of messages in the conversation
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            response_format: Format of the response (JSON or text)
        
        Returns:
            A response object that mimics OpenAI's structure
        """
        try:
            # Extract system message if present
            system_message = None
            user_message = None
            
            for message in messages:
                if message["role"] == "system":
                    system_message = message["content"]
                elif message["role"] == "user":
                    user_message = message["content"]
            
            # Start with system message if provided
            prompt = ""
            if system_message:
                prompt = f"System Instructions: {system_message}\n\n"
            
            if user_message:
                prompt += user_message
            
            # Check if we want JSON response
            if response_format and response_format.get("type") == "json_object":
                prompt += "\n\nPlease format your response as a valid JSON object."
            
            # Set up generation config
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                top_p=0.95,
                top_k=40,
            )
            
            if max_tokens:
                generation_config.max_output_tokens = max_tokens
            
            # Make the API request
            try:
                # Run in a way that works with asyncio
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.genai_model.generate_content(
                        prompt,
                        generation_config=generation_config
                    )
                )
                
                # Extract content from the response
                content = response.text
                
                # Create an OpenAI-like response object
                return type('obj', (object,), {
                    'choices': [
                        type('choice', (object,), {
                            'message': type('message', (object,), {
                                'content': content
                            })
                        })
                    ]
                })
                
            except Exception as e:
                error_text = str(e)
                logger.error(f"Gemini API error: {error_text}")
                raise Exception(f"Gemini API error: {error_text}")
                
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            raise

# Initialize Gemini client
gemini_client = GeminiClient()

# Use the appropriate client based on settings
def get_ai_client():
    """Return the appropriate AI client based on settings"""
    # OpenAI client has been removed, always return Gemini client
    return gemini_client

# Model for generated content
class GeneratedContent(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    
# Model for generated quiz
class GeneratedQuizQuestion(BaseModel):
    question_text: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None
    difficulty_level: float = 0.5
    concept_id: Optional[str] = None
    
class GeneratedQuiz(BaseModel):
    title: str
    description: str
    difficulty_level: float = 0.5
    is_adaptive: bool = False
    questions: List[GeneratedQuizQuestion]

# Model for generated flashcard
class Flashcard(BaseModel):
    front: str
    back: str
    concept_id: Optional[str] = None
    difficulty_level: float = 0.5

# Model for practice exercise
class PracticeExercise(BaseModel):
    instruction: str
    problem: str
    solution: str
    hint: Optional[str] = None
    concept_id: Optional[str] = None
    difficulty_level: float = 0.5

class ContentGenerationService:
    """
    Service for generating educational content using AI.
    Supports personalized content based on knowledge states and learning preferences.
    """
    
    @staticmethod
    async def generate_study_materials(
        db: Session,
        topic_id: str,
        user_id: Optional[str] = None,
        difficulty: Optional[float] = None,
        format_type: str = "markdown",
        length: str = "medium"
    ) -> Dict:
        """
        Generate study materials for a given topic, optionally personalized for a user.
        
        Args:
            db: Database session
            topic_id: ID of the topic
            user_id: Optional user ID for personalization
            difficulty: Optional difficulty level (0.0-1.0)
            format_type: Format of content ("markdown", "html", etc)
            length: Length of content ("short", "medium", "long")
            
        Returns:
            Dictionary containing generated study materials
        """
        # Get topic info
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            logger.error(f"Topic with ID {topic_id} not found")
            return {"error": "Topic not found"}
            
        # Get concepts related to this topic
        concepts = db.query(Concept).filter(Concept.topic_id == topic_id).all()
        concept_names = [concept.name for concept in concepts]
        
        # If user_id provided, personalize based on knowledge state
        adaptivity_params = {}
        if user_id:
            adaptivity_params = await KnowledgeTracingService.get_adaptivity_parameters(
                db=db,
                user_id=user_id,
                topic_id=topic_id
            )
            # Override difficulty with personalized difficulty if not explicitly set
            if difficulty is None and "recommended_difficulty" in adaptivity_params:
                difficulty = adaptivity_params["recommended_difficulty"]
        
        # Default difficulty if not set
        if difficulty is None:
            difficulty = 0.5  # Medium difficulty
            
        # Map length to approximate word count
        length_map = {
            "short": 200,
            "medium": 500,
            "long": 1000
        }
        target_length = length_map.get(length, 500)
        
        # Prepare system message based on topic and personalization
        system_message = f"""
You are an AI educational content creator specialized in generating high-quality learning materials.
Create comprehensive study materials on the topic: {topic.name}.
Difficulty level: {difficulty:.1f}/1.0 (where 0 is beginner and 1 is advanced).
Target length: approximately {target_length} words.
Format: {format_type}

The study material should cover these key concepts: {', '.join(concept_names)}.
"""

        # Add personalization if we have user data
        if user_id and adaptivity_params:
            # Add focus concepts if any
            if adaptivity_params.get("focus_concepts"):
                focus_concepts = [f"{c['name']} (current mastery: {c['mastery']:.2f})" 
                                 for c in adaptivity_params["focus_concepts"].values()]
                system_message += f"\nThe user needs additional focus on these concepts: {', '.join(focus_concepts)}."
                
            # Add general mastery level
            system_message += f"\nThe user's average mastery level of this topic is {adaptivity_params.get('average_mastery', 0):.2f}/1.0."
            
        # Create user message to request content
        user_message = f"Please generate study materials for '{topic.name}' that are clear, informative, and engaging."
        
        try:
            # Call AI client for content generation
            ai_client = get_ai_client()
            response = await ai_client.chat_completions_create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            generated_content = response.choices[0].message.content
            
            # Store generated content in database
            content_item = ContentItem(
                topic_id=topic_id,
                user_id=user_id,
                content_type="study_material",
                content=generated_content,
                metadata=json.dumps({
                    "difficulty": difficulty,
                    "format": format_type,
                    "length": length,
                    "personalized": user_id is not None
                })
            )
            db.add(content_item)
            db.commit()
            
            return {
                "topic_id": topic_id,
                "topic_name": topic.name,
                "content": generated_content,
                "difficulty": difficulty,
                "personalized": user_id is not None,
                "content_item_id": content_item.id
            }
            
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            return {"error": f"Content generation failed: {str(e)}"}
    
    @staticmethod
    async def generate_quiz(
        db: Session,
        topic_id: str,
        user_id: Optional[str] = None,
        num_questions: int = 5,
        difficulty: Optional[float] = None
    ) -> Dict:
        """
        Generate a quiz for a given topic, optionally personalized for a user.
        
        Args:
            db: Database session
            topic_id: ID of the topic
            user_id: Optional user ID for personalization
            num_questions: Number of questions to generate
            difficulty: Optional difficulty level (0.0-1.0)
            
        Returns:
            Dictionary containing generated quiz questions
        """
        # Get topic info
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            logger.error(f"Topic with ID {topic_id} not found")
            return {"error": "Topic not found"}
            
        # Get concepts related to this topic
        concepts = db.query(Concept).filter(Concept.topic_id == topic_id).all()
        concept_map = {concept.id: concept.name for concept in concepts}
        
        # Get adaptivity parameters if user_id provided
        adaptivity_params = {}
        if user_id:
            adaptivity_params = await KnowledgeTracingService.get_adaptivity_parameters(
                db=db,
                user_id=user_id,
                topic_id=topic_id
            )
            # Override difficulty if not explicitly set
            if difficulty is None and "recommended_difficulty" in adaptivity_params:
                difficulty = adaptivity_params["recommended_difficulty"]
        
        # Default difficulty if not set
        if difficulty is None:
            difficulty = 0.5  # Medium difficulty
            
        # Prepare the prompt for quiz generation
        system_message = f"""
You are an AI quiz creator specialized in educational assessment.
Create a quiz on the topic: {topic.name}.
Generate {num_questions} multiple-choice questions with 4 options each.
Difficulty level: {difficulty:.1f}/1.0 (where 0 is beginner and 1 is advanced).

The questions should cover these key concepts: {', '.join(concept_map.values())}.

Return the quiz in the following JSON format:
{{
  "questions": [
    {{
      "question_text": "Question text here",
      "concept_id": "concept_id_here",
      "options": [
        {{ "text": "Option A", "is_correct": true }},
        {{ "text": "Option B", "is_correct": false }},
        {{ "text": "Option C", "is_correct": false }},
        {{ "text": "Option D", "is_correct": false }}
      ],
      "explanation": "Explanation of correct answer here"
    }},
    // more questions...
  ]
}}
"""

        # Add personalization if we have user data
        if user_id and adaptivity_params:
            # Focus on concepts with lower mastery
            if adaptivity_params.get("focus_concepts"):
                focus_concepts = list(adaptivity_params["focus_concepts"].keys())
                focus_concept_names = [concept_map.get(c_id, "Unknown") for c_id in focus_concepts]
                
                system_message += f"""
The learner has lower mastery in these concepts: {', '.join(focus_concept_names)}.
Include more questions (at least {min(num_questions // 2, len(focus_concepts))}) related to these concepts.
"""
                
            # Knowledge state info
            system_message += f"\nThe learner's average mastery level of this topic is {adaptivity_params.get('average_mastery', 0):.2f}/1.0."
            
        # Create user message to request quiz
        user_message = f"Please generate a quiz for '{topic.name}' with {num_questions} questions."
        
        try:
            # Call AI client for quiz generation
            ai_client = get_ai_client()
            response = await ai_client.chat_completions_create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=2000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            generated_quiz_json = response.choices[0].message.content
            
            # Parse the generated JSON
            try:
                generated_quiz = json.loads(generated_quiz_json)
                
                # Validate and clean the generated quiz
                if "questions" not in generated_quiz or not isinstance(generated_quiz["questions"], list):
                    logger.error("Invalid quiz format: missing questions array")
                    return {"error": "Generated quiz has invalid format"}
                
                # Store questions in database
                db_questions = []
                for q_data in generated_quiz["questions"]:
                    # Find a matching concept or use the first one
                    concept_id = q_data.get("concept_id")
                    if concept_id not in concept_map and concepts:
                        concept_id = concepts[0].id
                    
                    # Create question
                    question = Question(
                        topic_id=topic_id,
                        concept_id=concept_id,
                        text=q_data.get("question_text"),
                        options=json.dumps(q_data.get("options")),
                        explanation=q_data.get("explanation"),
                        metadata=json.dumps({
                            "difficulty": difficulty,
                            "generated": True,
                            "personalized": user_id is not None
                        })
                    )
                    db.add(question)
                    db_questions.append(question)
                
                # Commit to database
                db.commit()
                
                # Update the generated quiz with database IDs
                for i, question in enumerate(db_questions):
                    generated_quiz["questions"][i]["id"] = question.id
                
                return {
                    "topic_id": topic_id,
                    "topic_name": topic.name,
                    "questions": generated_quiz["questions"],
                    "difficulty": difficulty,
                    "personalized": user_id is not None
                }
                
            except json.JSONDecodeError:
                logger.error("Failed to parse generated quiz JSON")
                return {"error": "Failed to parse generated quiz"}
                
        except Exception as e:
            logger.error(f"Error generating quiz: {str(e)}")
            return {"error": f"Quiz generation failed: {str(e)}"}
    
    @staticmethod
    async def explain_concept(
        db: Session,
        concept_id: str,
        user_id: Optional[str] = None,
        format_type: str = "markdown"
    ) -> Dict:
        """
        Generate an explanation for a specific concept.
        
        Args:
            db: Database session
            concept_id: ID of the concept to explain
            user_id: Optional user ID for personalization
            format_type: Format of explanation ("markdown", "html", etc)
            
        Returns:
            Dictionary containing the explanation
        """
        # Get concept info
        concept = db.query(Concept).filter(Concept.id == concept_id).first()
        if not concept:
            logger.error(f"Concept with ID {concept_id} not found")
            return {"error": "Concept not found"}
            
        # Get topic for this concept
        topic = db.query(Topic).filter(Topic.id == concept.topic_id).first()
        if not topic:
            logger.error(f"Topic for concept {concept_id} not found")
            return {"error": "Parent topic not found"}
            
        # Get user's mastery level if user_id provided
        mastery_level = None
        if user_id:
            kt_service = KnowledgeTracingService()
            mastery_data = await kt_service.get_mastery_level(
                db=db, 
                user_id=user_id,
                concept_id=concept_id
            )
            mastery_level = mastery_data.get("mastery", 0.5)
            
        # Prepare system message based on concept and personalization
        system_message = f"""
You are an educational AI specialized in explaining complex concepts clearly.
Generate a comprehensive explanation of the concept: {concept.name} 
This concept is part of the topic: {topic.name}.

Your explanation should be:
1. Clear and concise
2. Rich in examples
3. In proper markdown format with clear structure
4. Include analogies where appropriate
5. Define any technical terms

FORMAT REQUIREMENTS:
- Use a main heading (# title) for the concept name
- Use subheadings (## subheading) to organize different aspects of the concept
- Break your explanation into meaningful paragraphs (don't use one big paragraph)
- Use bullet points or numbered lists where appropriate
- Bold or italicize key terms and important points
- Include a "Key Takeaways" section at the end with bullet points
- If applicable, use markdown tables to present comparative information
- Use code blocks if explaining programming concepts
"""

        # Add personalization based on mastery level
        if mastery_level is not None:
            if mastery_level < 0.3:
                system_message += """
The learner has low familiarity with this concept.
Focus on fundamentals and use simple language.
Provide more basic examples and build up gradually.
"""
            elif mastery_level > 0.7:
                system_message += """
The learner already has good understanding of this concept.
You can use more advanced terminology and deeper explanations.
Focus on nuances, exceptions, and advanced applications.
"""
            else:
                system_message += """
The learner has intermediate understanding of this concept.
Balance between fundamentals and more advanced aspects.
Reinforce core principles while introducing more complex applications.
"""
                
        # Create user message to request explanation
        user_message = f"Please explain the concept of '{concept.name}' in detail."
        
        try:
            # Call AI client for explanation generation
            ai_client = get_ai_client()
            response = await ai_client.chat_completions_create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=1200,
                temperature=0.6
            )
            
            explanation = response.choices[0].message.content
            
            # Store generated explanation in database
            content_item = ContentItem(
                topic_id=topic.id,
                concept_id=concept_id,
                user_id=user_id,
                content_type="concept_explanation",
                content=explanation,
                metadata=json.dumps({
                    "format": format_type,
                    "personalized": user_id is not None,
                    "mastery_level": mastery_level
                })
            )
            db.add(content_item)
            db.commit()
            
            return {
                "concept_id": concept_id,
                "concept_name": concept.name,
                "topic_name": topic.name,
                "explanation": explanation,
                "personalized": user_id is not None,
                "content_item_id": content_item.id
            }
            
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            return {"error": f"Explanation generation failed: {str(e)}"}
    
    @staticmethod
    async def generate_flashcards(
        db: Session,
        topic_id: str,
        user_id: Optional[str] = None,
        num_cards: int = 10,
        difficulty: Optional[float] = None
    ) -> Dict:
        """
        Generate flashcards for a given topic, optionally personalized for a user.
        
        Args:
            db: Database session
            topic_id: ID of the topic
            user_id: Optional user ID for personalization
            num_cards: Number of flashcards to generate
            difficulty: Optional difficulty level (0.0-1.0)
            
        Returns:
            Dictionary containing generated flashcards
        """
        # Get topic info
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            logger.error(f"Topic with ID {topic_id} not found")
            return {"error": "Topic not found"}
            
        # Get concepts related to this topic
        concepts = db.query(Concept).filter(Concept.topic_id == topic_id).all()
        concept_names = [concept.name for concept in concepts]
        concept_map = {concept.id: concept.name for concept in concepts}
        
        # If user_id provided, personalize based on knowledge state
        adaptivity_params = {}
        if user_id:
            adaptivity_params = await KnowledgeTracingService.get_adaptivity_parameters(
                db=db,
                user_id=user_id,
                topic_id=topic_id
            )
            # Override difficulty with personalized difficulty if not explicitly set
            if difficulty is None and "recommended_difficulty" in adaptivity_params:
                difficulty = adaptivity_params["recommended_difficulty"]
        
        # Default difficulty if not set
        if difficulty is None:
            difficulty = 0.5  # Medium difficulty
        
        # Prepare system message
        system_message = f"""
You are an AI educational assistant specialized in creating effective flashcards.
Create {num_cards} flashcards for studying: {topic.name}.
Difficulty level: {difficulty:.1f}/1.0 (where 0 is beginner and 1 is advanced).

The flashcards should cover these key concepts: {', '.join(concept_names)}.
For each flashcard, provide:
1. Front: A concise prompt, question, or term
2. Back: The complete answer, definition, or explanation

Format each flashcard as a JSON object with "front" and "back" fields.
"""

        # Add personalization if we have user data
        if user_id and adaptivity_params:
            # Add focus concepts if any
            if adaptivity_params.get("focus_concepts"):
                focus_concepts = [f"{c['name']} (current mastery: {c['mastery']:.2f})" 
                                 for c in adaptivity_params["focus_concepts"].values()]
                system_message += f"\nPrioritize creating flashcards for these concepts: {', '.join(focus_concepts)}."
                
            # Add general mastery level
            system_message += f"\nThe user's average mastery level of this topic is {adaptivity_params.get('average_mastery', 0):.2f}/1.0."
        
        try:
            # Call AI client for flashcard generation
            ai_client = get_ai_client()
            response = await ai_client.chat_completions_create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Please create {num_cards} flashcards for '{topic.name}' that will help me study effectively."}
                ],
                max_tokens=1500,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            flashcards_data = json.loads(content)
            
            # Process the flashcards
            flashcards = []
            if "flashcards" in flashcards_data:
                raw_flashcards = flashcards_data["flashcards"]
            else:
                # If no "flashcards" key, assume the response is a list directly
                raw_flashcards = [flashcards_data[key] for key in flashcards_data if isinstance(flashcards_data[key], dict)]
                
            # Process each flashcard
            for i, card_data in enumerate(raw_flashcards):
                # Skip if we already have enough cards
                if i >= num_cards:
                    break
                
                # Try to match concept
                card_concept_id = None
                for concept_id, concept_name in concept_map.items():
                    if concept_name.lower() in card_data.get("front", "").lower() or \
                       concept_name.lower() in card_data.get("back", "").lower():
                        card_concept_id = concept_id
                        break
                
                flashcard = Flashcard(
                    front=card_data.get("front", ""),
                    back=card_data.get("back", ""),
                    concept_id=card_concept_id,
                    difficulty_level=difficulty
                )
                flashcards.append(flashcard)
            
            # Store generated content in database
            content_item = ContentItem(
                topic_id=topic_id,
                user_id=user_id,
                content_type="flashcards",
                content=json.dumps([card.dict() for card in flashcards]),
                metadata=json.dumps({
                    "difficulty": difficulty,
                    "count": len(flashcards),
                    "personalized": user_id is not None
                })
            )
            db.add(content_item)
            db.commit()
            
            return {
                "topic_id": topic_id,
                "topic_name": topic.name,
                "flashcards": [card.dict() for card in flashcards],
                "difficulty": difficulty,
                "personalized": user_id is not None,
                "content_item_id": content_item.id
            }
            
        except Exception as e:
            logger.error(f"Error generating flashcards: {str(e)}")
            return {"error": f"Flashcard generation failed: {str(e)}"}
    
    @staticmethod
    async def generate_practice_exercises(
        db: Session,
        topic_id: str,
        user_id: Optional[str] = None,
        num_exercises: int = 3,
        difficulty: Optional[float] = None,
        with_solutions: bool = True
    ) -> Dict:
        """
        Generate practice exercises for a topic.
        
        Args:
            db: Database session
            topic_id: ID of the topic
            user_id: Optional user ID for personalization
            num_exercises: Number of exercises to generate
            difficulty: Optional difficulty level (0.0-1.0)
            with_solutions: Whether to include detailed solutions
            
        Returns:
            Dictionary containing generated practice exercises
        """
        # Get topic info
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            logger.error(f"Topic with ID {topic_id} not found")
            return {"error": "Topic not found"}
            
        # Get concepts related to this topic
        concepts = db.query(Concept).filter(Concept.topic_id == topic_id).all()
        concept_map = {concept.id: concept.name for concept in concepts}
        
        # Get adaptivity parameters if user_id provided
        adaptivity_params = {}
        if user_id:
            adaptivity_params = await KnowledgeTracingService.get_adaptivity_parameters(
                db=db,
                user_id=user_id,
                topic_id=topic_id
            )
            # Override difficulty if not explicitly set
            if difficulty is None and "recommended_difficulty" in adaptivity_params:
                difficulty = adaptivity_params["recommended_difficulty"]
        
        # Default difficulty if not set
        if difficulty is None:
            difficulty = 0.5  # Medium difficulty
            
        # Prepare the prompt for exercise generation
        system_message = f"""
You are an AI educational exercise creator specialized in creating practice problems.
Create {num_exercises} practice exercises on the topic: {topic.name}.
Difficulty level: {difficulty:.1f}/1.0 (where 0 is beginner and 1 is advanced).
Include {"detailed solutions" if with_solutions else "hints only"}.

The exercises should cover these key concepts: {', '.join(concept_map.values())}.
Try to distribute the exercises across different concepts.

Return the exercises in the following JSON format:
{{
  "exercises": [
    {{
      "instruction": "Brief instruction for the exercise",
      "problem": "Detailed problem statement",
      "solution": "Step-by-step solution with explanation",
      "hint": "A helpful hint without giving away the answer",
      "concept_id": "concept_id_here",
      "difficulty_level": 0.5
    }},
    // more exercises...
  ]
}}
"""

        # Add personalization if we have user data
        if user_id and adaptivity_params:
            # Focus on concepts with lower mastery
            if adaptivity_params.get("focus_concepts"):
                focus_concepts = list(adaptivity_params["focus_concepts"].keys())
                focus_concept_names = [concept_map.get(c_id, "Unknown") for c_id in focus_concepts]
                
                system_message += f"""
The learner has lower mastery in these concepts: {', '.join(focus_concept_names)}.
Include more exercises related to these concepts.
"""
                
            # Knowledge state info
            system_message += f"\nThe learner's average mastery level of this topic is {adaptivity_params.get('average_mastery', 0):.2f}/1.0."
            
        # Create user message to request exercises
        user_message = f"Please create {num_exercises} practice exercises for '{topic.name}' with {'solutions' if with_solutions else 'hints'}."
        
        try:
            # Call AI client for exercise generation
            ai_client = get_ai_client()
            response = await ai_client.chat_completions_create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=2000,
                temperature=0.6,
                response_format={"type": "json_object"}
            )
            
            generated_content = response.choices[0].message.content
            
            try:
                # Parse the generated JSON
                exercises_data = json.loads(generated_content)
                
                # Validate the generated data
                if "exercises" not in exercises_data or not isinstance(exercises_data["exercises"], list):
                    logger.error("Invalid exercises format: missing exercises array")
                    return {"error": "Generated exercises have invalid format"}
                
                # Store exercises in database
                content_item = ContentItem(
                    topic_id=topic_id,
                    user_id=user_id,
                    content_type="practice_exercises",
                    content=json.dumps(exercises_data),
                    metadata=json.dumps({
                        "difficulty": difficulty,
                        "count": len(exercises_data["exercises"]),
                        "with_solutions": with_solutions,
                        "personalized": user_id is not None
                    })
                )
                db.add(content_item)
                db.commit()
                
                return {
                    "topic_id": topic_id,
                    "topic_name": topic.name,
                    "exercises": exercises_data["exercises"],
                    "difficulty": difficulty,
                    "with_solutions": with_solutions,
                    "personalized": user_id is not None,
                    "content_item_id": content_item.id
                }
                
            except json.JSONDecodeError:
                logger.error("Failed to parse generated exercises JSON")
                return {"error": "Failed to parse generated exercises"}
                
        except Exception as e:
            logger.error(f"Error generating practice exercises: {str(e)}")
            return {"error": f"Practice exercise generation failed: {str(e)}"}