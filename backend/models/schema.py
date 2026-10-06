"""
Data models and schemas for API requests/responses
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# ==================== Resume Models ====================

class PersonalInfo(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None

class WorkExperience(BaseModel):
    company: str
    position: str
    start_date: str
    end_date: Optional[str] = None
    duration_years: Optional[float] = None
    key_achievements: List[str] = []
    technologies: List[str] = []

class Education(BaseModel):
    institution: str
    degree: str
    field: str
    graduation_year: str

class Skills(BaseModel):
    technical: List[str] = []
    programming_languages: List[str] = []
    frameworks: List[str] = []
    tools: List[str] = []
    soft_skills: List[str] = []

class Certification(BaseModel):
    name: str
    issuer: str
    year: str

class Project(BaseModel):
    name: str
    description: str
    technologies: List[str] = []

class ParsedResume(BaseModel):
    personal_info: PersonalInfo
    professional_summary: Optional[str] = None
    work_experience: List[WorkExperience] = []
    education: List[Education] = []
    skills: Skills
    certifications: List[Certification] = []
    projects: List[Project] = []
    years_of_experience: float
    experience_level: str
    primary_skills: List[str] = []

# ==================== API Request/Response Models ====================

class ResumeUploadResponse(BaseModel):
    resume_id: str
    filename: str
    status: str
    parsed_data: Dict[str, Any]

class GoogleCredentialRequest(BaseModel):
    credential: str

class MatchingRequest(BaseModel):
    resume_id: str
    job_title: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[List[int]] = None
    experience_level: Optional[str] = None

class JobMatch(BaseModel):
    job_id: str
    company: str
    position: str
    location: str
    salary_range: Optional[List[int]] = None
    match_score: float
    match_percentage: float
    reasoning: str
    strengths: List[str]
    gaps: List[str]
    apply_url: Optional[str] = None

class MatchingResponse(BaseModel):
    match_id: str
    resume_id: str
    matches_count: int
    matches: List[JobMatch]
    timestamp: str

class MatchScore(BaseModel):
    score: float
    percentage: float
    reasoning: str
    strengths: List[str]
    gaps: List[str]

class CareerPath(BaseModel):
    path: str
    description: str
    required_skills: List[str]
    estimated_timeline: str

class SalaryInsights(BaseModel):
    current_market_range: str
    potential_range_in_2_years: str
    salary_growth_potential: str

class CareerAdviceResponse(BaseModel):
    resume_id: str
    recommendations: List[str]
    career_paths: List[CareerPath]
    salary_insights: SalaryInsights
    next_steps: List[str]
    timestamp: str

class InterviewQuestion(BaseModel):
    question: str
    expected_answer: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None

class InterviewPrepResponse(BaseModel):
    job_id: str
    resume_id: str
    technical_questions: List[InterviewQuestion]
    behavioral_questions: List[InterviewQuestion]
    company_questions: List[InterviewQuestion]
    sample_answers: Dict[str, str]
    tips: List[str]
    timestamp: str

# ==================== Database Models ====================

class ResumeRecord(BaseModel):
    id: str
    filename: str
    parsed_data: Dict[str, Any]
    upload_date: str
    status: str

class JobRecord(BaseModel):
    id: str
    title: str
    company: str
    location: str
    level: str
    min_experience: int
    salary_range: List[int]
    required_skills: List[str]
    description: str
    url: str

class MatchRecord(BaseModel):
    id: str
    resume_id: str
    job_id: str
    score: float
    timestamp: str

# ==================== Skill Analysis Models ====================

class SkillGap(BaseModel):
    skill: str
    importance: str  # high, medium, low
    learning_time: str
    resources: List[Dict[str, str]]

class SkillGapsResponse(BaseModel):
    resume_id: str
    current_skills: List[str]
    gaps: List[SkillGap]
    estimated_time: str
    priority_order: List[str]

class LearningResource(BaseModel):
    name: str
    platform: str
    duration: str
    level: str
    url: Optional[str] = None

# ==================== Statistics Models ====================

class SystemStats(BaseModel):
    total_resumes: int
    total_matches: int
    timestamp: str
    agents_status: Dict[str, str]
