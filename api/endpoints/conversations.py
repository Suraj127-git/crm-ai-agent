from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import uuid

from db.utils.database import get_db
from models.user import User
from models.conversation import Conversation
from models.conversation_message import ConversationMessage, MessageRole
from api.endpoints.auth import get_current_user
from chatbot.chains.conversation import ConversationChain
from vector_db.qdrant_client import get_qdrant_client
from vector_db.utils.embeddings import get_conversation_embedding

router = APIRouter()

# Pydantic models
class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    
    class Config:
        from_attributes = True

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    messages: List[MessageResponse] = []
    
    class Config:
        from_attributes = True

# Store active conversation chains
active_conversations = {}

# Helper function to get or create conversation chain
def get_conversation_chain(conversation_id):
    if conversation_id not in active_conversations:
        active_conversations[conversation_id] = ConversationChain(conversation_id=conversation_id)
    return active_conversations[conversation_id]

# Background task to save embeddings
def save_conversation_embeddings(conversation_id: int, db: Session):
    # Get conversation messages
    messages = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at)
        .all()
    )
    
    # Convert to format for embedding
    formatted_messages = [
        {"role": msg.role, "content": msg.content} for msg in messages
    ]
    
    # Generate embedding
    embedding = get_conversation_embedding(formatted_messages)
    
    # Generate a stable ID for the vector
    vector_id = str(conversation_id)
    
    # Get conversation metadata
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    # Create metadata
    metadata = {
        "conversation_id": conversation_id,
        "user_id": conversation.user_id,
        "title": conversation.title or f"Conversation {conversation_id}",
        "message_count": len(messages)
    }
    
    # Save to vector database
    client = get_qdrant_client()
    client.upsert(
        collection_name="conversation_embeddings",
        points=[{
            "id": vector_id,
            "vector": embedding,
            "payload": metadata
        }]
    )
    
    # Update conversation with vector ID
    conversation.vector_id = vector_id
    db.commit()

# Endpoints
@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    title = conversation.title or f"Conversation {uuid.uuid4().hex[:8]}"
    db_conversation = Conversation(
        user_id=current_user.id,
        title=title
    )
    
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    
    # Create conversation chain
    get_conversation_chain(db_conversation.id)
    
    return db_conversation

@router.get("/", response_model=List[ConversationResponse])
def get_conversations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return conversations

@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation

@router.post("/{conversation_id}/messages", response_model=MessageResponse)
def add_message(
    conversation_id: int,
    message: MessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if conversation exists and belongs to user
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Create user message
    db_message = ConversationMessage(
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=message.content
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Get AI response
    chain = get_conversation_chain(conversation_id)
    chain.add_message("user", message.content)
    response = chain.get_response(message.content)
    
    # Save AI response
    ai_message = ConversationMessage(
        conversation_id=conversation_id,
        role=MessageRole.ASSISTANT,
        content=response
    )
    
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)
    
    # Add to conversation memory
    chain.add_message("assistant", response)
    
    # Schedule background task to save embeddings
    background_tasks.add_task(save_conversation_embeddings, conversation_id, db)
    
    return db_message

@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete conversation chain if exists
    if conversation_id in active_conversations:
        del active_conversations[conversation_id]
    
    # Delete from database
    db.delete(conversation)
    db.commit()
    
    # Delete from vector database if it exists
    if conversation.vector_id:
        try:
            client = get_qdrant_client()
            client.delete(
                collection_name="conversation_embeddings",
                points_selector=[conversation.vector_id]
            )
        except Exception as e:
            # Log the error but continue with deletion
            print(f"Error deleting from vector DB: {e}")
    
    return None