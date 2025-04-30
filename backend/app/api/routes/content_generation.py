from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel
import json

from ...db.session import get_db
from ...db.models import Topic, User, ContentItem
from .user import get_current_user
from ...services.content_generation import ContentGenerationService, get_ai_client
from ...core.config import settings

router = APIRouter()

# Pydantic models for request/response
class GenerateStudyMaterialsRequest(BaseModel):
    topic_id: str
    difficulty: Optional[float] = None
    format: Optional[str] = "markdown"

class GenerateQuizRequest(BaseModel):
    topic_id: str
    num_questions: int = 5
    difficulty: Optional[float] = None

# New models matching frontend requests
class GenerateQuestionsRequest(BaseModel):
    context: str
    num_questions: int = 3
    topic_id: Optional[str] = None

class GenerateFlashcardsRequest(BaseModel):
    context: str
    num_cards: int = 5
    topic_id: Optional[str] = None

class GenerateExplanationRequest(BaseModel):
    concept: str
    difficulty: str = "intermediate"

class QuestionResponse(BaseModel):
    text: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None

class Flashcard(BaseModel):
    front: str
    back: str

class FlashcardSetResponse(BaseModel):
    topic_id: str
    topic_name: str
    flashcards: List[Dict[str, str]]
    difficulty: float
    personalized: bool
    content_item_id: str

class ExplanationRequest(BaseModel):
    concept_id: str
    difficulty: Optional[float] = 0.5

class PracticeExerciseRequest(BaseModel):
    topic_id: str
    num_exercises: int = 3
    difficulty: Optional[float] = None

@router.post("/generate/study-materials", response_model=Dict)
async def generate_study_materials(
    request: GenerateStudyMaterialsRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    try:
        user_id = current_user.id if current_user else None
        
        result = await ContentGenerationService.generate_study_materials(
            db=db,
            topic_id=request.topic_id,
            user_id=user_id,
            difficulty=request.difficulty,
            format=request.format
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Study material generation failed: {str(e)}"
        )

@router.post("/generate/quiz", response_model=Dict)
async def generate_quiz(
    request: GenerateQuizRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    try:
        user_id = current_user.id if current_user else None
        
        result = await ContentGenerationService.generate_quiz(
            db=db,
            topic_id=request.topic_id,
            user_id=user_id,
            num_questions=request.num_questions,
            difficulty=request.difficulty
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz generation failed: {str(e)}"
        )

@router.post("/generate/flashcards-by-topic", response_model=FlashcardSetResponse)
async def generate_flashcards(
    request: GenerateQuizRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    try:
        user_id = current_user.id if current_user else None
        
        result = await ContentGenerationService.generate_flashcards(
            db=db,
            topic_id=request.topic_id,
            user_id=user_id,
            num_cards=request.num_questions,  # Using num_questions as num_cards
            difficulty=request.difficulty
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Flashcard generation failed: {str(e)}"
        )

@router.post("/explain/concept", response_model=Dict)
async def explain_concept(
    request: ExplanationRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    try:
        user_id = current_user.id if current_user else None
        
        result = await ContentGenerationService.explain_concept(
            db=db,
            concept_id=request.concept_id,
            user_id=user_id,
            difficulty=request.difficulty
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Concept explanation failed: {str(e)}"
        )

@router.post("/generate/practice-exercises", response_model=Dict)
async def generate_practice_exercises(
    request: PracticeExerciseRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    try:
        user_id = current_user.id if current_user else None
        
        result = await ContentGenerationService.generate_practice_exercises(
            db=db,
            topic_id=request.topic_id,
            user_id=user_id,
            num_exercises=request.num_exercises,
            difficulty=request.difficulty
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Practice exercise generation failed: {str(e)}"
        )

@router.post("/generate/questions", response_model=List[Dict])
async def generate_questions(
    request: GenerateQuestionsRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    try:
        user_id = current_user.id if current_user else None
        
        # Map difficulty levels
        difficulty = 0.5  # default medium difficulty
        
        # Prepare system message for question generation
        system_message = f"""
You are an AI quiz creator specializing in educational assessment.
Create {request.num_questions} multiple-choice questions based on the following context:

{request.context}

For each question:
1. The question should test understanding of concepts from the context
2. Create 4 options with only one being correct
3. CRITICAL: Each option MUST contain full, meaningful text (not just a single word)
4. IMPORTANT: Do NOT use "Option 1", "Option 2" or similar as option text
5. Each option should be a clear, complete statement or answer
6. Do NOT include A, B, C, D or any numbering as part of the option text
7. Each option should be a simple string without internal newlines or formatting
8. Provide a brief explanation for the correct answer

EXAMPLE OF GOOD OPTIONS FORMAT:
"options": [
  "The result is 19",
  "The result is 21",
  "The result is 13",
  "The result is 15"
],

Return the quiz questions in the following JSON format:
[
  {{ 
    "text": "Question text here?",
    "options": ["Complete option text", "Complete option text", "Complete option text", "Complete option text"],
    "correct_answer": "The exact text of the correct option",
    "explanation": "Brief explanation of why this is correct"
  }},
  // more questions...
]

IMPORTANT:
- Return only the JSON array
- DO NOT include any markdown formatting or code blocks
- DO NOT add prefixes like "Option 1", "Option 2", "A:", "B:", "1)", "2)" to the options
- DO NOT include any numbering or lettering with the options
- DO NOT format options with internal newlines
"""
        
        # Call AI API for question generation
        try:
            ai_client = get_ai_client()
            response = await ai_client.chat_completions_create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Generate {request.num_questions} questions about this context."}
                ],
                max_tokens=2000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            # Add debug logging
            print(f"AI response content: {content[:200]}...")
            
            if not content or content.isspace():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Received empty response from AI service"
                )
            
            # Clean up the content - remove markdown formatting if present
            cleaned_content = content
            
            # Check for markdown code block format and extract just the JSON
            if cleaned_content.startswith("```"):
                # Find the first and last code block markers
                start_marker = cleaned_content.find("```")
                # Check if there's a language specifier after the first ```
                first_newline = cleaned_content.find("\n", start_marker)
                if first_newline > start_marker:
                    content_start = first_newline + 1
                else:
                    content_start = start_marker + 3
                
                end_marker = cleaned_content.rfind("```")
                if end_marker > start_marker:
                    cleaned_content = cleaned_content[content_start:end_marker].strip()
                else:
                    # If no closing marker, just remove the opening marker
                    cleaned_content = cleaned_content[content_start:].strip()
            
            try:
                questions_data = json.loads(cleaned_content)
            except json.JSONDecodeError as e:
                # If first attempt failed, try again with some additional cleanup
                try:
                    # Sometimes model outputs have extra text before or after the JSON
                    # Try to find JSON array brackets
                    start_bracket = cleaned_content.find('[')
                    end_bracket = cleaned_content.rfind(']')
                    if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
                        extracted_json = cleaned_content[start_bracket:end_bracket+1]
                        questions_data = json.loads(extracted_json)
                    else:
                        raise e
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to parse AI response as JSON: {str(e)}. Content received: {content[:100]}..."
                    )
            
            # Extract questions from response
            questions = []
            if isinstance(questions_data, list):
                questions = questions_data
            elif "questions" in questions_data:
                questions = questions_data["questions"]
            else:
                # Try to find question array in the response
                for key in questions_data:
                    if isinstance(questions_data[key], list) and len(questions_data[key]) > 0:
                        questions = questions_data[key]
                        break
            
            # Validate that we have questions in the expected format
            if not questions:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not find questions in AI response"
                )
                
            # Validate question format and clean options
            for question in questions:
                if not isinstance(question, dict):
                    continue
                if "text" not in question or "options" not in question or "correct_answer" not in question:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Questions in unexpected format"
                    )
                
                # Clean up any option prefixes that might still be present
                if isinstance(question["options"], list):
                    # Regular expression pattern to match common option prefixes
                    import re
                    prefix_pattern = re.compile(r'^(Option\s*\d+[:.)\s-]*|[A-D][:.)\s-]*|[0-9]+[:.)\s-]*)', re.IGNORECASE)
                    
                    # Clean each option and ensure none are empty
                    for i in range(len(question["options"])):
                        if not isinstance(question["options"][i], str) or not question["options"][i].strip():
                            # If empty or not a string, generate a default placeholder
                            question["options"][i] = f"Answer option {i+1}"
                        else:
                            # Remove any prefixes like "Option 1:", "A.", "1)", etc.
                            question["options"][i] = prefix_pattern.sub('', question["options"][i]).strip()
                            
                            # Also remove any newlines that might be in the option
                            question["options"][i] = question["options"][i].replace('\n', ' ').strip()
                            
                            # If after cleaning it's empty, use a default
                            if not question["options"][i]:
                                question["options"][i] = f"Answer option {i+1}"
                    
                    # Also clean the correct answer
                    if isinstance(question["correct_answer"], str):
                        question["correct_answer"] = prefix_pattern.sub('', question["correct_answer"]).strip()
                        question["correct_answer"] = question["correct_answer"].replace('\n', ' ').strip()
                        # If the correct answer is empty after cleaning, use the first option as default
                        if not question["correct_answer"] and question["options"]:
                            question["correct_answer"] = question["options"][0]
                
            # Store in database if a topic is provided
            if request.topic_id:
                topic = db.query(Topic).filter(Topic.id == request.topic_id).first()
                if topic:
                    content_item = ContentItem(
                        topic_id=topic.id,
                        content_type="quiz_questions",
                        content=json.dumps(questions),
                        title=f"Generated quiz questions",
                        difficulty_level=difficulty
                    )
                    db.add(content_item)
                    db.commit()
            
            return questions
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate questions: {str(e)}"
            )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Question generation failed: {str(e)}"
        )

@router.post("/generate/flashcards", response_model=List[Dict])
async def generate_flashcards_from_context(
    request: GenerateFlashcardsRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    try:
        user_id = current_user.id if current_user else None
        
        # Prepare system message
        system_message = f"""
You are an AI educational assistant specialized in creating effective flashcards.
Create {request.num_cards} flashcards based on the following context:

{request.context}

For each flashcard, provide:
1. Front: A concise prompt, question, or term
2. Back: The complete answer, definition, or explanation

Return the flashcards in the following JSON format:
[
  {{
    "front": "Front of flashcard 1",
    "back": "Back of flashcard 1"
  }},
  // more flashcards...
]

IMPORTANT: Return only the JSON array without any markdown formatting or code blocks.
"""
        
        try:
            # Call AI API for flashcard generation
            ai_client = get_ai_client()
            response = await ai_client.chat_completions_create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Create {request.num_cards} flashcards from this context."}
                ],
                max_tokens=1500,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            # Add debug logging
            print(f"AI flashcard response content: {content[:200]}...")
            
            if not content or content.isspace():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Received empty response from AI service"
                )
            
            # Clean up the content - remove markdown formatting if present
            cleaned_content = content
            
            # Check for markdown code block format and extract just the JSON
            if cleaned_content.startswith("```"):
                # Find the first and last code block markers
                start_marker = cleaned_content.find("```")
                # Check if there's a language specifier after the first ```
                first_newline = cleaned_content.find("\n", start_marker)
                if first_newline > start_marker:
                    content_start = first_newline + 1
                else:
                    content_start = start_marker + 3
                
                end_marker = cleaned_content.rfind("```")
                if end_marker > start_marker:
                    cleaned_content = cleaned_content[content_start:end_marker].strip()
                else:
                    # If no closing marker, just remove the opening marker
                    cleaned_content = cleaned_content[content_start:].strip()
            
            try:
                data = json.loads(cleaned_content)
            except json.JSONDecodeError as e:
                # If first attempt failed, try again with some additional cleanup
                try:
                    # Sometimes model outputs have extra text before or after the JSON
                    # Try to find JSON array brackets
                    start_bracket = cleaned_content.find('[')
                    end_bracket = cleaned_content.rfind(']')
                    if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
                        extracted_json = cleaned_content[start_bracket:end_bracket+1]
                        data = json.loads(extracted_json)
                    else:
                        raise e
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to parse AI response as JSON: {str(e)}. Content received: {content[:100]}..."
                    )
            
            # Extract flashcards from response
            flashcards = []
            if isinstance(data, list):
                flashcards = data
            elif "flashcards" in data:
                flashcards = data["flashcards"]
            else:
                # Try to find flashcards array in the response
                for key in data:
                    if isinstance(data[key], list) and len(data[key]) > 0:
                        flashcards = data[key]
                        break
            
            # Validate that we have flashcards in the expected format
            if not flashcards:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not find flashcards in AI response"
                )
                
            # Validate flashcard format
            for card in flashcards:
                if not isinstance(card, dict):
                    continue
                if "front" not in card or "back" not in card:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Flashcards in unexpected format"
                    )
            
            # Store in database if a topic is provided
            if request.topic_id:
                topic = db.query(Topic).filter(Topic.id == request.topic_id).first()
                if topic:
                    content_item = ContentItem(
                        topic_id=topic.id,
                        content_type="flashcards",
                        content=json.dumps(flashcards),
                        title=f"Generated flashcards",
                        difficulty_level=0.5
                    )
                    db.add(content_item)
                    db.commit()
            
            return flashcards
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate flashcards: {str(e)}"
            )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Flashcard generation failed: {str(e)}"
        )

@router.post("/generate/explanation")
async def generate_explanation(
    request: GenerateExplanationRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    try:
        user_id = current_user.id if current_user else None
        
        # Map difficulty levels
        difficulty_map = {
            "beginner": 0.3,
            "intermediate": 0.5,
            "advanced": 0.8
        }
        difficulty = difficulty_map.get(request.difficulty, 0.5)
        
        # Prepare system message
        system_message = f"""
You are an educational AI specialized in explaining complex concepts clearly.
Generate a comprehensive explanation of the concept: {request.concept}

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

The explanation should be at {request.difficulty} level.

For {request.difficulty} level:
"""

        # Add difficulty-specific instructions
        if request.difficulty == "beginner":
            system_message += """
- Use simple language and avoid jargon
- Explain all terminology clearly
- Focus on foundational concepts
- Use everyday examples and analogies
"""
        elif request.difficulty == "advanced":
            system_message += """
- You can use technical terminology (but still define specialized terms)
- Include more in-depth analysis
- Cover edge cases and exceptions
- Make connections to related advanced concepts
"""
        else:  # intermediate
            system_message += """
- Balance technical accuracy with accessibility
- Explain most terminology, but can assume some basic knowledge
- Include both simple and more complex examples
"""

        try:
            # Call AI API for explanation generation
            ai_client = get_ai_client()
            response = await ai_client.chat_completions_create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Please explain the concept of '{request.concept}' in detail."}
                ],
                max_tokens=1000,
                temperature=0.6
            )
            
            explanation = response.choices[0].message.content
            
            # Store in database as general content
            content_item = ContentItem(
                content_type="concept_explanation",
                content=explanation,
                title=f"Explanation of {request.concept}",
                difficulty_level=difficulty,
                format="markdown"
            )
            db.add(content_item)
            db.commit()
            
            return explanation
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate explanation: {str(e)}"
            )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explanation generation failed: {str(e)}"
        )