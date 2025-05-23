import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add the common services directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'common')))

from models import DocumentStatus
from redis_utils import redis_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("status-service")

app = FastAPI(title="Status Service", docs_url="/docs", redoc_url="/redoc")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/status/{document_id}")
async def get_document_status(document_id: str):
    """Get the status of a document by its ID"""
    logger.info(f"Received request for document status: {document_id}")
    try:
        # Retrieve document metadata from Redis
        document_metadata = redis_client.get_document_metadata(document_id)
        
        if not document_metadata:
            logger.error(f"Document not found: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Return relevant status information
        logger.info(f"Returning document status: {document_id}")
        return {
            "document_id": document_id,
            "filename": document_metadata.get('filename', ''),
            "status": document_metadata.get('status', DocumentStatus.PENDING.value),
            "parser_type": document_metadata.get('parser_type', ''),
            "content_preview": (document_metadata.get('content', '')[:200] + '...') if document_metadata.get('content') else None,
            "error": document_metadata.get('error')
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "PDF Status Service is running"}