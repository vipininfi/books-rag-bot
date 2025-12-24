from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/bookrag"
    
    # Gemini AI
    GEMINI_API_KEY: str
    
    # BGE Embeddings
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-base-en-v1.5"
    EMBEDDING_DEVICE: str = "cpu"
    
    # Pinecone
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str = "us-east-1-aws"
    PINECONE_INDEX_NAME: str = "book-chunks"
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 100000000  # 100MB
    
    # Chunking
    DEFAULT_CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 75
    MAX_SEMANTIC_CALLS_PER_BOOK: int = 30
    
    # Cost Limits
    MAX_EMBEDDING_TOKENS_PER_BOOK: int = 200000
    
    class Config:
        env_file = ".env"


settings = Settings()