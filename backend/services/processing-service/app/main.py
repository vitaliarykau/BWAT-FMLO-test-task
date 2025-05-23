import sys
import os
import asyncio
import logging

# Add the common services directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'common')))

from models import DocumentProcessingRequest, DocumentStatus, ParserType
from redis_utils import redis_client
from pypdf import PdfReader
from io import BytesIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("processing-service")

class PDFProcessor:
    @staticmethod
    async def process_pdf(file_content: bytes) -> str:
        """Extract text from PDF using PyPDF"""
        try:
            pdf = PdfReader(BytesIO(file_content))
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")

async def process_document(document_id: str, filename: str, file_content: bytes, parser_type: str):
    """Process a document based on the parser type"""
    try:
        # Update document status to processing
        redis_client.update_document_metadata(
            document_id, 
            {"status": DocumentStatus.PROCESSING.value}
        )
        logger.info(f"Processing document {document_id} with parser {parser_type}")
        
        # Process PDF (currently only PyPDF is implemented)
        if parser_type == ParserType.PYPDF.value:
            text = await PDFProcessor.process_pdf(file_content)
            logger.info(f"PDF processing completed for document {document_id}")
            
            # Update document with processed content
            redis_client.update_document_metadata(
                document_id, 
                {
                    "content": text,
                    "status": DocumentStatus.COMPLETED.value
                }
            )
            logger.info(f"Document {document_id} marked as completed")
        else:
            logger.error(f"Unsupported parser type: {parser_type}")
            raise ValueError(f"Unsupported parser type: {parser_type}")
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
        # Update document with error status
        redis_client.update_document_metadata(
            document_id, 
            {
                "status": DocumentStatus.FAILED.value,
                "error": str(e)
            }
        )
        logger.error(f"Document {document_id} marked as failed")

async def start_processing_worker():
    """Start a worker to process documents from the queue"""
    logger.info("Starting PDF Processing Worker...")
    while True:
        try:
            # Use XREADGROUP for better stream handling
            results = redis_client.consume_stream(
                "pdf_processing_queue",
                "pdf_processor_group",
                "worker1",
                timeout_ms=1000
            )
            
            for message_id, message_data in results:
                # Convert message data to dictionary
                message_data = dict(message_data)
                
                # Safely get required fields
                document_id = message_data.get('document_id')
                filename = message_data.get('filename')
                parser_type = message_data.get('parser_type')
                
                # Log the message data for debugging
                logger.debug(f"Processing message: {message_data}")
                
                # Validate required fields
                if not document_id:
                    logger.error(f"Message missing document_id: {message_data}")
                    continue
                if not filename:
                    logger.error(f"Message missing filename: {message_data}")
                    continue
                if not parser_type:
                    logger.error(f"Message missing parser_type: {message_data}")
                    continue
                
                # Process the document
                document_metadata = redis_client.get_document_metadata(document_id)
                if not document_metadata:
                    logger.error(f"No metadata found for document {document_id}")
                    continue
                
                # Decode base64 file content
                file_content = document_metadata.get('file_content')
                if file_content:
                    import base64
                    file_content = base64.b64decode(file_content)
                else:
                    file_content = b''
                
                # Process the document
                await process_document(
                    document_id,
                    filename,
                    file_content,
                    parser_type
                )
                
                # Remove processed message from the queue
                redis_client.acknowledge_message("pdf_processing_queue", "pdf_processor_group", message_id)
                
                # Process the document
                document_metadata = redis_client.get_document_metadata(document_id)
                if not document_metadata:
                    logger.error(f"No metadata found for document {document_id}")
                    continue
                
                # Decode base64 file content
                file_content = document_metadata.get('file_content')
                if file_content:
                    import base64
                    file_content = base64.b64decode(file_content)
                else:
                    file_content = b''
                
                # Process the document
                await process_document(
                    document_id,
                    filename,
                    file_content,
                    parser_type
                )
                
                # Remove processed message from the queue
                redis_client.acknowledge_message("pdf_processing_queue", "pdf_processor_group", message_id)
                document_metadata = redis_client.get_document_metadata(document_id)
                
                # Decode base64 file content
                file_content = document_metadata.get('file_content')
                if file_content:
                    import base64
                    file_content = base64.b64decode(file_content)
                else:
                    file_content = b''
                
                # Process the document
                await process_document(
                    document_id,
                    message_data['filename'],
                    file_content,
                    message_data['parser_type']
                )
                
                # Remove processed message from the queue
                redis_client.client.xdel("pdf_processing_queue", message_id)
        
        except Exception as e:
            logger.error(f"Error in processing worker: {str(e)}", exc_info=True)
        
        # Avoid tight looping
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(start_processing_worker())