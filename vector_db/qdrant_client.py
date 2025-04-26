from qdrant_client import QdrantClient
from qdrant_client.http import models
import os
from dotenv import load_dotenv

load_dotenv()

# Qdrant configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "conversation_embeddings")
VECTOR_SIZE = 1536  # OpenAI embedding size

def get_qdrant_client():
    """Get a Qdrant client instance"""
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

def initialize_collection():
    """Initialize the Qdrant collection if it doesn't exist"""
    client = get_qdrant_client()
    
    # Check if collection exists
    collections = client.get_collections()
    if not any(collection.name == QDRANT_COLLECTION for collection in collections.collections):
        # Create new collection
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE
            )
        )
        print(f"Created new Qdrant collection: {QDRANT_COLLECTION}")
    else:
        print(f"Qdrant collection {QDRANT_COLLECTION} already exists")

    return client

def upsert_conversation(client, vector_id, embedding, metadata=None):
    """Store a conversation embedding in Qdrant"""
    client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=[
            models.PointStruct(
                id=vector_id,
                vector=embedding,
                payload=metadata or {}
            )
        ]
    )

def search_similar_conversations(client, embedding, limit=5):
    """Search for similar conversations based on embedding"""
    results = client.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=embedding,
        limit=limit
    )
    
    return results