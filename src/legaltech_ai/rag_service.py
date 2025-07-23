"""
RAG (Retrieval Augmented Generation) service using ChromaDB for vector storage.
"""

import os
import uuid
from typing import List, Dict, Any
from dotenv import load_dotenv
from watsonx_service import WatsonxService

class RAGService:
    """Simple RAG service with ChromaDB for document chunks."""
    
    def __init__(self, watsonx_service=None):
        """Initialize the RAG service."""
        load_dotenv()
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.max_results = 3
        
        # Initialize ChromaDB and watsonx service
        self._client = None
        self._collection = None
        self._watsonx_service = watsonx_service or WatsonxService()
    
    @property
    def client(self):
        """Lazy initialization of ChromaDB client."""
        if self._client is None:
            import chromadb
            self._client = chromadb.Client()
        return self._client
    
    @property
    def collection(self):
        """Lazy initialization of ChromaDB collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name="legal_documents",
                metadata={"description": "Legal document chunks for RAG"}
            )
        return self._collection
    
    @property
    def embedding_model(self):
        """Get watsonx.ai embedding service."""
        return self._watsonx_service
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings within overlap range
                for i in range(end, max(start + self.chunk_size - self.chunk_overlap, start), -1):
                    if text[i-1] in '.!?\n':
                        end = i
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start forward with overlap
            start = end - self.chunk_overlap
            
            if start >= len(text):
                break
        
        return chunks
    
    def add_document(self, document_text: str, document_name: str = "document") -> Dict[str, Any]:
        """Add a document to the RAG system."""
        try:
            # Clear existing documents for simplicity
            self.clear_documents()
            
            # Chunk the document
            chunks = self.chunk_text(document_text)
            
            if not chunks:
                return {"success": False, "error": "No chunks created from document"}
            
            # Generate embeddings using watsonx.ai
            embeddings = self.embedding_model.embed_documents(chunks)
            
            # Create IDs and metadata
            ids = [f"{document_name}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "document_name": document_name,
                    "chunk_index": i,
                    "chunk_size": len(chunk)
                }
                for i, chunk in enumerate(chunks)
            ]
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            
            return {
                "success": True,
                "chunks_created": len(chunks),
                "document_name": document_name
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def search_relevant_chunks(self, query: str) -> List[str]:
        """Search for relevant document chunks based on query."""
        try:
            # Generate query embedding using watsonx.ai
            query_embedding = [self.embedding_model.embed_query(query)]
            
            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=self.max_results
            )
            
            # Return the document chunks
            if results['documents'] and results['documents'][0]:
                return results['documents'][0]
            else:
                return []
                
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def clear_documents(self):
        """Clear all documents from the RAG system."""
        try:
            # Get all IDs and delete them
            all_items = self.collection.get()
            if all_items['ids']:
                self.collection.delete(ids=all_items['ids'])
        except Exception as e:
            print(f"Clear error: {e}")
    
    def get_context_for_query(self, query: str) -> str:
        """Get relevant context for a query."""
        relevant_chunks = self.search_relevant_chunks(query)
        
        if not relevant_chunks:
            return ""
        
        # Combine chunks with separators
        context = "\n\n---\n\n".join(relevant_chunks)
        
        # Ensure context doesn't exceed reasonable size
        max_context_length = 4000  # Leave room for query and response
        if len(context) > max_context_length:
            context = context[:max_context_length] + "\n\n[Context truncated...]"
        
        return context
    
    def has_documents(self) -> bool:
        """Check if any documents are loaded."""
        try:
            count = self.collection.count()
            return count > 0
        except:
            return False