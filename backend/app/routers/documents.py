from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from enum import Enum
import os
import redis.asyncio as redis
from dotenv import load_dotenv
from ..services.pdf_parser import parse_pdf_pypdf #, parse_pdf_gemini, summarize_text_gemini
from typing import List
from ..models import DocumentResponse, ParserType
from ..services.pypdf_service import PyPDFService

load_dotenv() # Load environment variables from .env

router = APIRouter()
pypdf_service = PyPDFService()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
# REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") # Uncomment if you have a password

async def get_redis_connection():
    # print(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}")
    try:
        r = await redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
        await r.ping() # Check connection
        # print("Successfully connected to Redis")
        return r
    except redis.exceptions.ConnectionError as e:
        # print(f"Redis connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Could not connect to Redis: {e}")

class ParserType(str, Enum):
    PYPDF = "pypdf"
    GEMINI = "gemini"
    # MISTRAL = "mistral"

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    parser_type: ParserType = ParserType.PYPDF
):
    """Upload a PDF document for processing"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        content = await file.read()
        doc_id = await pypdf_service.process_pdf(content, file.filename)
        document = await pypdf_service.get_document(doc_id)
        return DocumentResponse(**document)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    """Get document status and content"""
    try:
        document = await pypdf_service.get_document(doc_id)
        return DocumentResponse(**document)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/status/{filename}")
async def get_document_status(filename: str, redis_client: redis.Redis = Depends(get_redis_connection)):
    status = await redis_client.get(f"document:{filename}:status")
    text = await redis_client.get(f"document:{filename}:text")
    summary = await redis_client.get(f"document:{filename}:summary") # Assuming summary is stored

    if not status:
        raise HTTPException(status_code=404, detail="Document not found or not processed yet")

    return {"filename": filename, "status": status, "text_preview": (text[:200] + "...") if text else None, "summary_preview": (summary[:200] + "...") if summary else None} 