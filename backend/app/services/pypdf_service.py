import os
from typing import Tuple
from pypdf import PdfReader
from datetime import datetime
import redis
import json
import uuid

class PyPDFService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0))
        )

    async def process_pdf(self, file_content: bytes, filename: str) -> str:
        """Process PDF file and return document ID"""
        try:
            # Create document ID
            doc_id = str(uuid.uuid4())
            
            # Create initial document record
            document = {
                "id": doc_id,
                "filename": filename,
                "parser_type": "pypdf",
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Store document in Redis
            self.redis_client.hset(f"document:{doc_id}", mapping=document)
            
            # Add to processing queue
            self.redis_client.xadd(
                "pdf_processing_queue",
                {
                    "document_id": doc_id,
                    "filename": filename,
                    "parser_type": "pypdf"
                }
            )
            
            return doc_id
            
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")

    async def extract_text(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf = PdfReader(file_content)
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")

    async def get_document(self, doc_id: str) -> dict:
        """Get document from Redis"""
        doc_data = self.redis_client.hgetall(f"document:{doc_id}")
        if not doc_data:
            raise Exception("Document not found")
        return {k.decode(): v.decode() for k, v in doc_data.items()}

    async def update_document(self, doc_id: str, updates: dict):
        """Update document in Redis"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        self.redis_client.hset(f"document:{doc_id}", mapping=updates) 