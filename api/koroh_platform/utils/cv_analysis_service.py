"""
CV Analysis AI Service for Koroh Platform

This module provides comprehensive CV analysis capabilities using AWS Bedrock.
It extracts structured information from unstructured CV content including:
- Personal information
- Professional summary
- Skills and competencies
- Work experience
- Education and certifications
- Languages and additional qualifications
"""

import json
import logging
import re
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from datetime import datetime

from .ai_services import TextAnalysisService, AIServiceConfig, ModelType
from .bedrock_config import get_model_for_task

logger = logging.getLogger(__name__)


@dataclass
class PersonalInfo:
    """Personal information extracted from CV."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None
    github: Optional[str] = None


@dataclass
class WorkExperience:
    """Work experience entry."""
    company: Optional[str] = None
    position: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    achievements: List[str] = None
    technologies: List[str] = None
    
    def __post_init__(self):
        if self.achievements is None:
            self.achievements = []
        if self.technologies is None:
            self.technologies = []


@dataclass
class Education:
    """Education entry."""
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[str] = None
    honors: Optional[str] = None
    relevant_coursework: List[str] = None
    
    def __post_init__(self):
        if self.relevant_coursework is None:
            self.relevant_coursework = []


@dataclass
class Certification:
    """Certification or license entry."""
    name: str
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_id: Optional[str] = None
    verification_url: Optional[str] = None


@dataclass
class CVAnalysisResult:
    """Complete CV analysis result."""
    personal_info: PersonalInfo
    professional_summary: Optional[str] = None
    skills: List[str] = None
    technical_skills: List[str] = None
    soft_skills: List[str] = None
    work_experience: List[WorkExperience] = None
    education: List[Education] = None
    certifications: List[Certification] = None
    languages: List[Dict[str, str]] = None
    projects: List[Dict[str, Any]] = None
    publications: List[Dict[str, Any]] = None
    awards: List[str] = None
    volunteer_experience: List[Dict[str, Any]] = None
    interests: List[str] = None
    
    # Analysis metadata
    analysis_confidence: float = 0.0
    extracted_sections: List[str] = None
    processing_notes: List[str] = None
    
    def __post_init__(self):
        """Initialize empty lists for None values."""
        for field_name in ['skills', 'technical_skills', 'soft_skills', 'work_experience', 
                          'education', 'certifications', 'languages', 'projects', 
                          'publications', 'awards', 'volunteer_experience', 'interests',
                          'extracted_sections', 'processing_notes']:
            if getattr(self, field_name) is None:
                setattr(self, field_name, [])


class CVAnalysisService:
    """
    Comprehensive CV analysis service using AWS Bedrock.
    
    This service provides intelligent CV parsing and analysis capabilities
    with structured data extraction and validation.
    """
    
    def __init__(self, config: Optional[AIServiceConfig] = None):
        """Initialize CV analysis service."""
        if config is None:
            # Use optimized configuration for CV analysis
            config = AIServiceConfig(
                model_type=ModelType.CLAUDE_3_SONNET,
                max_tokens=4000,  # Larger token limit for comprehensive analysis
                temperature=0.2,  # Lower temperature for consistent extraction
                max_retries=3
            )
        
        self.text_service = TextAnalysisService(config)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def analyze_cv(self, cv_text: str, analysis_options: Optional[Dict[str, Any]] = None) -> CVAnalysisResult:
        """
        Analyze CV text and extract structured information.
        
        Args:
            cv_text: Raw text content of the CV
            analysis_options: Optional configuration for analysis
            
        Returns:
            CVAnalysisResult with extracted information
        """
        if not cv_text or not cv_text.strip():
            raise ValueError("CV text cannot be empty")
        
        options = analysis_options or {}
        
        try:
            self.logger.info(f"Starting CV analysis for {len(cv_text)} character document")
            
            # Step 1: Extract basic structured data
            structured_data = self._extract_structured_data(cv_text, options)
            
            # Step 2: Parse and validate the extracted data
            analysis_result = self._parse_structured_data(structured_data)
            
            # Step 3: Enhance with additional analysis
            if options.get('detailed_analysis', True):
                analysis_result = self._enhance_analysis(cv_text, analysis_result, options)
            
            # Step 4: Validate and clean the results
            analysis_result = self._validate_and_clean_results(analysis_result)
            
            self.logger.info("CV analysis completed successfully")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"CV analysis failed: {e}")
            raise
    
    def _extract_structured_data(self, cv_text: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data using AI text analysis."""
        
        # Define comprehensive extraction schema
        extraction_schema = {
            "personal_info": {
                "name": "Full name of the person",
                "email": "Email address",
                "phone": "Phone number",
                "location": "Current location/address",
                "linkedin": "LinkedIn profile URL",
                "website": "Personal website URL",
                "github": "GitHub profile URL"
            },
            "professional_summary": "Professional summary or objective statement",
            "skills": {
                "technical_skills": "List of technical skills, programming languages, tools, frameworks",
                "soft_skills": "List of soft skills and interpersonal abilities",
                "all_skills": "Complete list of all mentioned skills"
            },
            "work_experience": [
                {
                    "company": "Company name",
                    "position": "Job title/position",
                    "start_date": "Start date (format: YYYY-MM or Month YYYY)",
                    "end_date": "End date (format: YYYY-MM or Month YYYY or 'Present')",
                    "duration": "Duration of employment",
                    "description": "Job description and responsibilities",
                    "achievements": "List of key achievements and accomplishments",
                    "technologies": "Technologies and tools used in this role"
                }
            ],
            "education": [
                {
                    "institution": "Educational institution name",
                    "degree": "Degree type (Bachelor's, Master's, PhD, etc.)",
                    "field_of_study": "Major or field of study",
                    "start_date": "Start date",
                    "end_date": "End date or graduation date",
                    "gpa": "GPA if mentioned",
                    "honors": "Academic honors or distinctions",
                    "relevant_coursework": "Relevant courses or subjects"
                }
            ],
            "certifications": [
                {
                    "name": "Certification name",
                    "issuer": "Issuing organization",
                    "issue_date": "Date issued",
                    "expiry_date": "Expiry date if applicable",
                    "credential_id": "Credential ID if provided"
                }
            ],
            "languages": [
                {
                    "language": "Language name",
                    "proficiency": "Proficiency level (Native, Fluent, Intermediate, Basic)"
                }
            ],
            "projects": [
                {
                    "name": "Project name",
                    "description": "Project description",
                    "technologies": "Technologies used",
                    "url": "Project URL if available",
                    "date": "Project date or duration"
                }
            ],
            "awards": "List of awards and recognitions",
            "volunteer_experience": [
                {
                    "organization": "Organization name",
                    "role": "Volunteer role",
                    "description": "Description of volunteer work",
                    "date": "Date or duration"
                }
            ],
            "interests": "List of personal interests and hobbies"
        }
        
        # Create analysis prompt
        prompt = self._build_extraction_prompt(cv_text, extraction_schema, options)
        
        # Use text analysis service
        input_data = {
            "text": cv_text,
            "extraction_schema": extraction_schema
        }
        
        # Override the process method to use our custom prompt
        response = self.text_service._invoke_model_with_retry(prompt)
        response_text = self.text_service._extract_response_text(response)
        
        return self.text_service._parse_json_response(response_text)
    
    def _build_extraction_prompt(
        self, 
        cv_text: str, 
        schema: Dict[str, Any], 
        options: Dict[str, Any]
    ) -> str:
        """Build comprehensive extraction prompt for CV analysis."""
        
        return f"""
You are an expert CV/resume analyzer. Please analyze the following CV text and extract structured information in JSON format.

IMPORTANT INSTRUCTIONS:
1. Extract information ONLY if it's explicitly mentioned in the CV
2. Use null for missing information, don't make assumptions
3. For dates, preserve the original format when possible
4. For skills, categorize them appropriately (technical vs soft skills)
5. For work experience, extract achievements separately from general descriptions
6. Be precise and accurate - this data will be used for professional purposes

CV TEXT TO ANALYZE:
{cv_text}

EXTRACTION SCHEMA:
{json.dumps(schema, indent=2)}

Please respond with valid JSON only, following the exact schema structure above.
Ensure all extracted information is accurate and properly categorized.
If a section is not found in the CV, use an empty array [] or null as appropriate.

Focus on extracting:
- Complete and accurate personal information
- Detailed work experience with achievements
- Comprehensive skills categorization
- Educational background with relevant details
- Certifications and professional qualifications
- Any additional relevant information (projects, languages, etc.)
"""
    
    def _parse_structured_data(self, data: Dict[str, Any]) -> CVAnalysisResult:
        """Parse extracted data into structured result objects."""
        
        try:
            # Parse personal information
            personal_data = data.get('personal_info', {})
            personal_info = PersonalInfo(
                name=personal_data.get('name'),
                email=personal_data.get('email'),
                phone=personal_data.get('phone'),
                location=personal_data.get('location'),
                linkedin=personal_data.get('linkedin'),
                website=personal_data.get('website'),
                github=personal_data.get('github')
            )
            
            # Parse work experience
            work_experience = []
            for exp_data in data.get('work_experience', []):
                if isinstance(exp_data, dict):
                    experience = WorkExperience(
                        company=exp_data.get('company'),
                        position=exp_data.get('position'),
                        start_date=exp_data.get('start_date'),
                        end_date=exp_data.get('end_date'),
                        duration=exp_data.get('duration'),
                        description=exp_data.get('description'),
                        achievements=exp_data.get('achievements', []),
                        technologies=exp_data.get('technologies', [])
                    )
                    work_experience.append(experience)
            
            # Parse education
            education = []
            for edu_data in data.get('education', []):
                if isinstance(edu_data, dict):
                    edu = Education(
                        institution=edu_data.get('institution'),
                        degree=edu_data.get('degree'),
                        field_of_study=edu_data.get('field_of_study'),
                        start_date=edu_data.get('start_date'),
                        end_date=edu_data.get('end_date'),
                        gpa=edu_data.get('gpa'),
                        honors=edu_data.get('honors'),
                        relevant_coursework=edu_data.get('relevant_coursework', [])
                    )
                    education.append(edu)
            
            # Parse certifications
            certifications = []
            for cert_data in data.get('certifications', []):
                if isinstance(cert_data, dict) and cert_data.get('name'):
                    cert = Certification(
                        name=cert_data['name'],
                        issuer=cert_data.get('issuer'),
                        issue_date=cert_data.get('issue_date'),
                        expiry_date=cert_data.get('expiry_date'),
                        credential_id=cert_data.get('credential_id')
                    )
                    certifications.append(cert)
            
            # Extract skills
            skills_data = data.get('skills', {})
            if isinstance(skills_data, dict):
                technical_skills = skills_data.get('technical_skills', [])
                soft_skills = skills_data.get('soft_skills', [])
                all_skills = skills_data.get('all_skills', [])
            else:
                # Fallback if skills is a simple list
                all_skills = data.get('skills', [])
                technical_skills = []
                soft_skills = []
            
            # Create result object
            result = CVAnalysisResult(
                personal_info=personal_info,
                professional_summary=data.get('professional_summary'),
                skills=all_skills,
                technical_skills=technical_skills,
                soft_skills=soft_skills,
                work_experience=work_experience,
                education=education,
                certifications=certifications,
                languages=data.get('languages', []),
                projects=data.get('projects', []),
                publications=data.get('publications', []),
                awards=data.get('awards', []),
                volunteer_experience=data.get('volunteer_experience', []),
                interests=data.get('interests', [])
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to parse structured data: {e}")
            # Return minimal result with error info
            return CVAnalysisResult(
                personal_info=PersonalInfo(),
                processing_notes=[f"Parsing error: {str(e)}"]
            )
    
    def _enhance_analysis(
        self, 
        cv_text: str, 
        result: CVAnalysisResult, 
        options: Dict[str, Any]
    ) -> CVAnalysisResult:
        """Enhance analysis with additional insights and validation."""
        
        try:
            # Calculate analysis confidence based on extracted data completeness
            confidence = self._calculate_confidence(result)
            result.analysis_confidence = confidence
            
            # Identify extracted sections
            result.extracted_sections = self._identify_sections(cv_text)
            
            # Add processing notes
            notes = []
            if confidence < 0.5:
                notes.append("Low confidence analysis - CV may have unusual format")
            if not result.work_experience:
                notes.append("No work experience found")
            if not result.education:
                notes.append("No education information found")
            if not result.skills:
                notes.append("No skills information found")
            
            result.processing_notes.extend(notes)
            
            return result
            
        except Exception as e:
            self.logger.warning(f"Enhancement analysis failed: {e}")
            return result
    
    def _calculate_confidence(self, result: CVAnalysisResult) -> float:
        """Calculate confidence score based on extracted data completeness."""
        
        score = 0.0
        max_score = 10.0
        
        # Personal info (2 points)
        if result.personal_info.name:
            score += 1.0
        if result.personal_info.email or result.personal_info.phone:
            score += 1.0
        
        # Work experience (3 points)
        if result.work_experience:
            score += 2.0
            if any(exp.achievements for exp in result.work_experience):
                score += 1.0
        
        # Education (2 points)
        if result.education:
            score += 2.0
        
        # Skills (2 points)
        if result.skills or result.technical_skills:
            score += 1.0
        if len(result.skills + result.technical_skills) >= 5:
            score += 1.0
        
        # Professional summary (1 point)
        if result.professional_summary:
            score += 1.0
        
        return min(score / max_score, 1.0)
    
    def _identify_sections(self, cv_text: str) -> List[str]:
        """Identify sections present in the CV text."""
        
        sections = []
        text_lower = cv_text.lower()
        
        section_patterns = {
            'personal_info': ['contact', 'personal', 'profile'],
            'summary': ['summary', 'objective', 'profile', 'about'],
            'experience': ['experience', 'employment', 'work', 'career'],
            'education': ['education', 'academic', 'qualification'],
            'skills': ['skills', 'competencies', 'expertise', 'technologies'],
            'certifications': ['certification', 'license', 'credential'],
            'projects': ['projects', 'portfolio'],
            'awards': ['awards', 'honors', 'recognition'],
            'languages': ['languages', 'linguistic'],
            'interests': ['interests', 'hobbies', 'activities']
        }
        
        for section, patterns in section_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                sections.append(section)
        
        return sections
    
    def _validate_and_clean_results(self, result: CVAnalysisResult) -> CVAnalysisResult:
        """Validate and clean the analysis results."""
        
        try:
            # Clean email format
            if result.personal_info.email:
                email = result.personal_info.email.strip()
                if '@' in email and '.' in email:
                    result.personal_info.email = email
                else:
                    result.personal_info.email = None
                    result.processing_notes.append("Invalid email format detected")
            
            # Clean phone number
            if result.personal_info.phone:
                phone = re.sub(r'[^\d+\-\(\)\s]', '', result.personal_info.phone)
                result.personal_info.phone = phone.strip()
            
            # Validate URLs
            for url_field in ['linkedin', 'website', 'github']:
                url = getattr(result.personal_info, url_field)
                if url and not (url.startswith('http://') or url.startswith('https://')):
                    if not url.startswith('www.'):
                        setattr(result.personal_info, url_field, f"https://{url}")
                    else:
                        setattr(result.personal_info, url_field, f"https://{url}")
            
            # Remove duplicate skills
            if result.skills:
                result.skills = list(set(skill.strip() for skill in result.skills if skill and skill.strip()))
            if result.technical_skills:
                result.technical_skills = list(set(skill.strip() for skill in result.technical_skills if skill and skill.strip()))
            if result.soft_skills:
                result.soft_skills = list(set(skill.strip() for skill in result.soft_skills if skill and skill.strip()))
            
            return result
            
        except Exception as e:
            self.logger.warning(f"Validation and cleaning failed: {e}")
            return result
    
    def extract_skills_summary(self, result: CVAnalysisResult) -> Dict[str, Any]:
        """Extract a comprehensive skills summary from the analysis result."""
        
        all_skills = set()
        all_skills.update(result.skills or [])
        all_skills.update(result.technical_skills or [])
        all_skills.update(result.soft_skills or [])
        
        # Extract skills from work experience
        for exp in result.work_experience or []:
            all_skills.update(exp.technologies or [])
        
        # Categorize skills
        technical_keywords = [
            'python', 'java', 'javascript', 'react', 'django', 'sql', 'aws', 'docker',
            'kubernetes', 'git', 'linux', 'html', 'css', 'node', 'angular', 'vue',
            'mongodb', 'postgresql', 'redis', 'elasticsearch', 'tensorflow', 'pytorch'
        ]
        
        categorized_skills = {
            'technical': [],
            'soft': [],
            'tools': [],
            'languages': [],
            'frameworks': [],
            'databases': [],
            'cloud': []
        }
        
        for skill in all_skills:
            skill_lower = skill.lower()
            
            # Technical skills categorization
            if any(keyword in skill_lower for keyword in technical_keywords):
                if any(db in skill_lower for db in ['sql', 'mongo', 'postgres', 'redis', 'elastic']):
                    categorized_skills['databases'].append(skill)
                elif any(cloud in skill_lower for cloud in ['aws', 'azure', 'gcp', 'docker', 'kubernetes']):
                    categorized_skills['cloud'].append(skill)
                elif any(framework in skill_lower for framework in ['react', 'django', 'angular', 'vue', 'spring']):
                    categorized_skills['frameworks'].append(skill)
                elif any(lang in skill_lower for lang in ['python', 'java', 'javascript', 'c++', 'go', 'rust']):
                    categorized_skills['languages'].append(skill)
                else:
                    categorized_skills['technical'].append(skill)
            elif any(soft in skill_lower for soft in ['leadership', 'communication', 'teamwork', 'management']):
                categorized_skills['soft'].append(skill)
            else:
                categorized_skills['tools'].append(skill)
        
        return {
            'total_skills': len(all_skills),
            'categorized_skills': categorized_skills,
            'top_skills': list(all_skills)[:10],  # Top 10 skills
            'years_of_experience': self._estimate_experience_years(result)
        }
    
    def _estimate_experience_years(self, result: CVAnalysisResult) -> Optional[int]:
        """Estimate total years of experience from work history."""
        
        if not result.work_experience:
            return None
        
        total_months = 0
        current_year = datetime.now().year
        
        for exp in result.work_experience:
            try:
                # Simple estimation - this could be enhanced with better date parsing
                if exp.duration:
                    # Extract years from duration strings like "2 years", "1.5 years"
                    duration_match = re.search(r'(\d+(?:\.\d+)?)\s*years?', exp.duration.lower())
                    if duration_match:
                        years = float(duration_match.group(1))
                        total_months += years * 12
                        continue
                
                # Fallback: assume 1 year per job if no duration info
                total_months += 12
                
            except Exception:
                # If parsing fails, assume 1 year
                total_months += 12
        
        return max(1, int(total_months / 12))


# Convenience function for direct CV analysis
def analyze_cv_text(cv_text: str, options: Optional[Dict[str, Any]] = None) -> CVAnalysisResult:
    """
    Convenience function to analyze CV text directly.
    
    Args:
        cv_text: Raw CV text content
        options: Optional analysis configuration
        
    Returns:
        CVAnalysisResult with extracted information
    """
    service = CVAnalysisService()
    return service.analyze_cv(cv_text, options)