from typing import Dict, Any, Optional
import os
import json
import redis.asyncio as redis
from pypdf import PdfReader
from pydantic import BaseModel
from dotenv import load_dotenv
import asyncio

load_dotenv()

class ProcessingTask(BaseModel):
    task_id: str
    file_path: str
    processor_type: str
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class PDFProcessor:
    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0"))
        )
        self.queue_name = os.getenv("PDF_PROCESSOR_QUEUE", "pdf_processor_queue")
        self.group_name = os.getenv("PDF_PROCESSOR_GROUP", "pdf_processor_group")

    async def process_pdf(self, task: ProcessingTask) -> Dict[str, Any]:
        try:
            pdf_reader = PdfReader(task.file_path)
            
            # Extract text from each page
            pages = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                pages.append({
                    "page_number": page_num + 1,
                    "text": text
                })

            # Create summary (for now, just basic stats)
            total_pages = len(pages)
            total_text = " ".join(page["text"] for page in pages)
            word_count = len(total_text.split())

            result = {
                "pages": pages,
                "summary": {
                    "total_pages": total_pages,
                    "total_words": word_count,
                    "text_preview": total_text[:200] + "..." if word_count > 200 else total_text
                }
            }

            return result

        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")

    async def process_message(self, message: Dict[str, Any]):
        try:
            task = ProcessingTask(**message)
            result = await self.process_pdf(task)
            
            # Update task status in Redis
            task.status = "completed"
            task.result = result
            
            await self.redis.set(f"task:{task.task_id}", task.json())
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            await self.redis.set(f"task:{task.task_id}", task.json())

    async def consume_messages(self):
        try:
            await self.redis.xgroup_create(
                self.queue_name,
                self.group_name,
                mkstream=True
            )
        except redis.exceptions.ResponseError:
            # Group already exists
            pass

        while True:
            try:
                messages = await self.redis.xreadgroup(
                    self.group_name,
                    "consumer",
                    {self.queue_name: '>'},
                    count=1,
                    block=0
                )

                if messages:
                    message_id, message_data = messages[0][1][0]
                    message = json.loads(message_data[b'message'].decode())
                    
                    await self.process_message(message)
                    
                    # Acknowledge message
                    await self.redis.xack(
                        self.queue_name,
                        self.group_name,
                        message_id
                    )

            except Exception as e:
                print(f"Error consuming message: {e}")
                continue

    async def start(self):
        await self.consume_messages()

async def main():
    processor = PDFProcessor()
    await processor.start()

if __name__ == "__main__":
    asyncio.run(main())
