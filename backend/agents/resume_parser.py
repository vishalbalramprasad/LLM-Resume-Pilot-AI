"""
Resume Parser Agent
Extracts structured data from resume documents using LLM and RAG
"""

import json
import logging
from typing import Dict, Any, Optional
import pypdf
from io import BytesIO

logger = logging.getLogger(__name__)

class ResumeParserAgent:
    """
    Agentic component for parsing and extracting resume information
    
    Capabilities:
    - Extract personal info (name, contact, email, phone)
    - Extract work experience with dates and achievements
    - Extract education and certifications
    - Extract skills and competencies
    - Extract projects and portfolio links
    """
    
    def __init__(self, llm_service, vector_store):
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.logger = logging.getLogger(__name__)
    
    def parse_resume(self, content: bytes, filename: str, file_type: str) -> Dict[str, Any]:
        """
        Parse resume and extract structured data
        
        Args:
            content: File content (bytes)
            filename: Original filename
            file_type: MIME type of file
        
        Returns:
            Dictionary with parsed resume data
        """
        try:
            # Extract text based on file type
            if file_type == "application/pdf":
                text = self._extract_text_from_pdf(content)
            elif file_type == "text/plain":
                text = content.decode('utf-8')
            else:
                text = self._extract_text_from_docx(content)
            
            self.logger.info(f"Extracted {len(text)} characters from {filename}")
            
            # Parse structured data using LLM
            parsed_data = self._extract_structured_data(text)
            
            # Add full text for RAG
            parsed_data["full_text"] = text
            parsed_data["filename"] = filename
            
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"Error parsing resume: {str(e)}")
            raise
    
    def _extract_text_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF"""
        pdf_file = BytesIO(content)
        pdf_reader = pypdf.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        return text
    
    def _extract_text_from_docx(self, content: bytes) -> str:
        """Extract text from DOCX (simplified version)"""
        # In production, use python-docx
        return content.decode('utf-8', errors='ignore')
    
    def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """
        Use LLM to extract structured information from resume text
        """
        prompt = f"""
        Please analyze the following resume text and extract structured information.
        Return ONLY valid JSON with these exact fields:
        
        {{
            "personal_info": {{
                "name": "string",
                "email": "string",
                "phone": "string",
                "location": "string",
                "linkedin": "string or null"
            }},
            "professional_summary": "string or null",
            "work_experience": [
                {{
                    "company": "string",
                    "position": "string",
                    "start_date": "string",
                    "end_date": "string or present",
                    "duration_years": "number",
                    "key_achievements": ["string"],
                    "technologies": ["string"]
                }}
            ],
            "education": [
                {{
                    "institution": "string",
                    "degree": "string",
                    "field": "string",
                    "graduation_year": "string"
                }}
            ],
            "skills": {{
                "technical": ["string"],
                "programming_languages": ["string"],
                "frameworks": ["string"],
                "tools": ["string"],
                "soft_skills": ["string"]
            }},
            "certifications": [
                {{
                    "name": "string",
                    "issuer": "string",
                    "year": "string"
                }}
            ],
            "projects": [
                {{
                    "name": "string",
                    "description": "string",
                    "technologies": ["string"]
                }}
            ],
            "years_of_experience": "number",
            "experience_level": "junior|mid-level|senior|lead",
            "primary_skills": ["string"]
        }}
        
        Resume Text:
        {text}
        """
        
        response = self.llm_service.call_claude(prompt)
        
        try:
            # Parse JSON response
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError:
            # Fallback: extract basic info
            self.logger.warning("Failed to parse LLM JSON response, using fallback")
            return self._parse_fallback(text)
    
    def _parse_fallback(self, text: str) -> Dict[str, Any]:
        """Fallback parsing when LLM JSON fails"""
        return {
            "personal_info": {
                "name": "Unknown",
                "email": self._extract_email(text),
                "phone": self._extract_phone(text),
                "location": "Not specified",
                "linkedin": None
            },
            "professional_summary": None,
            "work_experience": [],
            "education": [],
            "skills": {
                "technical": self._extract_skills(text),
                "programming_languages": [],
                "frameworks": [],
                "tools": [],
                "soft_skills": []
            },
            "certifications": [],
            "projects": [],
            "years_of_experience": 0,
            "experience_level": "unknown",
            "primary_skills": self._extract_skills(text)
        }
    
    def _extract_email(self, text: str) -> str:
        """Extract email from text"""
        import re
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, text)
        return match.group(0) if match else "Not found"
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number from text"""
        import re
        phone_pattern = r'\b[\d\s\-\+\(\)]{10,}\b'
        match = re.search(phone_pattern, text)
        return match.group(0) if match else "Not found"
    
    def _extract_skills(self, text: str) -> list:
        """Extract common technical skills"""
        common_skills = [
            'python', 'java', 'javascript', 'c++', 'c#', 'sql', 'html', 'css',
            'react', 'angular', 'vue', 'django', 'flask', 'fastapi',
            'aws', 'gcp', 'azure', 'docker', 'kubernetes',
            'machine learning', 'deep learning', 'nlp', 'computer vision',
            'git', 'linux', 'mongodb', 'postgresql',
            'rest api', 'graphql', 'microservices'
        ]
        
        text_lower = text.lower()
        found_skills = [skill for skill in common_skills if skill in text_lower]
        return list(set(found_skills))
    
    def calculate_resume_score(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate resume quality score
        
        Evaluates:
        - Completeness (0-25 points)
        - Technical depth (0-25 points)
        - Experience (0-25 points)
        - Clarity and presentation (0-25 points)
        """
        score = 0
        details = {}
        
        # Completeness
        completeness_fields = [
            'personal_info', 'professional_summary', 'work_experience',
            'education', 'skills', 'projects'
        ]
        completeness = sum(1 for field in completeness_fields if parsed_data.get(field))
        completeness_score = (completeness / len(completeness_fields)) * 25
        score += completeness_score
        details['completeness'] = completeness_score
        
        # Technical depth
        tech_skills = len(parsed_data.get('skills', {}).get('technical', []))
        tech_score = min(25, tech_skills * 2)
        score += tech_score
        details['technical_depth'] = tech_score
        
        # Experience
        years = parsed_data.get('years_of_experience', 0)
        exp_score = min(25, years * 2)
        score += exp_score
        details['experience'] = exp_score
        
        # Clarity
        has_achievements = any(
            job.get('key_achievements') 
            for job in parsed_data.get('work_experience', [])
        )
        clarity_score = 25 if has_achievements else 10
        score += clarity_score
        details['clarity'] = clarity_score
        
        return {
            'total_score': score,
            'max_score': 100,
            'percentage': (score / 100) * 100,
            'breakdown': details,
            'rating': self._get_rating(score)
        }
    
    def _get_rating(self, score: float) -> str:
        """Get rating based on score"""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Fair"
        else:
            return "Needs Improvement"
