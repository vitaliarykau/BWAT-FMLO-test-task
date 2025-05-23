from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import documents
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="PDF Processing API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])

@app.get("/")
async def root():
    return {"message": "PDF Processing API is running"} 