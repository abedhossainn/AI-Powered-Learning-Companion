from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import json

from ...db.session import get_db
from ...db.models import Quiz, Question, QuizQuestion, QuizAttempt, Topic, TopicProgress
from .user import get_current_user, User
from ...services.knowledge_tracing import BayesianKnowledgeTracing

router = APIRouter()

# Pydantic models for request/response
class QuestionBase(BaseModel):
    text: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None
    
class QuestionResponse(QuestionBase):
    id: str
    
    class Config:
        from_attributes = True

class QuizBase(BaseModel):
    title: str
    description: Optional[str] = None
    topic_id: str
    is_adaptive: bool = True
    difficulty_level: float = 0.5

class QuizCreate(QuizBase):
    questions: List[str] = []  # List of question IDs

class QuizResponse(QuizBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class QuizDetailResponse(QuizResponse):
    questions: List[QuestionResponse]
    
    class Config:
        from_attributes = True

class QuizAttemptCreate(BaseModel):
    quiz_id: str
    responses: Dict[str, str]  # Question ID to selected answer

class QuizAttemptResponse(BaseModel):
    id: str
    quiz_id: str
    score: float
    started_at: datetime
    completed_at: Optional[datetime] = None
    responses: Dict[str, str]
    questions: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        orm_mode = True
        from_attributes = True  # Adding this for Pydantic v2 compatibility

class QuizAttemptFeedbackResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    score: float
    questions: List[Dict[str, Any]]  # Detailed feedback for each question
    mastery_update: float  # New mastery level after this attempt
    
@router.post("/quizzes/", response_model=QuizResponse)
def create_quiz(
    quiz: QuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify that topic exists
    topic = db.query(Topic).filter(Topic.id == quiz.topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )
    
    # Create quiz
    db_quiz = Quiz(
        title=quiz.title,
        description=quiz.description,
        topic_id=quiz.topic_id,
        difficulty_level=quiz.difficulty_level,
        is_adaptive=quiz.is_adaptive
    )
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    
    # Add questions to quiz
    for idx, question_id in enumerate(quiz.questions):
        question = db.query(Question).filter(Question.id == question_id).first()
        if question:
            quiz_question = QuizQuestion(
                quiz_id=db_quiz.id,
                question_id=question_id,
                order=idx
            )
            db.add(quiz_question)
    
    db.commit()
    return db_quiz

@router.get("/quizzes/", response_model=List[QuizResponse])
def get_quizzes(
    topic_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Quiz)
    
    if topic_id:
        query = query.filter(Quiz.topic_id == topic_id)
        
    quizzes = query.offset(skip).limit(limit).all()
    return quizzes

@router.get("/quizzes/{quiz_id}", response_model=QuizDetailResponse)
def get_quiz_detail(
    quiz_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get quiz with questions
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
        
    # Get questions associated with this quiz
    quiz_questions = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz_id
    ).order_by(QuizQuestion.order).all()
    
    question_ids = [qq.question_id for qq in quiz_questions]
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
    
    # Reorder questions based on the quiz_questions order
    question_dict = {q.id: q for q in questions}
    ordered_questions = [question_dict[qid] for qid in question_ids if qid in question_dict]
    
    # Create response object
    response = QuizDetailResponse(
        id=quiz.id,
        title=quiz.title,
        description=quiz.description,
        topic_id=quiz.topic_id,
        is_adaptive=quiz.is_adaptive,
        difficulty_level=quiz.difficulty_level,
        created_at=quiz.created_at,
        questions=[
            QuestionResponse(
                id=q.id,
                text=q.text,
                options=[opt.lstrip('1234567890.)- ') for opt in q.options],  # Clean prefixes
                correct_answer=q.correct_answer,
                explanation=q.explanation
            ) for q in ordered_questions
        ]
    )
    
    return response

@router.post("/quizzes/attempt", response_model=QuizAttemptFeedbackResponse)
def submit_quiz_attempt(
    attempt: QuizAttemptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get quiz
    quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
        
    # Get questions for this quiz
    quiz_questions = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz.id
    ).all()
    question_ids = [qq.question_id for qq in quiz_questions]
    
    # Get questions with answers
    questions = db.query(Question).filter(
        Question.id.in_(question_ids)
    ).all()
    
    question_dict = {q.id: q for q in questions}
    
    # Calculate score
    total_questions = len(question_ids)
    correct_answers = 0
    responses_list = []  # List of correct/incorrect responses for BKT
    
    question_feedback = []
    
    for question_id, answer in attempt.responses.items():
        if question_id in question_dict:
            question = question_dict[question_id]
            is_correct = answer == question.correct_answer
            
            if is_correct:
                correct_answers += 1
                
            responses_list.append(is_correct)
            
            question_feedback.append({
                "question_id": question_id,
                "text": question.text,
                "user_answer": answer,
                "correct_answer": question.correct_answer,
                "is_correct": is_correct,
                "explanation": question.explanation
            })
    
    # Calculate percentage score
    score = (correct_answers / total_questions) if total_questions > 0 else 0
    
    # Update user mastery using Bayesian Knowledge Tracing
    user_progress = db.query(TopicProgress).filter(
        TopicProgress.user_id == current_user.id,
        TopicProgress.topic_id == quiz.topic_id
    ).first()
    
    bkt = BayesianKnowledgeTracing()
    
    if not user_progress:
        # Initialize new progress record if it doesn't exist
        user_progress = TopicProgress(
            user_id=current_user.id,
            topic_id=quiz.topic_id,
            mastery_level=bkt.p_know  # Changed from p_init to p_know
        )
        db.add(user_progress)
        current_mastery = bkt.p_know  # Changed from p_init to p_know
    else:
        current_mastery = user_progress.mastery_level
    
    # Update mastery using BKT
    updated_mastery = current_mastery
    for correct in responses_list:
        # Set the current knowledge level (p_know) before calling update
        bkt.p_know = updated_mastery
        # Call update with just the correct/incorrect flag
        updated_mastery = bkt.update(correct)
    
    # Update the user's progress
    user_progress.mastery_level = updated_mastery
    user_progress.last_activity_at = datetime.utcnow()  # Changed from last_updated to last_activity_at
    
    # Save the attempt
    db_attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_id=quiz.id,
        score=score,
        started_at=datetime.utcnow(),  # Changed from start_time to started_at
        completed_at=datetime.utcnow(),  # Changed from end_time to completed_at
        responses=attempt.responses
    )
    db.add(db_attempt)
    
    # Commit all changes
    db.commit()
    db.refresh(db_attempt)
    
    # Return the detailed feedback
    return QuizAttemptFeedbackResponse(
        attempt_id=db_attempt.id,
        quiz_id=quiz.id,
        score=score,
        questions=question_feedback,
        mastery_update=updated_mastery
    )

@router.get("/quizzes/attempts/user", response_model=List[QuizAttemptResponse])
def get_user_quiz_attempts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attempts = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == current_user.id
    ).all()
    
    # Parse the JSON responses for each attempt
    for attempt in attempts:
        if attempt.responses and isinstance(attempt.responses, str):
            try:
                attempt.responses = json.loads(attempt.responses)
            except json.JSONDecodeError:
                attempt.responses = {}  # Default to empty dict if JSON is invalid
        elif attempt.responses is None:
            attempt.responses = {}
    
    return attempts

@router.get("/quizzes/attempts/{attempt_id}", response_model=QuizAttemptResponse)
def get_quiz_attempt(
    attempt_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attempt = db.query(QuizAttempt).filter(
        QuizAttempt.id == attempt_id,
        QuizAttempt.user_id == current_user.id
    ).first()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz attempt not found"
        )
    
    # Parse JSON responses
    if attempt.responses and isinstance(attempt.responses, str):
        try:
            attempt.responses = json.loads(attempt.responses)
        except json.JSONDecodeError:
            attempt.responses = {}  # Default to empty dict if JSON is invalid
    elif attempt.responses is None:
        attempt.responses = {}
    
    # Check if this is a practice quiz and include the questions from quiz_metadata
    if attempt.quiz_id.startswith('practice-') and attempt.quiz_metadata:
        try:
            practice_questions = json.loads(attempt.quiz_metadata)
            # Add the questions to the attempt object
            attempt.questions = practice_questions
        except json.JSONDecodeError:
            attempt.questions = []
    
    return attempt

class PracticeQuizAttemptCreate(BaseModel):
    quiz_type: str = "practice"
    score: float
    questions: List[Dict[str, Any]]

@router.post("/quizzes/practice/attempt", response_model=Dict[str, str])
def submit_practice_quiz_attempt(
    attempt: PracticeQuizAttemptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a practice quiz attempt generated directly on the dashboard.
    This doesn't require a pre-existing quiz in the database.
    """
    try:
        # Convert responses and questions to JSON strings for SQLite storage
        questions_json = json.dumps(attempt.questions)
        
        # Save the attempt
        db_attempt = QuizAttempt(
            user_id=current_user.id,
            quiz_id=f"practice-{datetime.utcnow().isoformat()}",  # Generate a pseudo quiz ID
            score=attempt.score,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            responses=json.dumps({}),  # Store empty JSON object as string
            quiz_metadata=questions_json  # Store questions as JSON string in quiz_metadata
        )
        db.add(db_attempt)
        
        # Commit changes
        db.commit()
        db.refresh(db_attempt)
        
        # Return the attempt ID
        return {"attempt_id": db_attempt.id}
    except Exception as e:
        # Log the error for debugging
        print(f"Error in submit_practice_quiz_attempt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save quiz attempt: {str(e)}"
        )

# New endpoint to handle retrieving practice quizzes
class PracticeQuizDetailResponse(BaseModel):
    id: str
    title: str = "Practice Quiz"
    description: Optional[str] = "A practice quiz generated on the dashboard"
    topic_id: Optional[str] = None
    is_adaptive: bool = False
    difficulty_level: float = 0.5
    created_at: datetime
    questions: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True

@router.get("/quizzes/practice/{practice_id}", response_model=PracticeQuizDetailResponse)
def get_practice_quiz_detail(
    practice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a practice quiz by its ID (which is stored in the quiz_id field of QuizAttempt)
    """
    # The full practice ID includes the "practice-" prefix
    full_practice_id = f"practice-{practice_id}" if not practice_id.startswith("practice-") else practice_id
    
    # Find the quiz attempt that matches this practice ID
    attempt = db.query(QuizAttempt).filter(
        QuizAttempt.quiz_id == full_practice_id,
        QuizAttempt.user_id == current_user.id
    ).first()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practice quiz not found"
        )
    
    # Parse the quiz_metadata which contains the questions
    questions = []
    if attempt.quiz_metadata:
        try:
            questions = json.loads(attempt.quiz_metadata)
        except json.JSONDecodeError:
            questions = []
    
    # Create and return the response
    return PracticeQuizDetailResponse(
        id=attempt.quiz_id,
        created_at=attempt.started_at,
        questions=questions
    )