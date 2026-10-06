"""
Job Matcher Agent
Finds and matches resume to job opportunities using agentic AI
"""

import logging
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)

class JobMatcherAgent:
    """
    Agentic component for intelligent job search and matching
    
    Capabilities:
    - Search job databases using APIs
    - Score resume vs job requirements
    - Identify skill matches and gaps
    - Rank and filter opportunities
    - Provide matching rationale
    """
    
    def __init__(self, llm_service, vector_store):
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.logger = logging.getLogger(__name__)
        
        # Sample job database (in production, integrate with real APIs)
        self.jobs_database = self._load_sample_jobs()
    
    def find_matching_jobs(self, resume_data: Dict[str, Any], 
                          preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find jobs that match the candidate's profile
        
        Process:
        1. Search job database by preferences
        2. Score each job against resume
        3. Rank by match score
        4. Return top matches with reasoning
        """
        try:
            # Step 1: Initial search
            candidate_jobs = self._search_jobs(preferences)
            self.logger.info(f"Found {len(candidate_jobs)} potential jobs")
            
            # Step 2: Score and rank
            scored_matches = []
            for job in candidate_jobs:
                match_score = self.score_match(resume_data, job['id'])
                scored_matches.append({
                    'job': job,
                    'score': match_score
                })
            
            # Step 3: Sort by score
            scored_matches.sort(key=lambda x: x['score']['score'], reverse=True)
            
            # Step 4: Format results
            matches = [
                {
                    'job_id': m['job']['id'],
                    'company': m['job']['company'],
                    'position': m['job']['title'],
                    'location': m['job']['location'],
                    'salary_range': m['job'].get('salary_range'),
                    'match_score': m['score']['score'],
                    'match_percentage': min(100, m['score']['score']),
                    'reasoning': m['score']['reasoning'],
                    'strengths': m['score']['strengths'],
                    'gaps': m['score']['gaps'],
                    'apply_url': m['job'].get('url')
                }
                for m in scored_matches[:20]
            ]
            
            return matches
            
        except Exception as e:
            self.logger.error(f"Error finding matching jobs: {str(e)}")
            raise
    
    def score_match(self, resume_data: Dict[str, Any], job_id: str) -> Dict[str, Any]:
        """
        Score how well a resume matches a job
        
        Returns:
            Dictionary with score, reasoning, strengths, and gaps
        """
        try:
            # Get job details
            job = self._get_job_by_id(job_id)
            if not job:
                return {'score': 0, 'reasoning': 'Job not found', 'strengths': [], 'gaps': []}
            
            # Use LLM to score the match
            prompt = f"""
            Analyze the match between this candidate resume and job description.
            Return ONLY valid JSON with this structure:
            
            {{
                "match_score": "0-100 numeric score",
                "reasoning": "Brief explanation of the score",
                "strengths": ["matching skill 1", "matching skill 2"],
                "gaps": ["missing skill 1", "missing skill 2"],
                "required_experience_match": "0-100",
                "skill_match_percentage": "0-100"
            }}
            
            RESUME DATA:
            Name: {resume_data.get('personal_info', {}).get('name', 'Unknown')}
            Experience: {resume_data.get('years_of_experience', 0)} years
            Skills: {json.dumps(resume_data.get('skills', {}))}
            Experience: {json.dumps(resume_data.get('work_experience', [])[:2])}
            
            JOB DESCRIPTION:
            Title: {job.get('title')}
            Company: {job.get('company')}
            Required Skills: {json.dumps(job.get('required_skills', []))}
            Required Experience: {job.get('min_experience', 0)} years
            Description: {job.get('description')}
            """
            
            response = self.llm_service.call_claude(prompt)
            
            try:
                result = json.loads(response)
                result['score'] = int(result.get('match_score', 0))
                return result
            except (json.JSONDecodeError, ValueError):
                return self._calculate_score_fallback(resume_data, job)
        
        except Exception as e:
            self.logger.error(f"Error scoring match: {str(e)}")
            return {'score': 0, 'reasoning': f'Error: {str(e)}', 'strengths': [], 'gaps': []}
    
    def _calculate_score_fallback(self, resume_data: Dict[str, Any], 
                                  job: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback scoring algorithm"""
        score = 0
        strengths = []
        gaps = []
        
        # Skill matching
        resume_skills = set()
        for skill_list in resume_data.get('skills', {}).values():
            if isinstance(skill_list, list):
                resume_skills.update([s.lower() for s in skill_list])
        
        required_skills = set([s.lower() for s in job.get('required_skills', [])])
        matched_skills = resume_skills & required_skills
        missing_skills = required_skills - resume_skills
        
        skill_match = (len(matched_skills) / len(required_skills)) * 50 if required_skills else 50
        score += skill_match
        strengths.extend(list(matched_skills)[:5])
        gaps.extend(list(missing_skills)[:5])
        
        # Experience matching
        resume_years = resume_data.get('years_of_experience', 0)
        required_years = job.get('min_experience', 0)
        exp_match = min(50, (resume_years / max(required_years, 1)) * 50)
        score += exp_match
        
        return {
            'score': int(min(100, score)),
            'reasoning': f"Skill match: {int(skill_match)}%, Experience match: {int(exp_match)}%",
            'strengths': strengths,
            'gaps': gaps
        }
    
    def get_top_recommendations(self, resume_data: Dict[str, Any], 
                               limit: int = 10) -> List[Dict[str, Any]]:
        """Get top job recommendations without user-specified preferences"""
        preferences = {
            'job_title': resume_data.get('primary_skills', ['Software Engineer'])[0],
            'location': 'Remote',
            'salary_range': None,
            'experience_level': resume_data.get('experience_level', 'mid-level')
        }
        
        matches = self.find_matching_jobs(resume_data, preferences)
        return matches[:limit]
    
    def _search_jobs(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search jobs based on preferences
        
        In production, this would call real job APIs like:
        - JSearch API
        - Adzuna API
        - LinkedIn API
        """
        results = []
        
        for job in self.jobs_database:
            # Filter by preferences
            if (preferences.get('job_title') and 
                preferences['job_title'].lower() not in job['title'].lower()):
                continue
            
            if (preferences.get('location') and 
                preferences['location'].lower() != 'remote' and
                preferences['location'].lower() not in job['location'].lower()):
                continue
            
            if (preferences.get('experience_level') and 
                job.get('level', '').lower() != preferences['experience_level'].lower()):
                continue
            
            results.append(job)
        
        return results[:50]
    
    def _get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details by ID"""
        for job in self.jobs_database:
            if job['id'] == job_id:
                return job
        return None
    
    def _load_sample_jobs(self) -> List[Dict[str, Any]]:
        """Load sample job database for demonstration"""
        return [
            {
                'id': 'job_001',
                'title': 'Senior Backend Engineer',
                'company': 'TechCorp',
                'location': 'Remote',
                'level': 'senior',
                'min_experience': 5,
                'salary_range': [120000, 160000],
                'required_skills': ['Python', 'FastAPI', 'AWS', 'PostgreSQL', 'Docker', 'Kubernetes'],
                'description': 'Looking for experienced backend engineer with Python expertise...',
                'url': 'https://example.com/job/001'
            },
            {
                'id': 'job_002',
                'title': 'Full Stack Developer',
                'company': 'StartupXYZ',
                'location': 'San Francisco',
                'level': 'mid-level',
                'min_experience': 3,
                'salary_range': [100000, 140000],
                'required_skills': ['Python', 'React', 'Node.js', 'MongoDB', 'AWS'],
                'description': 'Join our growing team of full-stack developers...',
                'url': 'https://example.com/job/002'
            },
            {
                'id': 'job_003',
                'title': 'ML Engineer',
                'company': 'AI Solutions Inc',
                'location': 'Remote',
                'level': 'senior',
                'min_experience': 4,
                'salary_range': [130000, 180000],
                'required_skills': ['Python', 'Machine Learning', 'TensorFlow', 'PyTorch', 'AWS'],
                'description': 'Help us build next-generation ML models...',
                'url': 'https://example.com/job/003'
            },
            {
                'id': 'job_004',
                'title': 'DevOps Engineer',
                'company': 'CloudTech',
                'location': 'New York',
                'level': 'mid-level',
                'min_experience': 3,
                'salary_range': [110000, 150000],
                'required_skills': ['AWS', 'Docker', 'Kubernetes', 'Terraform', 'Python'],
                'description': 'Build and maintain our cloud infrastructure...',
                'url': 'https://example.com/job/004'
            },
            {
                'id': 'job_005',
                'title': 'Frontend Engineer - React',
                'company': 'WebStudio',
                'location': 'Remote',
                'level': 'mid-level',
                'min_experience': 2,
                'salary_range': [90000, 130000],
                'required_skills': ['React', 'JavaScript', 'CSS', 'REST APIs', 'Git'],
                'description': 'Create beautiful user interfaces with React...',
                'url': 'https://example.com/job/005'
            },
        ]
