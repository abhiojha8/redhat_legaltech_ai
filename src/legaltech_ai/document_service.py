"""
Simple document service that uses full document context or summarization.
No vector database required - just intelligent context management.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from watsonx_service import WatsonxService

class DocumentService:
    """Simple document service with intelligent context management."""
    
    def __init__(self, watsonx_service=None):
        """Initialize the document service."""
        load_dotenv()
        
        # Context limits (adjust based on your model's context window)
        self.max_context_length = int(os.getenv('MAX_CONTEXT_LENGTH', '30000'))  # Conservative limit
        self.max_summary_length = int(os.getenv('MAX_SUMMARY_LENGTH', '8000'))  # For summary generation
        
        # Initialize watsonx service
        self._watsonx_service = watsonx_service or WatsonxService()
        
        # Store current document
        self._document_text = None
        self._document_name = None
        self._document_summary = None
    
    def add_document(self, document_text: str, document_name: str = "document") -> Dict[str, Any]:
        """Store a document for context use."""
        try:
            self._document_text = document_text
            self._document_name = document_name
            self._document_summary = None  # Reset summary cache
            
            return {
                "success": True,
                "document_name": document_name,
                "document_length": len(document_text),
                "will_use_summary": len(document_text) > self.max_context_length,
                "chunks_created": 1  # For UI compatibility - we have 1 document
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_summary(self, text: str) -> str:
        """Generate a concise summary of the document."""
        try:
            summary_prompt = f"""Please provide a comprehensive but concise summary of the following document. 
Focus on key legal points, important clauses, obligations, rights, and any compliance-related information.
Keep the summary under {self.max_summary_length} characters while retaining all critical information.

Document:
{text[:self.max_summary_length * 3]}  

Summary:"""
            
            result = self._watsonx_service._generate_text(summary_prompt, max_tokens=500)
            return result.strip()
            
        except Exception as e:
            print(f"Summary generation error: {e}")
            # Fallback: return truncated document
            return text[:self.max_context_length] + "\n\n[Document truncated due to length...]"
    
    def get_context_for_query(self, query: str) -> str:
        """Get document context for a query - full document or summary."""
        if not self._document_text:
            return ""
        
        # If document fits within context limit, use full document
        if len(self._document_text) <= self.max_context_length:
            return self._document_text
        
        # Otherwise, generate or use cached summary
        if self._document_summary is None:
            print("Document too long for context - generating summary...")
            self._document_summary = self._generate_summary(self._document_text)
        
        return self._document_summary
    
    def has_documents(self) -> bool:
        """Check if any document is loaded."""
        return self._document_text is not None
    
    def clear_documents(self):
        """Clear the current document."""
        self._document_text = None
        self._document_name = None
        self._document_summary = None
    
    def get_document_info(self) -> Dict[str, Any]:
        """Get information about the current document."""
        if not self._document_text:
            return {"has_document": False}
        
        return {
            "has_document": True,
            "document_name": self._document_name,
            "document_length": len(self._document_text),
            "uses_summary": len(self._document_text) > self.max_context_length,
            "summary_cached": self._document_summary is not None
        }