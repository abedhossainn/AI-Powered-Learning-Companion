import numpy as np
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from ..db.models import KnowledgeState, QuestionResponse, Question, User, Concept
from ..core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BayesianKnowledgeTracing:
    """
    Implements Bayesian Knowledge Tracing (BKT) to model student knowledge.
    BKT is a hidden Markov model with two knowledge states: known and unknown.
    """
    
    def __init__(
        self,
        p_know: float = None,
        p_learn: float = None,
        p_guess: float = None,
        p_slip: float = None
    ):
        """
        Initialize the BKT model with parameters.
        
        Args:
            p_know: Initial probability of knowing the concept
            p_learn: Probability of learning a concept if previously unknown
            p_guess: Probability of guessing correctly if unknown
            p_slip: Probability of making a mistake if known
        """
        self.p_know = p_know if p_know is not None else settings.BKT_DEFAULT_INIT_P_KNOW
        self.p_learn = p_learn if p_learn is not None else settings.BKT_DEFAULT_LEARN
        self.p_guess = p_guess if p_guess is not None else settings.BKT_DEFAULT_GUESS
        self.p_slip = p_slip if p_slip is not None else settings.BKT_DEFAULT_SLIP
    
    def update(self, is_correct: bool) -> float:
        """
        Update knowledge estimate based on observed performance.
        
        Args:
            is_correct: Whether the student answered correctly
            
        Returns:
            Updated probability of knowledge
        """
        # Step 1: Adjust based on correctness (evidence)
        if is_correct:
            # P(known | correct)
            p_known_given_correct = (self.p_know * (1 - self.p_slip)) / \
                                    ((self.p_know * (1 - self.p_slip)) + ((1 - self.p_know) * self.p_guess))
        else:
            # P(known | incorrect)
            p_known_given_incorrect = (self.p_know * self.p_slip) / \
                                     ((self.p_know * self.p_slip) + ((1 - self.p_know) * (1 - self.p_guess)))
            p_known_given_correct = p_known_given_incorrect
        
        # Step 2: Account for learning
        self.p_know = p_known_given_correct + (1 - p_known_given_correct) * self.p_learn
        
        return self.p_know


class KnowledgeTracingService:
    """
    Service for tracking and updating user knowledge states using Bayesian Knowledge Tracing (BKT).
    BKT is a cognitive model that estimates student knowledge based on their performance.
    """
    
    @staticmethod
    async def get_user_knowledge_state(db: Session, user_id: str, concept_id: str) -> Optional[KnowledgeState]:
        """
        Get the knowledge state for a specific user and concept.
        If no state exists, create one with default values.
        """
        # Try to get existing knowledge state
        knowledge_state = db.query(KnowledgeState).filter(
            and_(
                KnowledgeState.user_id == user_id,
                KnowledgeState.concept_id == concept_id
            )
        ).first()
        
        # If no state exists, create one with default values
        if not knowledge_state:
            knowledge_state = KnowledgeState(
                user_id=user_id,
                concept_id=concept_id,
                p_know=settings.BKT_DEFAULT_INIT_P_KNOW,
                p_learn=settings.BKT_DEFAULT_LEARN,
                p_guess=settings.BKT_DEFAULT_GUESS,
                p_slip=settings.BKT_DEFAULT_SLIP
            )
            db.add(knowledge_state)
            db.commit()
            db.refresh(knowledge_state)
        
        return knowledge_state
    
    @staticmethod
    async def get_user_knowledge_states(db: Session, user_id: str) -> Dict[str, float]:
        """
        Get all knowledge states for a user, returned as a dictionary of concept_id -> p_know.
        """
        knowledge_states = db.query(KnowledgeState).filter(
            KnowledgeState.user_id == user_id
        ).all()
        
        return {state.concept_id: state.p_know for state in knowledge_states}
    
    @staticmethod
    async def update_knowledge_state(db: Session, question_response: QuestionResponse) -> Optional[KnowledgeState]:
        """
        Update a user's knowledge state based on their response to a question.
        Uses Bayesian Knowledge Tracing to update probabilities.
        
        Args:
            db: Database session
            question_response: The user's response to a question
            
        Returns:
            Updated KnowledgeState or None if the question has no associated concept
        """
        # Get question to find its associated concept
        question = db.query(Question).filter(Question.id == question_response.question_id).first()
        if not question or not question.concept_id:
            logger.info(f"No concept associated with question {question_response.question_id}")
            return None
        
        # Get user's knowledge state for this concept
        knowledge_state = await KnowledgeTracingService.get_user_knowledge_state(
            db=db, 
            user_id=question_response.user_id, 
            concept_id=question.concept_id
        )
        
        # Update knowledge state using BKT algorithm
        prior_p_know = knowledge_state.p_know
        
        # 1. Calculate conditional probability that student answers correctly
        p_correct = prior_p_know * (1 - knowledge_state.p_slip) + (1 - prior_p_know) * knowledge_state.p_guess
        
        # 2. Calculate posterior probability of knowledge given the response
        if question_response.is_correct:
            # If correct answer, update P(know) using Bayes' rule
            posterior_p_know = (prior_p_know * (1 - knowledge_state.p_slip)) / p_correct
        else:
            # If incorrect answer, update P(know) using Bayes' rule
            posterior_p_know = (prior_p_know * knowledge_state.p_slip) / (1 - p_correct)
        
        # 3. Update probability of knowledge to account for learning
        # P(L_t) = P(L_{t-1}) + (1 - P(L_{t-1})) * P(T)
        updated_p_know = posterior_p_know + (1 - posterior_p_know) * knowledge_state.p_learn
        
        # Update the knowledge state
        knowledge_state.p_know = updated_p_know
        
        # Save to database
        db.commit()
        db.refresh(knowledge_state)
        
        logger.info(f"Updated knowledge state for user {question_response.user_id} on concept {question.concept_id}")
        logger.info(f"  Prior P(Know): {prior_p_know:.4f}, Posterior: {updated_p_know:.4f}")
        
        return knowledge_state
    
    @staticmethod
    async def bulk_update_from_quiz(db: Session, quiz_attempt_id: str) -> Dict[str, float]:
        """
        Update knowledge states for all questions in a quiz attempt.
        
        Args:
            db: Database session
            quiz_attempt_id: ID of the completed quiz attempt
            
        Returns:
            Dictionary mapping concept_id to updated p_know values
        """
        # Get all responses for this quiz attempt
        responses = db.query(QuestionResponse).filter(
            QuestionResponse.quiz_attempt_id == quiz_attempt_id
        ).all()
        
        # Track updated concepts
        updated_concepts = {}
        
        # Process each response
        for response in responses:
            knowledge_state = await KnowledgeTracingService.update_knowledge_state(db, response)
            if knowledge_state:
                updated_concepts[knowledge_state.concept_id] = knowledge_state.p_know
        
        return updated_concepts
    
    @staticmethod
    async def recommend_topics_to_review(db: Session, user_id: str, threshold: float = 0.6) -> List[Dict]:
        """
        Recommend topics for a user to review based on their knowledge states.
        
        Args:
            db: Database session
            user_id: ID of the user
            threshold: Knowledge threshold below which concepts are recommended for review
            
        Returns:
            List of concepts/topics recommended for review
        """
        # Get user's knowledge states
        knowledge_states = db.query(KnowledgeState).filter(
            and_(
                KnowledgeState.user_id == user_id,
                KnowledgeState.p_know < threshold
            )
        ).all()
        
        recommendations = []
        
        for state in knowledge_states:
            # Get concept info
            concept = db.query(Concept).filter(Concept.id == state.concept_id).first()
            if concept:
                recommendations.append({
                    "concept_id": concept.id,
                    "concept_name": concept.name,
                    "topic_id": concept.topic_id,
                    "mastery_level": state.p_know,
                    "recommendation_reason": f"Current mastery level ({state.p_know:.2f}) is below target threshold ({threshold})"
                })
        
        # Sort by mastery level (ascending)
        recommendations.sort(key=lambda x: x["mastery_level"])
        
        return recommendations
    
    @staticmethod
    async def get_adaptivity_parameters(db: Session, user_id: str, topic_id: str) -> Dict:
        """
        Get parameters for adaptive content generation based on user's knowledge state.
        
        Args:
            db: Database session
            user_id: ID of the user
            topic_id: ID of the topic
            
        Returns:
            Dictionary with adaptivity parameters
        """
        # Get concepts for the topic
        concepts = db.query(Concept).filter(Concept.topic_id == topic_id).all()
        concept_ids = [c.id for c in concepts]
        
        # Get knowledge states for these concepts
        knowledge_states = {}
        for concept_id in concept_ids:
            state = await KnowledgeTracingService.get_user_knowledge_state(db, user_id, concept_id)
            knowledge_states[concept_id] = state.p_know
        
        # Calculate overall mastery level for the topic
        if knowledge_states:
            avg_mastery = sum(knowledge_states.values()) / len(knowledge_states)
        else:
            avg_mastery = 0.0
        
        # Determine appropriate difficulty level based on mastery
        # Slightly higher than current mastery to promote growth
        target_difficulty = min(0.9, avg_mastery + 0.2)
        
        # Find concepts that need more focus (lower mastery)
        focus_concepts = {}
        for concept_id, mastery in knowledge_states.items():
            if mastery < avg_mastery:
                concept = db.query(Concept).filter(Concept.id == concept_id).first()
                if concept:
                    focus_concepts[concept_id] = {
                        "name": concept.name,
                        "mastery": mastery
                    }
        
        return {
            "user_id": user_id,
            "topic_id": topic_id,
            "average_mastery": avg_mastery,
            "recommended_difficulty": target_difficulty,
            "focus_concepts": focus_concepts,
            "knowledge_states": knowledge_states
        }