"""
Vector Store and RAG Implementation
Handles document storage, retrieval, and semantic search
"""

import logging
import os
from typing import List, Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Vector store for RAG implementation
    
    In production, replace with:
    - ChromaDB
    - Pinecone
    - Weaviate
    - FAISS
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.documents = {}  # In-memory storage for demo
        self.embeddings_cache = {}
        self.logger = logging.getLogger(__name__)
        
        # Create directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        self.logger.info(f"Initialized VectorStore at {persist_directory}")
    
    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None):
        """
        Add document to vector store
        
        In production, this would:
        1. Split content into chunks
        2. Generate embeddings
        3. Store in vector database
        """
        try:
            self.documents[doc_id] = {
                'content': content,
                'metadata': metadata or {},
                'chunks': self._chunk_text(content),
                'timestamp': self._get_timestamp()
            }
            
            self.logger.info(f"Added document {doc_id} to vector store")
            
        except Exception as e:
            self.logger.error(f"Error adding document: {str(e)}")
            raise
    
    def retrieve_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve similar documents based on query
        
        In production, use cosine similarity on embeddings
        """
        try:
            results = []
            
            for doc_id, doc in self.documents.items():
                similarity = self._calculate_similarity(query, doc['content'])
                if similarity > 0.3:
                    results.append({
                        'doc_id': doc_id,
                        'content': doc['content'][:500],  # Truncate for display
                        'metadata': doc['metadata'],
                        'similarity_score': similarity
                    })
            
            # Sort by similarity
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            self.logger.error(f"Error retrieving similar documents: {str(e)}")
            return []
    
    def delete_document(self, doc_id: str):
        """Delete document from vector store"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self.logger.info(f"Deleted document {doc_id}")
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        return self.documents.get(doc_id)
    
    def search(self, query: str, doc_type: str = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search documents by query and optional filter
        """
        results = []
        
        for doc_id, doc in self.documents.items():
            # Filter by type if specified
            if doc_type and doc.get('metadata', {}).get('type') != doc_type:
                continue
            
            similarity = self._calculate_similarity(query, doc['content'])
            if similarity > 0.2:
                results.append({
                    'doc_id': doc_id,
                    'similarity': similarity,
                    'metadata': doc.get('metadata', {}),
                    'content_preview': doc['content'][:300]
                })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
    
    def _chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 100) -> List[str]:
        """
        Split text into overlapping chunks for processing
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
        """
        chunks = []
        text_len = len(text)
        
        for i in range(0, text_len, chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            chunks.append(chunk)
            
            if i + chunk_size >= text_len:
                break
        
        return chunks
    
    def _calculate_similarity(self, query: str, text: str) -> float:
        """
        Calculate similarity between query and text
        
        Simple implementation: keyword overlap
        In production, use embeddings and cosine similarity
        """
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        
        if not query_words:
            return 0.0
        
        intersection = len(query_words & text_words)
        similarity = intersection / len(query_words)
        
        return min(1.0, similarity)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def close(self):
        """Close vector store connection"""
        self.logger.info("Closing vector store")
