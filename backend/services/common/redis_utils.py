import os
import redis
import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("redis-utils")

class RedisClient:
    def __init__(self, host=None, port=None, db=None):
        self.host = host or os.getenv("REDIS_HOST", "redis")
        self.port = port or int(os.getenv("REDIS_PORT", 6379))
        self.db = db or int(os.getenv("REDIS_DB", 0))
        
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db
        )
    
    def store_document_metadata(self, document_id: str, metadata: dict[str, any]):
        """Store document metadata in Redis hash"""
        try:
            # Convert all values to strings for Redis
            redis_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, datetime.datetime):
                    redis_metadata[key] = value.isoformat()
                elif isinstance(value, bytes):
                    redis_metadata[key] = value.decode('utf-8')
                else:
                    redis_metadata[key] = str(value)
            
            self.client.hset(f"document:{document_id}", mapping=redis_metadata)
        except Exception as e:
            logger.error(f"Error storing document metadata for {document_id}: {str(e)}")
            raise
    
    def get_document_metadata(self, document_id: str) -> dict[str, any] | None:
        """Get metadata for a specific document"""
        try:
            metadata = self.client.hgetall(f"document:{document_id}")
            if not metadata:
                return None
            
            # Convert datetime strings back to datetime objects
            metadata = {k.decode(): v.decode() for k, v in metadata.items()}
            if 'created_at' in metadata:
                metadata['created_at'] = datetime.fromisoformat(metadata['created_at'])
            if 'updated_at' in metadata:
                metadata['updated_at'] = datetime.fromisoformat(metadata['updated_at'])
            return metadata
        except Exception as e:
            logger.error(f"Error getting document metadata for {document_id}: {str(e)}")
            raise
    
    def update_document_metadata(self, document_id: str, updates: dict[str, any]):
        """Update document metadata in Redis hash"""
        try:
            self.client.hset(f"document:{document_id}", mapping=updates)
        except Exception as e:
            logger.error(f"Error updating document metadata for {document_id}: {str(e)}")
            raise
    
    def add_to_queue(self, queue_name: str, message: dict[str, any]):
        """Add a message to a Redis Stream"""
        try:
            self.client.xadd(queue_name, message)
        except Exception as e:
            logger.error(f"Error adding message to queue {queue_name}: {str(e)}")
            raise
    
    def read_from_queue(self, queue_name: str, block=0, count=1, last_id='>'):
        """Read messages from a Redis Stream"""
        try:
            return self.client.xread({queue_name: last_id}, block=block, count=count)
        except Exception as e:
            logger.error(f"Error reading from queue {queue_name}: {str(e)}")
            raise

    def consume_stream(self, stream_key: str, group: str, consumer: str, timeout_ms: int = 0) -> list[tuple[str, dict[str, str]]]:
        """Consume messages from a Redis stream using consumer groups.

        Args:
            stream_key: The name of the Redis stream
            group: The consumer group name
            consumer: The consumer name
            timeout_ms: Timeout in milliseconds (0 for blocking).

        Returns:
            List of tuples containing message IDs and decoded message data.
        """
        try:
            # Create consumer group if it doesn't exist
            try:
                self.client.xgroup_create(stream_key, group, mkstream=True)
            except redis.exceptions.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise

            # Read from stream with blocking
            entries = self.client.xreadgroup(
                group,
                consumer,
                {stream_key: '>'},  # '>' means read new messages
                count=1,
                block=timeout_ms
            )
            
            if not entries:
                return []
            
            # Process each entry
            results = []
            for _, messages in entries:
                for message_id, message_data in messages:
                    # Convert message data to dictionary
                    decoded_message = dict(message_data)
                    results.append((message_id, decoded_message))
            
            return results
        except Exception as e:
            logger.error(f"Error in stream consumer for {stream_key}: {str(e)}")
            raise

# Singleton Redis client
redis_client = RedisClient()