import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import base64

# Add the common services directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'common')))

from models import ParserType, DocumentMetadata
from redis_utils import redis_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("upload-service")

app = FastAPI(title="PDF Upload Service", docs_url="/docs", redoc_url="/redoc")

# Configure CORS first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    logger.info("Received root endpoint request")
    return {"message": "PDF Upload Service is running"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...), parser_type: ParserType = ParserType.PYPDF):
    """Upload a PDF document for processing"""
    logger.info(f"Received upload request for file: {file.filename}")
    
    if not file.filename.endswith('.pdf'):
        logger.warning(f"Non-PDF file upload attempt: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Read file content once
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="File content is empty")
        logger.info(f"File {file.filename} read successfully")

        # Create document metadata
        document_metadata = DocumentMetadata(
            filename=file.filename,
            parser_type=parser_type
        )
        document_id = document_metadata.id
        
        # Convert datetime fields to strings before storing in Redis
        metadata_dict = document_metadata.dict()
        metadata_dict['created_at'] = metadata_dict['created_at'].isoformat()
        metadata_dict['updated_at'] = metadata_dict['updated_at'].isoformat()
        
        # Store file content as base64
        metadata_dict['file_content'] = base64.b64encode(content).decode('utf-8')
        
        # Store document metadata in Redis
        try:
            redis_client.store_document_metadata(document_id, metadata_dict)
            logger.info(f"Successfully stored metadata and file content for document {document_id}")
        except Exception as e:
            logger.error(f"Failed to store metadata for document {document_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to store document: {str(e)}")
        
        # Add to processing queue
        try:
            redis_client.add_to_queue(
                "pdf_processing_queue", 
                {
                    "document_id": document_id,
                    "filename": file.filename,
                    "parser_type": parser_type.value
                }
            )
            logger.info(f"Added document {document_id} to processing queue")
        except Exception as e:
            logger.error(f"Failed to add document {document_id} to queue: {str(e)}")
            redis_client.update_document_metadata(
                document_id, 
                {"status": "FAILED", "error": f"Failed to add to processing queue: {str(e)}"}
            )
            raise HTTPException(status_code=500, detail=f"Failed to queue document: {str(e)}")
        
        return {"document_id": document_id, "status": "uploaded"}
    
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
        document_id = upload_request.id
        metadata = upload_request.dict()
        redis_client.store_document_metadata(document_id, metadata)
        logger.info(f"Stored metadata for document {document_id}")
        
        # Add to processing queue
        redis_client.add_to_queue(
            "pdf_processing_queue", 
            {
                "document_id": document_id,
                "filename": upload_request.filename,
                "parser_type": upload_request.parser_type.value
            }
        )
        logger.info(f"Added document {document_id} to processing queue")
        
        return {"document_id": document_id, "status": "uploaded"}
    
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', 8001))
    logger.info(f"Starting upload service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

 