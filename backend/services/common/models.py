from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class ParserType(str, Enum):
    PYPDF = "pypdf"
    GEMINI = "gemini"

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentMetadata(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    parser_type: ParserType
    status: DocumentStatus = DocumentStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    content: Optional[bytes] = None
    summary: Optional[str] = None
    error: Optional[str] = None

class DocumentUploadRequest(BaseModel):
    filename: str
    parser_type: ParserType
    file_content: bytes

class DocumentProcessingRequest(BaseModel):
    document_id: str
    filename: str
    file_content: bytes
    parser_type: ParserType

class DocumentProcessingResponse(BaseModel):
    document_id: str
    status: DocumentStatus
    content: Optional[str] = None
    summary: Optional[str] = None
    error: Optional[str] = None 