"""
Career Advisor Agent
Provides personalized career recommendations and learning paths
"""

import logging
from typing import Dict, List, Any
import json

logger = logging.getLogger(__name__)

class CareerAdvisorAgent:
    """
    Agentic component for career guidance and development
    
    Capabilities:
    - Analyze career trajectory and goals
    - Identify skill gaps
    - Recommend learning resources
    - Suggest career path options
    - Provide salary insights
    """
    
    def __init__(self, llm_service, vector_store):
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.logger = logging.getLogger(__name__)
        self.learning_resources_db = self._load_learning_resources()
    
    def get_career_advice(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive career advice
        
        Returns:
            Dictionary with recommendations, paths, salary insights, and next steps
        """
        try:
            prompt = f"""
            Analyze this professional profile and provide career advice.
            Return ONLY valid JSON:
            
            {{
                "career_summary": "Brief overview of current career stage",
                "recommendations": ["recommendation 1", "recommendation 2"],
                "career_paths": [
                    {{
                        "path": "path name",
                        "description": "description",
                        "required_skills": ["skill1"],
                        "estimated_timeline": "duration"
                    }}
                ],
                "salary_insights": {{
                    "current_market_range": "min-max",
                    "potential_range_in_2_years": "min-max",
                    "salary_growth_potential": "percentage"
                }},
                "next_steps": ["step 1", "step 2"]
            }}
            
            PROFILE:
            Experience: {resume_data.get('years_of_experience', 0)} years
            Level: {resume_data.get('experience_level', 'unknown')}
            Skills: {json.dumps(resume_data.get('skills', {}).get('technical', []))}
            """
            
            response = self.llm_service.call_claude(prompt)
            
            try:
                advice = json.loads(response)
            except json.JSONDecodeError:
                advice = self._get_default_advice(resume_data)
            
            return advice
        
        except Exception as e:
            self.logger.error(f"Error generating career advice: {str(e)}")
            return self._get_default_advice(resume_data)
    
    def analyze_skill_gaps(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze missing skills and provide learning resources
        """
        try:
            experience_level = resume_data.get('experience_level', 'mid-level')
            current_skills = set()
            
            for skill_list in resume_data.get('skills', {}).values():
                if isinstance(skill_list, list):
                    current_skills.update(skill_list)
            
            # Define skills needed for each level
            level_skills = {
                'junior': ['Git', 'SQL', 'REST APIs', 'Testing'],
                'mid-level': ['System Design', 'CI/CD', 'Databases', 'Cloud Platforms'],
                'senior': ['Architecture', 'Leadership', 'Mentoring', 'Strategic Thinking'],
                'lead': ['Team Leadership', 'Project Management', 'Budgeting', 'Strategic Planning']
            }
            
            target_level = {
                'junior': 'mid-level',
                'mid-level': 'senior',
                'senior': 'lead'
            }.get(experience_level, 'senior')
            
            required_skills = level_skills.get(target_level, [])
            gaps = [s for s in required_skills if s.lower() not in [x.lower() for x in current_skills]]
            
            # Get resources for top gaps
            resources_by_skill = {}
            for skill in gaps[:5]:
                resources_by_skill[skill] = self.get_learning_resources(skill)
            
            return {
                'current_skills': list(current_skills),
                'target_level': target_level,
                'gaps': gaps,
                'resources': resources_by_skill,
                'estimated_time': self._estimate_learning_time(len(gaps)),
                'priority_order': gaps  # Order by importance
            }
        
        except Exception as e:
            self.logger.error(f"Error analyzing skill gaps: {str(e)}")
            return {
                'gaps': [],
                'resources': {},
                'estimated_time': 'Unknown'
            }
    
    def get_learning_resources(self, skill: str) -> List[Dict[str, str]]:
        """Get learning resources for a specific skill"""
        resources = self.learning_resources_db.get(skill.lower(), [])
        if not resources:
            resources = self._get_generic_resources(skill)
        return resources[:5]  # Return top 5
    
    def _get_generic_resources(self, skill: str) -> List[Dict[str, str]]:
        """Generate generic learning resources"""
        return [
            {
                'name': f'{skill} Fundamentals Course',
                'platform': 'Udemy',
                'duration': '20 hours',
                'level': 'Beginner',
                'url': f'https://udemy.com/course/{skill.lower()}-fundamentals'
            },
            {
                'name': f'Advanced {skill} Guide',
                'platform': 'Coursera',
                'duration': '40 hours',
                'level': 'Intermediate',
                'url': f'https://coursera.org/{skill.lower()}'
            },
            {
                'name': f'{skill} Documentation',
                'platform': 'Official',
                'duration': 'Self-paced',
                'level': 'All',
                'url': f'https://{skill.lower()}.org/docs'
            }
        ]
    
    def _estimate_learning_time(self, num_skills: int) -> str:
        """Estimate time to learn skills"""
        hours = num_skills * 40  # Average 40 hours per skill
        weeks = hours / 15  # Assuming 15 hours/week
        months = weeks / 4
        
        if months < 1:
            return f"{int(weeks)} weeks"
        elif months < 12:
            return f"{int(months)} months"
        else:
            return f"{int(months / 12)} years"
    
    def _get_default_advice(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Default career advice template"""
        return {
            'career_summary': f"Professional with {resume_data.get('years_of_experience', 0)} years of experience at {resume_data.get('experience_level', 'unknown')} level",
            'recommendations': [
                'Build a strong portfolio of projects',
                'Contribute to open-source projects',
                'Develop leadership skills',
                'Stay updated with latest technologies'
            ],
            'career_paths': [
                {
                    'path': 'Technical Leadership',
                    'description': 'Move towards technical architect or staff engineer roles',
                    'required_skills': ['System Design', 'Architecture', 'Mentoring'],
                    'estimated_timeline': '2-3 years'
                },
                {
                    'path': 'Management',
                    'description': 'Transition to engineering management or team lead',
                    'required_skills': ['Leadership', 'Project Management', 'Communication'],
                    'estimated_timeline': '1-2 years'
                }
            ],
            'salary_insights': {
                'current_market_range': 'Based on location and experience',
                'potential_range_in_2_years': 'With skill development',
                'salary_growth_potential': '15-25%'
            },
            'next_steps': [
                'Take on challenging projects',
                'Seek mentorship from senior engineers',
                'Build relevant certifications',
                'Network with industry professionals'
            ]
        }
    
    def _load_learning_resources(self) -> Dict[str, List[Dict[str, str]]]:
        """Load learning resources database"""
        return {
            'python': [
                {'name': 'Python for Data Science', 'platform': 'Coursera', 'duration': '4 weeks'},
                {'name': 'Advanced Python Programming', 'platform': 'Udemy', 'duration': '30 hours'}
            ],
            'machine learning': [
                {'name': 'Machine Learning Specialization', 'platform': 'Coursera', 'duration': '3 months'},
                {'name': 'Deep Learning Course', 'platform': 'FastAI', 'duration': '7 weeks'}
            ],
            'aws': [
                {'name': 'AWS Solutions Architect Associate', 'platform': 'A Cloud Guru', 'duration': '40 hours'},
                {'name': 'AWS Certified Developer', 'platform': 'Linux Academy', 'duration': '60 hours'}
            ],
            'kubernetes': [
                {'name': 'Kubernetes Complete Course', 'platform': 'Udemy', 'duration': '20 hours'},
                {'name': 'CKA Preparation', 'platform': 'Linux Academy', 'duration': '50 hours'}
            ],
            'react': [
                {'name': 'React - The Complete Guide', 'platform': 'Udemy', 'duration': '40 hours'},
                {'name': 'Advanced React Patterns', 'platform': 'Frontend Masters', 'duration': '10 hours'}
            ]
        }
