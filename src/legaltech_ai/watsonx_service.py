"""
Simple watsonx.ai service for LegalTech AI application.
"""

import os
import requests
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

class WatsonxService:
    """Simple service for IBM watsonx.ai integration."""
    
    def __init__(self):
        """Initialize the service with environment variables."""
        load_dotenv()
        
        self.api_key = os.getenv('WATSONX_API_KEY')
        self.url = os.getenv('WATSONX_URL') 
        self.project_id = os.getenv('WATSONX_PROJECT_ID')
        self.model_id = os.getenv('MODEL_ID', 'meta-llama/llama-3-3-70b-instruct')
        
        if not all([self.api_key, self.url, self.project_id]):
            raise ValueError("Missing required watsonx.ai configuration")
        
        self._token = None
    
    def _get_access_token(self) -> str:
        """Get IBM Cloud access token."""
        if self._token:
            return self._token
            
        data = {
            'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
            'apikey': self.api_key
        }
        
        response = requests.post('https://iam.cloud.ibm.com/identity/token', data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self._token = token_data['access_token']
        return self._token
    
    def _generate_text(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate text using watsonx.ai."""
        token = self._get_access_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        data = {
            'input': prompt,
            'parameters': {
                'decoding_method': 'greedy',
                'max_new_tokens': max_tokens,
                'repetition_penalty': 1.1
            },
            'model_id': self.model_id,
            'project_id': self.project_id
        }
        
        response = requests.post(
            f'{self.url}/ml/v1/text/generation?version=2023-05-29',
            headers=headers,
            json=data
        )
        response.raise_for_status()
        
        result = response.json()
        return result['results'][0]['generated_text'].strip()
    
    def analyze_document(self, document_text: str) -> Dict[str, Any]:
        """Analyze a document for legal compliance."""
        prompt = f"""Analyze the following document for legal compliance and key insights:

Document:
{document_text}

Please provide:
1. Summary of the document
2. Key legal points
3. Potential compliance issues
4. Recommendations

Analysis:"""
        
        try:
            analysis = self._generate_text(prompt, max_tokens=1000)
            return {
                'status': 'success',
                'analysis': analysis,
                'document_length': len(document_text)
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def chat_response(self, question: str, context: str = "") -> Dict[str, Any]:
        """Get a chat response for a legal question."""
        if context:
            prompt = f"""Context: {context}

Question: {question}

Please provide a helpful legal analysis or answer based on the context provided.

Answer:"""
        else:
            prompt = f"""Question: {question}

Please provide a helpful legal analysis or general guidance.

Answer:"""
        
        try:
            response = self._generate_text(prompt, max_tokens=750)
            return {
                'status': 'success',
                'response': response
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }