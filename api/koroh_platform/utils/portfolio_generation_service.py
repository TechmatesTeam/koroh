"""
Portfolio Generation AI Service for Koroh Platform

This module provides AI-powered portfolio generation capabilities using AWS Bedrock.
It creates professional website portfolios from CV data with multiple template options,
customization features, and professional content generation.
"""

import json
import logging
import re
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .ai_services import ContentGenerationService, AIServiceConfig, ModelType
from .cv_analysis_service import CVAnalysisResult
from .bedrock_config import get_model_for_task

logger = logging.getLogger(__name__)


class PortfolioTemplate(Enum):
    """Available portfolio template types."""
    PROFESSIONAL = "professional"
    CREATIVE = "creative"
    MINIMAL = "minimal"
    MODERN = "modern"
    ACADEMIC = "academic"
    EXECUTIVE = "executive"


class PortfolioStyle(Enum):
    """Portfolio content styles."""
    FORMAL = "formal"
    CONVERSATIONAL = "conversational"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    EXECUTIVE = "executive"


class ContentSection(Enum):
    """Portfolio content sections."""
    HERO = "hero"
    ABOUT = "about"
    EXPERIENCE = "experience"
    SKILLS = "skills"
    EDUCATION = "education"
    PROJECTS = "projects"
    CERTIFICATIONS = "certifications"
    CONTACT = "contact"
    TESTIMONIALS = "testimonials"
    BLOG = "blog"


@dataclass
class PortfolioTheme:
    """Portfolio visual theme configuration."""
    name: str
    primary_color: str = "#2563eb"
    secondary_color: str = "#64748b"
    accent_color: str = "#f59e0b"
    background_color: str = "#ffffff"
    text_color: str = "#1f2937"
    font_family: str = "Inter, sans-serif"
    layout_style: str = "modern"
    
    # Theme-specific settings
    use_animations: bool = True
    use_gradients: bool = False
    card_style: str = "elevated"  # flat, elevated, outlined
    spacing: str = "comfortable"  # compact, comfortable, spacious


@dataclass
class PortfolioContent:
    """Generated portfolio content for all sections."""
    hero_section: Dict[str, str] = field(default_factory=dict)
    about_section: Dict[str, str] = field(default_factory=dict)
    experience_section: List[Dict[str, Any]] = field(default_factory=list)
    skills_section: Dict[str, Any] = field(default_factory=dict)
    education_section: List[Dict[str, Any]] = field(default_factory=list)
    projects_section: List[Dict[str, Any]] = field(default_factory=list)
    certifications_section: List[Dict[str, Any]] = field(default_factory=list)
    contact_section: Dict[str, str] = field(default_factory=dict)
    
    # Metadata
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    template_used: str = ""
    style_used: str = ""
    content_quality_score: float = 0.0


@dataclass
class PortfolioGenerationOptions:
    """Options for portfolio generation."""
    template: PortfolioTemplate = PortfolioTemplate.PROFESSIONAL
    style: PortfolioStyle = PortfolioStyle.FORMAL
    theme: Optional[PortfolioTheme] = None
    
    # Content options
    include_sections: List[ContentSection] = field(default_factory=lambda: [
        ContentSection.HERO, ContentSection.ABOUT, ContentSection.EXPERIENCE,
        ContentSection.SKILLS, ContentSection.EDUCATION, ContentSection.CONTACT
    ])
    
    # Customization options
    emphasize_achievements: bool = True
    include_metrics: bool = True
    use_action_words: bool = True
    optimize_for_seo: bool = True
    target_audience: str = "recruiters"  # recruiters, clients, peers, general
    
    # Content length preferences
    hero_length: str = "medium"  # short, medium, long
    about_length: str = "medium"
    experience_detail: str = "detailed"  # brief, detailed, comprehensive
    
    # Additional features
    include_call_to_action: bool = True
    add_social_proof: bool = True
    generate_meta_tags: bool = True


class PortfolioGenerationService:
    """
    Comprehensive portfolio generation service using AWS Bedrock.
    
    This service creates professional website portfolios from CV data
    with multiple templates, styles, and customization options.
    """
    
    def __init__(self, config: Optional[AIServiceConfig] = None):
        """Initialize portfolio generation service."""
        if config is None:
            # Use optimized configuration for content generation
            config = AIServiceConfig(
                model_type=ModelType.CLAUDE_3_SONNET,
                max_tokens=4000,  # Larger token limit for comprehensive content
                temperature=0.7,  # Balanced creativity and consistency
                max_retries=2
            )
        
        self.content_service = ContentGenerationService(config)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Load default themes
        self.themes = self._load_default_themes()
    
    def generate_portfolio(
        self, 
        cv_data: CVAnalysisResult, 
        options: Optional[PortfolioGenerationOptions] = None
    ) -> PortfolioContent:
        """
        Generate complete portfolio content from CV data.
        
        Args:
            cv_data: Analyzed CV data from CVAnalysisService
            options: Portfolio generation options
            
        Returns:
            PortfolioContent with generated sections
        """
        if not cv_data or not cv_data.personal_info.name:
            raise ValueError("Valid CV data with personal information is required")
        
        options = options or PortfolioGenerationOptions()
        
        try:
            self.logger.info(f"Starting portfolio generation for {cv_data.personal_info.name}")
            
            # Initialize portfolio content
            portfolio = PortfolioContent(
                template_used=options.template.value,
                style_used=options.style.value
            )
            
            # Generate each requested section
            for section in options.include_sections:
                self._generate_section(section, cv_data, options, portfolio)
            
            # Calculate content quality score
            portfolio.content_quality_score = self._calculate_quality_score(portfolio)
            
            self.logger.info(f"Portfolio generation completed with quality score: {portfolio.content_quality_score:.2f}")
            return portfolio
            
        except Exception as e:
            self.logger.error(f"Portfolio generation failed: {e}")
            raise
    
    def _generate_section(
        self, 
        section: ContentSection, 
        cv_data: CVAnalysisResult, 
        options: PortfolioGenerationOptions,
        portfolio: PortfolioContent
    ):
        """Generate content for a specific portfolio section."""
        
        try:
            if section == ContentSection.HERO:
                portfolio.hero_section = self._generate_hero_section(cv_data, options)
            elif section == ContentSection.ABOUT:
                portfolio.about_section = self._generate_about_section(cv_data, options)
            elif section == ContentSection.EXPERIENCE:
                portfolio.experience_section = self._generate_experience_section(cv_data, options)
            elif section == ContentSection.SKILLS:
                portfolio.skills_section = self._generate_skills_section(cv_data, options)
            elif section == ContentSection.EDUCATION:
                portfolio.education_section = self._generate_education_section(cv_data, options)
            elif section == ContentSection.PROJECTS:
                portfolio.projects_section = self._generate_projects_section(cv_data, options)
            elif section == ContentSection.CERTIFICATIONS:
                portfolio.certifications_section = self._generate_certifications_section(cv_data, options)
            elif section == ContentSection.CONTACT:
                portfolio.contact_section = self._generate_contact_section(cv_data, options)
            
            self.logger.debug(f"Generated {section.value} section successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to generate {section.value} section: {e}")
    
    def _generate_hero_section(self, cv_data: CVAnalysisResult, options: PortfolioGenerationOptions) -> Dict[str, str]:
        """Generate hero section content."""
        
        # Prepare data for hero generation
        hero_data = {
            "name": cv_data.personal_info.name,
            "current_role": self._extract_current_role(cv_data),
            "location": cv_data.personal_info.location,
            "top_skills": cv_data.technical_skills[:5] if cv_data.technical_skills else cv_data.skills[:5],
            "years_experience": self._estimate_experience_years(cv_data),
            "key_achievements": self._extract_key_achievements(cv_data),
            "professional_summary": cv_data.professional_summary
        }
        
        prompt = self._build_hero_prompt(hero_data, options)
        
        input_data = {
            "data": hero_data,
            "template_type": "hero_section",
            "style": options.style.value
        }
        
        # Override with custom prompt
        response = self.content_service._invoke_model_with_retry(prompt)
        content = self.content_service._extract_response_text(response)
        
        return self._parse_hero_content(content)
    
    def _generate_about_section(self, cv_data: CVAnalysisResult, options: PortfolioGenerationOptions) -> Dict[str, str]:
        """Generate about section content."""
        
        about_data = {
            "professional_summary": cv_data.professional_summary,
            "experience_highlights": self._extract_experience_highlights(cv_data),
            "core_competencies": cv_data.technical_skills + cv_data.soft_skills,
            "career_progression": self._analyze_career_progression(cv_data),
            "unique_value_proposition": self._generate_value_proposition(cv_data),
            "personal_interests": cv_data.interests
        }
        
        prompt = self._build_about_prompt(about_data, options)
        
        response = self.content_service._invoke_model_with_retry(prompt)
        content = self.content_service._extract_response_text(response)
        
        return self._parse_about_content(content)
    
    def _generate_experience_section(self, cv_data: CVAnalysisResult, options: PortfolioGenerationOptions) -> List[Dict[str, Any]]:
        """Generate experience section content."""
        
        if not cv_data.work_experience:
            return []
        
        experience_entries = []
        
        for exp in cv_data.work_experience:
            exp_data = {
                "company": exp.company,
                "position": exp.position,
                "duration": f"{exp.start_date} - {exp.end_date}",
                "description": exp.description,
                "achievements": exp.achievements,
                "technologies": exp.technologies,
                "impact_metrics": self._extract_impact_metrics(exp.description, exp.achievements)
            }
            
            prompt = self._build_experience_prompt(exp_data, options)
            
            response = self.content_service._invoke_model_with_retry(prompt)
            content = self.content_service._extract_response_text(response)
            
            parsed_exp = self._parse_experience_content(content, exp_data)
            experience_entries.append(parsed_exp)
        
        return experience_entries
    
    def _generate_skills_section(self, cv_data: CVAnalysisResult, options: PortfolioGenerationOptions) -> Dict[str, Any]:
        """Generate skills section content."""
        
        skills_data = {
            "technical_skills": cv_data.technical_skills,
            "soft_skills": cv_data.soft_skills,
            "all_skills": cv_data.skills,
            "experience_context": cv_data.work_experience,
            "skill_categories": self._categorize_skills(cv_data)
        }
        
        prompt = self._build_skills_prompt(skills_data, options)
        
        response = self.content_service._invoke_model_with_retry(prompt)
        content = self.content_service._extract_response_text(response)
        
        return self._parse_skills_content(content)
    
    def _generate_education_section(self, cv_data: CVAnalysisResult, options: PortfolioGenerationOptions) -> List[Dict[str, Any]]:
        """Generate education section content."""
        
        if not cv_data.education:
            return []
        
        education_entries = []
        
        for edu in cv_data.education:
            edu_data = {
                "institution": edu.institution,
                "degree": edu.degree,
                "field_of_study": edu.field_of_study,
                "duration": f"{edu.start_date} - {edu.end_date}",
                "gpa": edu.gpa,
                "honors": edu.honors,
                "relevant_coursework": edu.relevant_coursework
            }
            
            parsed_edu = {
                "institution": edu_data["institution"],
                "degree": edu_data["degree"],
                "field": edu_data["field_of_study"],
                "duration": edu_data["duration"],
                "details": []
            }
            
            if edu_data["gpa"]:
                parsed_edu["details"].append(f"GPA: {edu_data['gpa']}")
            if edu_data["honors"]:
                parsed_edu["details"].append(edu_data["honors"])
            if edu_data["relevant_coursework"]:
                parsed_edu["details"].append(f"Relevant Coursework: {', '.join(edu_data['relevant_coursework'][:3])}")
            
            education_entries.append(parsed_edu)
        
        return education_entries
    
    def _generate_projects_section(self, cv_data: CVAnalysisResult, options: PortfolioGenerationOptions) -> List[Dict[str, Any]]:
        """Generate projects section content."""
        
        if not cv_data.projects:
            return []
        
        projects_entries = []
        
        for project in cv_data.projects:
            if isinstance(project, dict):
                project_data = {
                    "name": project.get("name", ""),
                    "description": project.get("description", ""),
                    "technologies": project.get("technologies", []),
                    "url": project.get("url", ""),
                    "date": project.get("date", "")
                }
                
                # Enhance project description
                if project_data["description"]:
                    prompt = f"""
                    Enhance this project description for a professional portfolio:
                    
                    Project: {project_data['name']}
                    Description: {project_data['description']}
                    Technologies: {', '.join(project_data['technologies']) if project_data['technologies'] else 'Not specified'}
                    
                    Create a compelling, professional description that highlights:
                    - Technical achievements
                    - Problem-solving approach
                    - Impact or results
                    - Technologies used effectively
                    
                    Keep it concise but impactful (2-3 sentences).
                    """
                    
                    response = self.content_service._invoke_model_with_retry(prompt)
                    enhanced_description = self.content_service._extract_response_text(response)
                    
                    project_data["enhanced_description"] = enhanced_description
                
                projects_entries.append(project_data)
        
        return projects_entries
    
    def _generate_certifications_section(self, cv_data: CVAnalysisResult, options: PortfolioGenerationOptions) -> List[Dict[str, Any]]:
        """Generate certifications section content."""
        
        if not cv_data.certifications:
            return []
        
        cert_entries = []
        
        for cert in cv_data.certifications:
            cert_data = {
                "name": cert.name,
                "issuer": cert.issuer,
                "date": cert.issue_date,
                "expiry": cert.expiry_date,
                "credential_id": cert.credential_id,
                "verification_url": cert.verification_url
            }
            cert_entries.append(cert_data)
        
        return cert_entries
    
    def _generate_contact_section(self, cv_data: CVAnalysisResult, options: PortfolioGenerationOptions) -> Dict[str, str]:
        """Generate contact section content."""
        
        contact_data = {
            "email": cv_data.personal_info.email,
            "phone": cv_data.personal_info.phone,
            "location": cv_data.personal_info.location,
            "linkedin": cv_data.personal_info.linkedin,
            "github": cv_data.personal_info.github,
            "website": cv_data.personal_info.website
        }
        
        # Generate call-to-action message
        if options.include_call_to_action:
            cta_prompt = f"""
            Create a professional call-to-action message for a portfolio contact section.
            
            Context:
            - Name: {cv_data.personal_info.name}
            - Role: {self._extract_current_role(cv_data)}
            - Target audience: {options.target_audience}
            
            Generate a compelling, professional message that encourages contact.
            Keep it warm but professional, 1-2 sentences.
            """
            
            response = self.content_service._invoke_model_with_retry(cta_prompt)
            cta_message = self.content_service._extract_response_text(response)
            contact_data["call_to_action"] = cta_message
        
        return contact_data
    
    # Helper methods for content generation
    
    def _build_hero_prompt(self, data: Dict[str, Any], options: PortfolioGenerationOptions) -> str:
        """Build prompt for hero section generation."""
        return f"""
        Create compelling hero section content for a professional portfolio website.
        
        Personal Information:
        - Name: {data['name']}
        - Current Role: {data['current_role']}
        - Location: {data['location']}
        - Years of Experience: {data['years_experience']}
        - Top Skills: {', '.join(data['top_skills'][:5])}
        
        Style: {options.style.value}
        Template: {options.template.value}
        Target Audience: {options.target_audience}
        
        Generate:
        1. Headline: A powerful, attention-grabbing headline (1 line)
        2. Subheadline: Supporting description (1-2 lines)
        3. Value Proposition: What makes this person unique (1 sentence)
        4. Call to Action: Encouraging next step (1 phrase)
        
        Format as JSON:
        {{
            "headline": "...",
            "subheadline": "...",
            "value_proposition": "...",
            "call_to_action": "..."
        }}
        
        Make it compelling, professional, and {options.style.value} in tone.
        """
    
    def _build_about_prompt(self, data: Dict[str, Any], options: PortfolioGenerationOptions) -> str:
        """Build prompt for about section generation."""
        return f"""
        Create an engaging "About" section for a professional portfolio.
        
        Background Information:
        - Professional Summary: {data['professional_summary']}
        - Core Competencies: {', '.join(data['core_competencies'][:8])}
        - Career Highlights: {data['experience_highlights']}
        - Personal Interests: {', '.join(data['personal_interests'][:3]) if data['personal_interests'] else 'Not specified'}
        
        Style: {options.style.value}
        Length: {options.about_length}
        Target Audience: {options.target_audience}
        
        Generate a compelling about section that:
        - Tells a professional story
        - Highlights unique value
        - Shows personality appropriately
        - Connects with the target audience
        
        Format as JSON:
        {{
            "main_content": "Main about text (2-3 paragraphs)",
            "key_highlights": ["highlight1", "highlight2", "highlight3"],
            "personal_touch": "Brief personal element to show personality"
        }}
        
        Make it authentic, engaging, and professionally {options.style.value}.
        """
    
    def _build_experience_prompt(self, data: Dict[str, Any], options: PortfolioGenerationOptions) -> str:
        """Build prompt for experience entry generation."""
        return f"""
        Enhance this work experience entry for a professional portfolio:
        
        Position: {data['position']} at {data['company']}
        Duration: {data['duration']}
        Original Description: {data['description']}
        Achievements: {data['achievements']}
        Technologies: {', '.join(data['technologies']) if data['technologies'] else 'Not specified'}
        
        Style: {options.style.value}
        Detail Level: {options.experience_detail}
        Emphasize Achievements: {options.emphasize_achievements}
        Include Metrics: {options.include_metrics}
        
        Create enhanced content that:
        - Uses action verbs and quantifiable results
        - Highlights impact and achievements
        - Shows progression and growth
        - Demonstrates relevant skills
        
        Format as JSON:
        {{
            "enhanced_description": "Professional description with impact focus",
            "key_achievements": ["achievement1", "achievement2", "achievement3"],
            "skills_demonstrated": ["skill1", "skill2", "skill3"],
            "impact_summary": "One sentence summarizing the overall impact"
        }}
        """
    
    def _build_skills_prompt(self, data: Dict[str, Any], options: PortfolioGenerationOptions) -> str:
        """Build prompt for skills section generation."""
        return f"""
        Create a comprehensive skills section for a professional portfolio.
        
        Skills Data:
        - Technical Skills: {', '.join(data['technical_skills'][:10])}
        - Soft Skills: {', '.join(data['soft_skills'][:8])}
        - All Skills: {', '.join(data['all_skills'][:15])}
        
        Style: {options.style.value}
        Template: {options.template.value}
        
        Organize and present skills in a compelling way:
        - Group related skills logically
        - Highlight most relevant skills
        - Show proficiency levels where appropriate
        - Make it scannable and impressive
        
        Format as JSON:
        {{
            "skill_categories": {{
                "category1": {{
                    "name": "Category Name",
                    "skills": ["skill1", "skill2"],
                    "proficiency": "Expert/Advanced/Intermediate"
                }}
            }},
            "top_skills": ["top5", "skills", "to", "highlight", "first"],
            "skills_summary": "Brief overview of skill set strength"
        }}
        """
    
    # Utility methods
    
    def _extract_current_role(self, cv_data: CVAnalysisResult) -> str:
        """Extract current or most recent role."""
        if cv_data.work_experience:
            latest_exp = cv_data.work_experience[0]  # Assuming sorted by recency
            return latest_exp.position or "Professional"
        return "Professional"
    
    def _estimate_experience_years(self, cv_data: CVAnalysisResult) -> int:
        """Estimate total years of experience."""
        if not cv_data.work_experience:
            return 0
        
        total_years = 0
        for exp in cv_data.work_experience:
            if exp.duration and "year" in exp.duration.lower():
                # Simple extraction - could be enhanced
                import re
                years_match = re.search(r'(\d+(?:\.\d+)?)\s*years?', exp.duration.lower())
                if years_match:
                    total_years += float(years_match.group(1))
                else:
                    total_years += 1  # Default assumption
            else:
                total_years += 1  # Default assumption
        
        return max(1, int(total_years))
    
    def _extract_key_achievements(self, cv_data: CVAnalysisResult) -> List[str]:
        """Extract key achievements from work experience."""
        achievements = []
        for exp in cv_data.work_experience:
            if exp.achievements:
                achievements.extend(exp.achievements[:2])  # Top 2 per job
        return achievements[:5]  # Top 5 overall
    
    def _extract_experience_highlights(self, cv_data: CVAnalysisResult) -> str:
        """Extract experience highlights summary."""
        if not cv_data.work_experience:
            return ""
        
        companies = [exp.company for exp in cv_data.work_experience if exp.company]
        roles = [exp.position for exp in cv_data.work_experience if exp.position]
        
        return f"Experience across {len(companies)} companies in roles including {', '.join(roles[:3])}"
    
    def _analyze_career_progression(self, cv_data: CVAnalysisResult) -> str:
        """Analyze career progression pattern."""
        if len(cv_data.work_experience) < 2:
            return "Building expertise in current role"
        
        # Simple progression analysis
        return f"Progressed from {cv_data.work_experience[-1].position} to {cv_data.work_experience[0].position}"
    
    def _generate_value_proposition(self, cv_data: CVAnalysisResult) -> str:
        """Generate unique value proposition."""
        top_skills = (cv_data.technical_skills + cv_data.soft_skills)[:3]
        experience_years = self._estimate_experience_years(cv_data)
        
        return f"{experience_years}+ years of expertise in {', '.join(top_skills)} with proven track record of delivering results"
    
    def _extract_impact_metrics(self, description: str, achievements: List[str]) -> List[str]:
        """Extract quantifiable metrics from descriptions."""
        metrics = []
        text = f"{description} {' '.join(achievements)}"
        
        # Look for percentage improvements
        percent_matches = re.findall(r'(\d+)%', text)
        metrics.extend([f"{p}% improvement" for p in percent_matches[:2]])
        
        # Look for user/customer numbers
        user_matches = re.findall(r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:million|k|thousand)?\s*(?:users|customers|clients)', text.lower())
        metrics.extend([f"{u} users/customers" for u in user_matches[:2]])
        
        return metrics[:3]
    
    def _categorize_skills(self, cv_data: CVAnalysisResult) -> Dict[str, List[str]]:
        """Categorize skills into logical groups."""
        categories = {
            "Programming Languages": [],
            "Frameworks & Libraries": [],
            "Tools & Technologies": [],
            "Soft Skills": cv_data.soft_skills[:6]
        }
        
        # Simple categorization - could be enhanced with ML
        for skill in cv_data.technical_skills:
            skill_lower = skill.lower()
            if any(lang in skill_lower for lang in ['python', 'java', 'javascript', 'c++', 'go', 'rust']):
                categories["Programming Languages"].append(skill)
            elif any(framework in skill_lower for framework in ['react', 'django', 'angular', 'vue', 'spring']):
                categories["Frameworks & Libraries"].append(skill)
            else:
                categories["Tools & Technologies"].append(skill)
        
        return {k: v for k, v in categories.items() if v}  # Remove empty categories
    
    def _parse_hero_content(self, content: str) -> Dict[str, str]:
        """Parse hero section content from AI response."""
        try:
            # Try to parse as JSON first
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback parsing
            return {
                "headline": content.split('\n')[0] if content else "Professional Portfolio",
                "subheadline": "Experienced professional ready to make an impact",
                "value_proposition": "Bringing expertise and dedication to every project",
                "call_to_action": "Let's connect"
            }
    
    def _parse_about_content(self, content: str) -> Dict[str, str]:
        """Parse about section content from AI response."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "main_content": content,
                "key_highlights": [],
                "personal_touch": ""
            }
    
    def _parse_experience_content(self, content: str, original_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse experience content from AI response."""
        try:
            parsed = json.loads(content)
            # Merge with original data
            return {
                **original_data,
                **parsed
            }
        except json.JSONDecodeError:
            return {
                **original_data,
                "enhanced_description": content,
                "key_achievements": [],
                "skills_demonstrated": [],
                "impact_summary": ""
            }
    
    def _parse_skills_content(self, content: str) -> Dict[str, Any]:
        """Parse skills section content from AI response."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "skill_categories": {},
                "top_skills": [],
                "skills_summary": content
            }
    
    def _calculate_quality_score(self, portfolio: PortfolioContent) -> float:
        """Calculate content quality score."""
        score = 0.0
        max_score = 10.0
        
        # Hero section quality (2 points)
        if portfolio.hero_section.get("headline"):
            score += 1.0
        if portfolio.hero_section.get("value_proposition"):
            score += 1.0
        
        # About section quality (2 points)
        if portfolio.about_section.get("main_content"):
            score += 1.0
        if len(portfolio.about_section.get("key_highlights", [])) >= 2:
            score += 1.0
        
        # Experience section quality (3 points)
        if portfolio.experience_section:
            score += 1.0
            if any(exp.get("key_achievements") for exp in portfolio.experience_section):
                score += 1.0
            if any(exp.get("impact_summary") for exp in portfolio.experience_section):
                score += 1.0
        
        # Skills section quality (2 points)
        if portfolio.skills_section.get("skill_categories"):
            score += 1.0
        if portfolio.skills_section.get("top_skills"):
            score += 1.0
        
        # Contact section quality (1 point)
        if portfolio.contact_section.get("email") or portfolio.contact_section.get("phone"):
            score += 1.0
        
        return min(score / max_score, 1.0)
    
    def _load_default_themes(self) -> Dict[str, PortfolioTheme]:
        """Load default portfolio themes."""
        return {
            "professional": PortfolioTheme(
                name="Professional",
                primary_color="#2563eb",
                secondary_color="#64748b",
                accent_color="#f59e0b"
            ),
            "creative": PortfolioTheme(
                name="Creative",
                primary_color="#7c3aed",
                secondary_color="#a78bfa",
                accent_color="#f472b6",
                use_gradients=True
            ),
            "minimal": PortfolioTheme(
                name="Minimal",
                primary_color="#1f2937",
                secondary_color="#6b7280",
                accent_color="#059669",
                use_animations=False,
                card_style="flat"
            ),
            "modern": PortfolioTheme(
                name="Modern",
                primary_color="#0ea5e9",
                secondary_color="#0f172a",
                accent_color="#f97316",
                use_gradients=True,
                card_style="elevated"
            )
        }


# Convenience function for direct portfolio generation
def generate_portfolio_from_cv(
    cv_data: CVAnalysisResult, 
    template: str = "professional",
    style: str = "formal",
    options: Optional[Dict[str, Any]] = None
) -> PortfolioContent:
    """
    Convenience function to generate portfolio directly from CV data.
    
    Args:
        cv_data: Analyzed CV data
        template: Portfolio template name
        style: Content style
        options: Additional generation options
        
    Returns:
        PortfolioContent with generated sections
    """
    generation_options = PortfolioGenerationOptions(
        template=PortfolioTemplate(template),
        style=PortfolioStyle(style)
    )
    
    # Apply additional options if provided
    if options:
        for key, value in options.items():
            if hasattr(generation_options, key):
                setattr(generation_options, key, value)
    
    service = PortfolioGenerationService()
    return service.generate_portfolio(cv_data, generation_options)