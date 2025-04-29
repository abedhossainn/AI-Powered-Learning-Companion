from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ...db.session import get_db
from ...db.models import Topic, TopicProgress
from .user import get_current_user, User

router = APIRouter()

# Pydantic models for request/response
class TopicBase(BaseModel):
    name: str
    description: Optional[str] = None

class TopicCreate(TopicBase):
    pass

class TopicResponse(TopicBase):
    id: str
    
    class Config:
        from_attributes = True

class UserProgressResponse(BaseModel):
    topic_id: str
    topic_name: str
    mastery_level: float
    
    class Config:
        from_attributes = True

@router.post("/topics/", response_model=TopicResponse)
def create_topic(
    topic: TopicCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only allow superusers to create topics
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create topics"
        )
    
    # Check if topic with same name already exists
    existing = db.query(Topic).filter(Topic.name == topic.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Topic with name '{topic.name}' already exists"
        )
    
    db_topic = Topic(**topic.dict())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic

@router.get("/topics/", response_model=List[TopicResponse])
def get_topics(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    topics = db.query(Topic).offset(skip).limit(limit).all()
    return topics

@router.get("/topics/{topic_id}", response_model=TopicResponse)
def get_topic(
    topic_id: str,
    db: Session = Depends(get_db)
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if topic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )
    return topic

@router.get("/topics/progress/", response_model=List[UserProgressResponse])
def get_user_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Join TopicProgress with Topic to get names
    progress = db.query(
        TopicProgress.topic_id,
        Topic.name.label("topic_name"),
        TopicProgress.mastery_level
    ).join(
        Topic, TopicProgress.topic_id == Topic.id
    ).filter(
        TopicProgress.user_id == current_user.id
    ).all()
    
    # Convert SQLAlchemy result to Pydantic model
    result = []
    for p in progress:
        result.append(UserProgressResponse(
            topic_id=p.topic_id,
            topic_name=p.topic_name,
            mastery_level=p.mastery_level
        ))
    
    return result