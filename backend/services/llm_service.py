"""
LLM Service - Anthropic Claude API Integration
Handles all LLM calls and prompt management
"""

import logging
import json
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for interacting with Anthropic Claude API
    
    In production, this would use actual Claude API
    For now, returns mock responses for demonstration
    """
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.api_key = api_key
        self.model = model
        self.logger = logging.getLogger(__name__)
        self.call_count = 0
        
        self.logger.info(f"Initialized LLMService with model: {model}")
    
    def call_claude(self, prompt: str, temperature: float = 0.7, 
                   max_tokens: int = 1500) -> str:
        """
        Call Claude API with given prompt
        
        Returns structured response
        """
        try:
            self.call_count += 1
            self.logger.info(f"Claude API call #{self.call_count}")
            
            # In production, use actual API call:
            # response = anthropic.Anthropic(api_key=self.api_key).messages.create(
            #     model=self.model,
            #     max_tokens=max_tokens,
            #     messages=[{"role": "user", "content": prompt}]
            # )
            # return response.content[0].text
            
            # For now, return mock response based on prompt
            return self._get_mock_response(prompt)
        
        except Exception as e:
            self.logger.error(f"Error calling Claude API: {str(e)}")
            raise
    
    def _get_mock_response(self, prompt: str) -> str:
        """
        Get mock response for demonstration
        In production, replace with actual API call
        """
        
        # Detect what kind of request this is
        if "extract" in prompt.lower() and "resume" in prompt.lower():
            return self._mock_resume_extraction()
        elif "match" in prompt.lower() or "score" in prompt.lower():
            return self._mock_job_matching()
        elif "career" in prompt.lower() or "advice" in prompt.lower():
            return self._mock_career_advice()
        elif "interview" in prompt.lower() or "question" in prompt.lower():
            return self._mock_interview_prep()
        else:
            return self._mock_generic_response()
    
    def _mock_resume_extraction(self) -> str:
        """Mock resume extraction response"""
        return json.dumps({
            "personal_info": {
                "name": "John Smith",
                "email": "john.smith@email.com",
                "phone": "+1-555-0123",
                "location": "San Francisco, CA",
                "linkedin": "linkedin.com/in/johnsmith"
            },
            "professional_summary": "Experienced software engineer with 5+ years of experience in full-stack development",
            "work_experience": [
                {
                    "company": "Tech Corp",
                    "position": "Senior Backend Engineer",
                    "start_date": "2020-01",
                    "end_date": "present",
                    "duration_years": 3.5,
                    "key_achievements": [
                        "Led redesign of core payment system",
                        "Improved API performance by 40%",
                        "Mentored 3 junior engineers"
                    ],
                    "technologies": ["Python", "FastAPI", "PostgreSQL", "AWS"]
                }
            ],
            "education": [
                {
                    "institution": "University of California",
                    "degree": "Bachelor of Science",
                    "field": "Computer Science",
                    "graduation_year": "2016"
                }
            ],
            "skills": {
                "technical": ["Python", "JavaScript", "AWS", "Docker"],
                "programming_languages": ["Python", "JavaScript", "SQL"],
                "frameworks": ["FastAPI", "React", "Django"],
                "tools": ["Docker", "Kubernetes", "Git"],
                "soft_skills": ["Leadership", "Communication", "Problem-solving"]
            },
            "certifications": [
                {
                    "name": "AWS Solutions Architect",
                    "issuer": "Amazon",
                    "year": "2021"
                }
            ],
            "projects": [
                {
                    "name": "Payment System Redesign",
                    "description": "Rewrote legacy payment processing system",
                    "technologies": ["Python", "FastAPI", "PostgreSQL"]
                }
            ],
            "years_of_experience": 5,
            "experience_level": "senior",
            "primary_skills": ["Python", "AWS", "FastAPI"]
        })
    
    def _mock_job_matching(self) -> str:
        """Mock job matching response"""
        return json.dumps({
            "match_score": 92,
            "reasoning": "Strong Python and AWS expertise matches job requirements perfectly. Backend experience aligns well.",
            "strengths": ["Python", "AWS", "API Development", "Leadership"],
            "gaps": ["Kubernetes", "Microservices"],
            "required_experience_match": 95,
            "skill_match_percentage": 88
        })
    
    def _mock_career_advice(self) -> str:
        """Mock career advice response"""
        return json.dumps({
            "career_summary": "Senior software engineer with strong technical foundation and leadership experience",
            "recommendations": [
                "Consider transitioning to Staff Engineer or Engineering Manager role",
                "Develop expertise in emerging technologies like distributed systems",
                "Lead architectural decision-making for high-impact projects",
                "Mentor more junior engineers"
            ],
            "career_paths": [
                {
                    "path": "Staff Engineer",
                    "description": "Technical leadership without management",
                    "required_skills": ["System Design", "Mentoring", "Architecture"],
                    "estimated_timeline": "1-2 years"
                },
                {
                    "path": "Engineering Manager",
                    "description": "Lead teams and manage engineers",
                    "required_skills": ["Leadership", "Project Management", "Communication"],
                    "estimated_timeline": "1-2 years"
                }
            ],
            "salary_insights": {
                "current_market_range": "$140,000 - $180,000",
                "potential_range_in_2_years": "$160,000 - $220,000",
                "salary_growth_potential": "25%"
            },
            "next_steps": [
                "Build deeper expertise in cloud architecture",
                "Lead a major project end-to-end",
                "Get AWS architect certification",
                "Network with senior engineering leaders"
            ]
        })
    
    def _mock_interview_prep(self) -> str:
        """Mock interview preparation response"""
        return json.dumps({
            "technical": [
                {
                    "question": "Design a scalable payment processing system",
                    "expected_answer": "Should discuss databases, caching, async processing",
                    "difficulty": "hard"
                }
            ],
            "behavioral": [
                {
                    "question": "Tell us about a technical decision you regret",
                    "topic": "problem-solving",
                    "example_answer": "Explain the initial approach, why it failed, what you learned"
                }
            ],
            "company": [
                {
                    "question": "What do you know about our engineering culture?",
                    "research_points": ["Recent tech blog posts", "Open source projects", "Tech stack"]
                }
            ],
            "answers": {
                "Why our company?": "Alignment with your technical interests and career goals",
                "Greatest achievement?": "Payment system redesign improving performance by 40%"
            },
            "tips": [
                "Emphasize your AWS and Python expertise",
                "Discuss scalability challenges you've solved",
                "Ask about team structure and growth opportunities"
            ]
        })
    
    def _mock_generic_response(self) -> str:
        """Generic mock response"""
        return json.dumps({
            "status": "success",
            "data": "Response generated successfully"
        })
