# PyPDF Processing Service

This service handles PDF processing using PyPDF library. It's designed to work as part of a microservices architecture with Redis Streams for message queuing.

## Features

- Asynchronous PDF processing using Redis Streams
- Extracts text content from each page
- Generates basic summary statistics
- Error handling and status tracking
- Uses PyPDF for text extraction

## Environment Variables

- `REDIS_HOST`: Redis host (default: redis)
- `REDIS_PORT`: Redis port (default: 6379)
- `REDIS_DB`: Redis database number (default: 0)
- `PDF_PROCESSOR_QUEUE`: Redis Stream queue name (default: pdf_processor_queue)
- `PDF_PROCESSOR_GROUP`: Redis consumer group name (default: pdf_processor_group)

## Usage

The service runs continuously, consuming messages from the Redis Stream queue. Each message should contain:

```json
{
    "task_id": "unique-task-id",
    "file_path": "path-to-pdf-file",
    "processor_type": "pypdf"
}
```

## Error Handling

The service will update the task status in Redis with either:
- `completed` and the processing result
- `failed` and an error message

## Dependencies

- redis>=5.0.1
- pypdf>=4.0.1
- python-dotenv>=1.0.1
- pydantic>=2.6.1
