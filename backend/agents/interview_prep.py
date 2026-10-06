"""
Interview Preparation Agent
Generates personalized interview questions and preparation materials
"""

import logging
from typing import Dict, List, Any
import json

logger = logging.getLogger(__name__)

class InterviewPrepAgent:
    \"\"\"
    Agentic component for interview preparation
    
    Capabilities:
    - Generate role-specific interview questions
    - Provide sample answers
    - Create interview strategy
    - Suggest company research points
    - Identify questions to ask interviewer
    \"\"\"
    
    def __init__(self, llm_service, vector_store):
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.logger = logging.getLogger(__name__)
    
    def generate_questions(self, job_id: str, resume_data: Dict[str, Any]) -> Dict[str, List[Any]]:
        \"\"\"
        Generate personalized interview questions
        \"\"\"
        try:
            prompt = f\"\"\"
            Generate interview questions for this candidate and role.
            Return ONLY valid JSON:
            
            {{
                "technical": [
                    {{
                        "question": "question text",
                        "expected_answer": "what to look for",
                        "difficulty": "easy|medium|hard"
                    }}
                ],
                "behavioral": [
                    {{
                        "question": "question text",
                        "topic": "leadership|teamwork|problem-solving",
                        "example_answer": "sample response"
                    }}
                ],
                "company": [
                    {{
                        "question": "question about company",
                        "research_points": ["point1", "point2"]
                    }}
                ],
                "answers": {{
                    "Tell us about your background": "Structured sample answer",
                    "Why are you interested in this role": "Relevant reasons"
                }},
                "tips": ["tip1", "tip2"]
            }}
            
            CANDIDATE PROFILE:
            Experience: {resume_data.get('years_of_experience', 0)} years
            Skills: {json.dumps(resume_data.get('skills', {}).get('technical', []))}
            
            JOB REQUIREMENTS (job_id: {job_id}):
            - Similar to the jobs in our database
            \"\"\"
            
            response = self.llm_service.call_claude(prompt)
            
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                result = self._get_default_questions(resume_data)
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error generating interview questions: {str(e)}")
            return self._get_default_questions(resume_data)
    
    def get_interview_tips(self, job_id: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"
        Get comprehensive interview tips and strategy
        \"\"\"
        try:
            experience = resume_data.get('years_of_experience', 0)
            
            tips = {
                'tips': [
                    'Research the company thoroughly - check their recent news',
                    'Review job description and match your skills to requirements',
                    'Practice the STAR method for behavioral questions',
                    'Prepare 3-5 specific examples from your experience',
                    'Have 3-5 thoughtful questions ready for the interviewer',
                    'Dress professionally and arrive 10 minutes early',
                    'Make eye contact and maintain confident body language',
                    'Listen carefully and take notes',
                    'Follow up with thank you email within 24 hours'
                ],
                'strategy': self._get_interview_strategy(experience),
                'key_points_to_emphasize': self._get_key_points(resume_data),
                'questions_to_ask': self._get_candidate_questions(job_id)
            }
            
            return tips
        
        except Exception as e:
            self.logger.error(f"Error generating interview tips: {str(e)}")
            return self._get_default_tips()
    
    def _get_interview_strategy(self, years_exp: int) -> Dict[str, str]:
        \"\"\"Get interview strategy based on experience level\"\"\"
        if years_exp < 2:
            return {
                'approach': 'Focus on learning and enthusiasm',
                'emphasis': 'Highlight projects and achievements',
                'key_message': 'Show eagerness to grow and contribute'
            }
        elif years_exp < 5:
            return {
                'approach': 'Balance technical skills with soft skills',
                'emphasis': 'Discuss impact and results',
                'key_message': 'Demonstrate problem-solving abilities'
            }
        else:
            return {
                'approach': 'Position yourself as senior/leadership material',
                'emphasis': 'Discuss strategic decisions and team impact',
                'key_message': 'Showcase mentoring and leadership examples'
            }
    
    def _get_key_points(self, resume_data: Dict[str, Any]) -> List[str]:
        \"\"\"Get key points to emphasize during interview\"\"\"
        points = []
        
        # Unique skills
        skills = resume_data.get('skills', {}).get('technical', [])
        if skills:
            points.append(f\"Your expertise in {', '.join(skills[:3])}\")
        
        # Experience
        years = resume_data.get('years_of_experience', 0)
        if years > 0:
            points.append(f\"{years} years of professional experience\")
        
        # Achievements
        work_exp = resume_data.get('work_experience', [])
        if work_exp and work_exp[0].get('key_achievements'):
            achievement = work_exp[0]['key_achievements'][0]
            points.append(f\"Major achievement: {achievement}\")
        
        # Education
        education = resume_data.get('education', [])
        if education:
            degree = education[0].get('degree', 'education')
            points.append(f\"Strong foundation in {degree}\")
        
        return points
    
    def _get_candidate_questions(self, job_id: str) -> List[str]:
        \"\"\"Questions candidate should ask interviewer\"\"\"
        return [
            'What does success look like in this role after 6 months?',
            'What are the biggest challenges the team is facing right now?',
            'How does the team collaborate and what tools do you use?',
            'What opportunities are there for professional growth?',
            'Can you tell me about the team structure and who I would work with?',
            'What is the interview timeline, and when should I expect to hear back?',
            'What attracted you to working at this company?'
        ]
    
    def _get_default_questions(self, resume_data: Dict[str, Any]) -> Dict[str, List[Any]]:
        \"\"\"Default interview questions\"\"\"
        return {
            'technical': [
                {
                    'question': 'Walk us through a challenging technical problem you solved',
                    'expected_answer': 'Clear explanation of problem, approach, and solution',
                    'difficulty': 'medium'
                },
                {
                    'question': 'How do you approach system design?',
                    'expected_answer': 'Structured approach to scalability and architecture',
                    'difficulty': 'hard'
                }
            ],
            'behavioral': [
                {
                    'question': 'Tell us about a time you worked in a team on a project',
                    'topic': 'teamwork',
                    'example_answer': 'Describe your role and contribution'
                },
                {
                    'question': 'How do you handle disagreements with team members?',
                    'topic': 'problem-solving',
                    'example_answer': 'Show empathy and communication skills'
                }
            ],
            'company': [
                {
                    'question': 'What do you know about our company?',
                    'research_points': ['Recent news', 'Products/services', 'Company culture']
                }
            ],
            'answers': {
                'Tell us about yourself': 'Start with professional summary, highlight 2-3 key achievements',
                'Why do you want this job': 'Connect role to your career goals and skills'
            },
            'tips': [
                'Be specific with examples',
                'Show enthusiasm for the role',
                'Ask thoughtful questions',
                'Follow up after the interview'
            ]
        }
    
    def _get_default_tips(self) -> Dict[str, Any]:
        \"\"\"Default interview tips\"\"\"
        return {
            'tips': [
                'Prepare thoroughly',
                'Be on time',
                'Dress appropriately',
                'Show enthusiasm',
                'Ask good questions'
            ],
            'strategy': {
                'approach': 'Be professional and prepared',
                'emphasis': 'Your relevant skills and experience',
                'key_message': 'I can add value to this role'
            },
            'key_points_to_emphasize': [
                'Your relevant experience',
                'Your technical skills',
                'Your achievements'
            ],
            'questions_to_ask': [
                'What does success look like in this role?',
                'What is the team structure?',
                'What are the growth opportunities?'
            ]
        }
