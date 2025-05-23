from enum import Enum
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ParserType(str, Enum):
    PYPDF = "pypdf"
    GEMINI = "gemini"

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Document(BaseModel):
    id: str
    filename: str
    parser_type: ParserType
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    content: Optional[str] = None
    summary: Optional[str] = None
    error: Optional[str] = None

class DocumentCreate(BaseModel):
    filename: str
    parser_type: ParserType

class DocumentResponse(BaseModel):
    id: str
    filename: str
    parser_type: ParserType
    status: DocumentStatus
    content: Optional[str] = None
    summary: Optional[str] = None
    error: Optional[str] = None 