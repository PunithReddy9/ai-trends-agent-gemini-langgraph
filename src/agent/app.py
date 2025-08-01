# src/agent/app.py
"""Minimal FastAPI app for AI Trends Reporter (optional API access)"""

from fastapi import FastAPI

# Define the FastAPI app
app = FastAPI(
    title="AI Trends Reporter API",
    description="Backend API for AI Trends Report Generation",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Trends Reporter API", 
        "status": "running",
        "note": "Use 'python run_report.py' to generate reports directly"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
