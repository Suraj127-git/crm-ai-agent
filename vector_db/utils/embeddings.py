from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)
EMBEDDING_MODEL = "text-embedding-3-small"

def get_embeddings(text):
    """Get OpenAI embeddings for a text"""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    
    return response.data[0].embedding

def get_conversation_embedding(messages):
    """Get embedding for a full conversation"""
    # Concatenate all messages
    text = " ".join([f"{msg['role']}: {msg['content']}" for msg in messages])
    return get_embeddings(text)