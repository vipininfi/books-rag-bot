from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
import torch

from app.core.config import settings


class EmbeddingService:
    """Handles text embedding generation using BGE-Base model."""
    
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.device = settings.EMBEDDING_DEVICE
        self.dimension = 768  # BGE-Base dimension
        
        # Load the model
        print(f"Loading BGE embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name, device=self.device)
        print(f"Model loaded successfully on {self.device}")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            # BGE models work best with this instruction prefix for retrieval
            if len(text) > 50:  # Only add instruction for longer texts
                text = f"Represent this document for retrieval: {text}"
            
            embedding = self.model.encode(text, convert_to_tensor=False, normalize_embeddings=True)
            return embedding.tolist()
            
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            raise e
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            # Add instruction prefix for longer texts
            processed_texts = []
            for text in texts:
                if len(text) > 50:
                    processed_texts.append(f"Represent this document for retrieval: {text}")
                else:
                    processed_texts.append(text)
            
            # Generate embeddings in batches
            batch_size = 32  # Adjust based on available memory
            all_embeddings = []
            
            for i in range(0, len(processed_texts), batch_size):
                batch = processed_texts[i:i + batch_size]
                batch_embeddings = self.model.encode(
                    batch, 
                    convert_to_tensor=False, 
                    normalize_embeddings=True,
                    show_progress_bar=True
                )
                all_embeddings.extend(batch_embeddings.tolist())
            
            return all_embeddings
            
        except Exception as e:
            print(f"Error generating batch embeddings: {str(e)}")
            raise e
    
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a search query."""
        try:
            # BGE models use different instruction for queries
            query_text = f"Represent this query for retrieving relevant documents: {query}"
            
            embedding = self.model.encode(query_text, convert_to_tensor=False, normalize_embeddings=True)
            return embedding.tolist()
            
        except Exception as e:
            print(f"Error generating query embedding: {str(e)}")
            raise e
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        return dot_product / (norm1 * norm2)
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "device": self.device,
            "max_seq_length": self.model.max_seq_length
        }