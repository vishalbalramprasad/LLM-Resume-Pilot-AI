"""
FastAPI Application - Resume Parser & Job Matcher System
Main entry point for the agentic AI system
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token
import os
import logging
from datetime import datetime
import uuid
from typing import List, Optional

# Import agents and services
from agents.resume_parser import ResumeParserAgent
from agents.job_matcher import JobMatcherAgent
from agents.career_advisor import CareerAdvisorAgent
from agents.interview_prep import InterviewPrepAgent
from rag.vector_store import VectorStore
from services.llm_service import LLMService
from models.schema import (
    ResumeUploadResponse,
    GoogleCredentialRequest,
    MatchingRequest,
    MatchingResponse,
    CareerAdviceResponse,
    InterviewPrepResponse
)
from utils.config import Settings
from utils.logger import setup_logger

# Initialize FastAPI app
app = FastAPI(
    title="Resume Parser & Job Matcher API",
    description="Agentic AI system for intelligent job matching and career guidance",
    version="1.0.0"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize logger
logger = setup_logger("main")

# Load configuration
config = Settings()

# Initialize services
llm_service = LLMService(api_key=config.claude_api_key)
vector_store = VectorStore(persist_directory=config.vector_db_path)

# Initialize agents
resume_parser_agent = ResumeParserAgent(llm_service, vector_store)
job_matcher_agent = JobMatcherAgent(llm_service, vector_store)
career_advisor_agent = CareerAdvisorAgent(llm_service, vector_store)
interview_prep_agent = InterviewPrepAgent(llm_service, vector_store)

# In-memory storage (replace with database in production)
resumes_db = {}
jobs_db = {}
matches_db = {}

# ==================== Health Check ====================

@app.get("/api/auth/google/config")
async def get_google_auth_config():
    """Return the public Google OAuth client ID needed by the browser SDK."""
    if not config.google_client_id:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured on the server")
    return {"client_id": config.google_client_id}


@app.post("/api/auth/google")
async def sign_in_with_google(request: GoogleCredentialRequest):
    """Verify a Google ID token and return its trusted profile claims."""
    if not config.google_client_id:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured on the server")

    try:
        claims = id_token.verify_oauth2_token(
            request.credential,
            GoogleAuthRequest(),
            config.google_client_id,
        )
    except (ValueError, GoogleAuthError) as exc:
        raise HTTPException(status_code=401, detail="Google credential is invalid or expired") from exc

    if claims.get("email_verified") is not True:
        raise HTTPException(status_code=401, detail="Google account email is not verified")

    return {
        "subject": claims["sub"],
        "email": claims.get("email"),
        "name": claims.get("name"),
        "picture": claims.get("picture"),
    }


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "llm": "connected",
            "vector_db": "connected",
            "agents": "ready"
        }
    }

# ==================== Resume Management ====================

@app.post("/api/resume/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload and parse a resume
    
    Accepts: PDF, DOCX, TXT files
    Returns: Parsed resume data with resume_id
    """
    try:
        # Validate file type
        allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type. Accept PDF, DOCX, or TXT")
        
        # Generate unique resume ID
        resume_id = f"res_{uuid.uuid4().hex[:12]}"
        
        # Read file content
        content = await file.read()
        
        logger.info(f"Processing resume: {resume_id}")
        
        # Parse resume using agent
        parsed_data = resume_parser_agent.parse_resume(
            content=content,
            filename=file.filename,
            file_type=file.content_type
        )
        
        # Store in vector database
        vector_store.add_document(
            doc_id=resume_id,
            content=str(parsed_data),
            metadata={
                "type": "resume",
                "filename": file.filename,
                "upload_date": datetime.now().isoformat(),
                "extracted_text": parsed_data.get("full_text", "")
            }
        )
        
        # Store metadata
        resumes_db[resume_id] = {
            "id": resume_id,
            "filename": file.filename,
            "parsed_data": parsed_data,
            "upload_date": datetime.now().isoformat(),
            "status": "processed"
        }
        
        logger.info(f"Resume {resume_id} parsed successfully")
        
        return ResumeUploadResponse(
            resume_id=resume_id,
            filename=file.filename,
            status="processed",
            parsed_data=parsed_data
        )
        
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@app.get("/api/resume/parse/{resume_id}")
async def get_parsed_resume(resume_id: str):
    """Get previously parsed resume data"""
    if resume_id not in resumes_db:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return resumes_db[resume_id]

@app.delete("/api/resume/{resume_id}")
async def delete_resume(resume_id: str):
    """Delete a resume and its data"""
    if resume_id not in resumes_db:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Remove from vector store
    vector_store.delete_document(resume_id)
    
    # Remove from database
    del resumes_db[resume_id]
    
    logger.info(f"Resume {resume_id} deleted")
    
    return {"message": "Resume deleted successfully", "resume_id": resume_id}

# ==================== Job Matching ====================

@app.post("/api/matching/analyze", response_model=MatchingResponse)
async def analyze_resume_for_jobs(request: MatchingRequest):
    """
    Analyze resume and find matching jobs
    
    This endpoint:
    1. Retrieves the parsed resume
    2. Searches for relevant jobs
    3. Scores matches using AI
    4. Returns ranked job recommendations
    """
    try:
        if request.resume_id not in resumes_db:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        resume_data = resumes_db[request.resume_id]
        
        logger.info(f"Starting job matching for resume: {request.resume_id}")
        
        # Get job matches using agent
        matches = job_matcher_agent.find_matching_jobs(
            resume_data=resume_data["parsed_data"],
            preferences={
                "job_title": request.job_title,
                "location": request.location,
                "salary_range": request.salary_range,
                "experience_level": request.experience_level
            }
        )
        
        # Store matches
        match_id = f"match_{uuid.uuid4().hex[:12]}"
        matches_db[match_id] = {
            "id": match_id,
            "resume_id": request.resume_id,
            "matches": matches,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Found {len(matches)} matching jobs for {request.resume_id}")
        
        return MatchingResponse(
            match_id=match_id,
            resume_id=request.resume_id,
            matches_count=len(matches),
            matches=matches,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error during job matching: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during matching: {str(e)}")

@app.get("/api/matching/recommendations/{resume_id}")
async def get_recommendations(resume_id: str, limit: int = 10):
    """Get job recommendations for a resume"""
    if resume_id not in resumes_db:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume_data = resumes_db[resume_id]
    
    # Get recommendations
    recommendations = job_matcher_agent.get_top_recommendations(
        resume_data=resume_data["parsed_data"],
        limit=limit
    )
    
    return {
        "resume_id": resume_id,
        "recommendations": recommendations,
        "count": len(recommendations)
    }

@app.post("/api/matching/score")
async def score_resume_job(resume_id: str, job_id: str):
    """Score how well a resume matches a specific job"""
    if resume_id not in resumes_db:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume_data = resumes_db[resume_id]
    
    # Score the match
    score = job_matcher_agent.score_match(
        resume_data=resume_data["parsed_data"],
        job_id=job_id
    )
    
    return {
        "resume_id": resume_id,
        "job_id": job_id,
        "match_score": score["score"],
        "reasoning": score["reasoning"],
        "strengths": score["strengths"],
        "gaps": score["gaps"]
    }

# ==================== Career Guidance ====================

@app.get("/api/career/advice/{resume_id}", response_model=CareerAdviceResponse)
async def get_career_advice(resume_id: str):
    """
    Get personalized career recommendations and advice
    
    Provides:
    - Career path suggestions
    - Skill development recommendations
    - Salary insights
    - Next steps
    """
    try:
        if resume_id not in resumes_db:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        resume_data = resumes_db[resume_id]
        
        logger.info(f"Generating career advice for {resume_id}")
        
        # Get career advice using agent
        advice = career_advisor_agent.get_career_advice(
            resume_data=resume_data["parsed_data"]
        )
        
        return CareerAdviceResponse(
            resume_id=resume_id,
            recommendations=advice["recommendations"],
            career_paths=advice["career_paths"],
            salary_insights=advice["salary_insights"],
            next_steps=advice["next_steps"],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error generating career advice: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating advice: {str(e)}")

@app.get("/api/career/skill-gaps/{resume_id}")
async def get_skill_gaps(resume_id: str):
    """Analyze skill gaps and provide learning resources"""
    if resume_id not in resumes_db:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume_data = resumes_db[resume_id]
    
    # Analyze gaps
    gaps = career_advisor_agent.analyze_skill_gaps(
        resume_data=resume_data["parsed_data"]
    )
    
    return {
        "resume_id": resume_id,
        "skill_gaps": gaps["gaps"],
        "high_priority": gaps["high_priority"],
        "learning_resources": gaps["resources"],
        "estimated_learning_time": gaps["estimated_time"]
    }

@app.get("/api/career/learning-paths/{skill}")
async def get_learning_path(skill: str):
    """Get learning resources for a specific skill"""
    resources = career_advisor_agent.get_learning_resources(skill)
    
    return {
        "skill": skill,
        "resources": resources,
        "estimated_learning_time": "3-6 months",
        "difficulty_level": "intermediate"
    }

# ==================== Interview Preparation ====================

@app.get("/api/interview/questions/{job_id}/{resume_id}", response_model=InterviewPrepResponse)
async def generate_interview_questions(job_id: str, resume_id: str):
    """
    Generate personalized interview questions based on job and resume
    
    Returns:
    - Technical questions
    - Behavioral questions
    - Company-specific questions
    - Sample answers
    """
    try:
        if resume_id not in resumes_db:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        resume_data = resumes_db[resume_id]
        
        logger.info(f"Generating interview questions for job {job_id}")
        
        # Generate questions using agent
        questions = interview_prep_agent.generate_questions(
            job_id=job_id,
            resume_data=resume_data["parsed_data"]
        )
        
        return InterviewPrepResponse(
            job_id=job_id,
            resume_id=resume_id,
            technical_questions=questions["technical"],
            behavioral_questions=questions["behavioral"],
            company_questions=questions["company"],
            sample_answers=questions["answers"],
            tips=questions["tips"],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error generating interview questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")

@app.get("/api/interview/tips/{job_id}/{resume_id}")
async def get_interview_tips(job_id: str, resume_id: str):
    """Get job-specific interview tips and preparation strategy"""
    if resume_id not in resumes_db:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume_data = resumes_db[resume_id]
    
    # Get tips
    tips = interview_prep_agent.get_interview_tips(
        job_id=job_id,
        resume_data=resume_data["parsed_data"]
    )
    
    return {
        "job_id": job_id,
        "resume_id": resume_id,
        "tips": tips["tips"],
        "preparation_strategy": tips["strategy"],
        "key_points_to_emphasize": tips["key_points"],
        "questions_to_ask": tips["questions_to_ask"]
    }

# ==================== Statistics & Analytics ====================

@app.get("/api/stats/overview")
async def get_statistics():
    """Get system statistics"""
    return {
        "total_resumes": len(resumes_db),
        "total_matches": len(matches_db),
        "timestamp": datetime.now().isoformat(),
        "agents_status": {
            "resume_parser": "active",
            "job_matcher": "active",
            "career_advisor": "active",
            "interview_prep": "active"
        }
    }

# ==================== Error Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    logger.error(f"HTTP Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "timestamp": datetime.now().isoformat()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "timestamp": datetime.now().isoformat()}
    )

# ==================== Startup & Shutdown ====================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Resume Parser & Job Matcher API")
    logger.info("Initializing vector database...")
    logger.info("Loading agents...")
    logger.info("System ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Resume Parser & Job Matcher API")
    vector_store.close()

# ==================== Main ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
