#!/usr/bin/env python
"""
AI Service Integration Tests for Koroh Platform

This test suite validates real AWS Bedrock integration by:
1. Testing CV analysis accuracy with real PDF files
2. Testing portfolio generation quality
3. Creating actual HTML/CSS/JavaScript portfolio files
4. Validating AI workflow end-to-end

Requirements: 1.1, 1.2, 6.3
"""

import os
import sys
import django
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import PyPDF2
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koroh_platform.settings')
django.setup()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_OUTPUT_DIR = Path("test_portfolio_output")
SAMPLE_CV_PATH = Path("api/media/cvs/1/test_cv.pdf")


class AIIntegrationTestSuite:
    """Comprehensive AI integration test suite."""
    
    def __init__(self):
        """Initialize test suite."""
        self.results = {}
        self.test_data = {}
        
        # Create output directory
        TEST_OUTPUT_DIR.mkdir(exist_ok=True)
        
        # Add to .gitignore if not already there
        gitignore_path = Path(".gitignore")
        gitignore_content = ""
        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text()
        
        if "test_portfolio_output/" not in gitignore_content:
            with open(gitignore_path, "a") as f:
                f.write("\n# Test portfolio output\ntest_portfolio_output/\n")
    
    def extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            logger.error(f"Failed to extract PDF text: {e}")
            return "" 
   
    def test_cv_analysis_accuracy(self) -> bool:
        """Test CV analysis accuracy with real AWS Bedrock."""
        print("\n🧠 Testing CV Analysis Accuracy with Real AWS Bedrock")
        print("=" * 70)
        
        try:
            from koroh_platform.utils.cv_analysis_service import CVAnalysisService
            
            # Check if sample CV exists
            if not SAMPLE_CV_PATH.exists():
                print(f"⚠️ Sample CV not found at {SAMPLE_CV_PATH}")
                print("Using fallback sample CV text...")
                cv_text = self._get_fallback_cv_text()
            else:
                print(f"📄 Extracting text from {SAMPLE_CV_PATH}")
                cv_text = self.extract_pdf_text(SAMPLE_CV_PATH)
                
                if not cv_text:
                    print("⚠️ PDF text extraction failed, using fallback...")
                    cv_text = self._get_fallback_cv_text()
            
            print(f"📝 CV text length: {len(cv_text)} characters")
            
            # Initialize CV analysis service
            service = CVAnalysisService()
            
            # Perform real CV analysis
            print("🔍 Analyzing CV with AWS Bedrock...")
            analysis_result = service.analyze_cv(cv_text, {
                'detailed_analysis': True
            })
            
            # Store results for portfolio generation
            self.test_data['cv_analysis'] = analysis_result
            
            # Validate analysis results
            print("\n📊 Analysis Results:")
            print(f"  Name: {analysis_result.personal_info.name}")
            print(f"  Email: {analysis_result.personal_info.email}")
            print(f"  Phone: {analysis_result.personal_info.phone}")
            print(f"  Location: {analysis_result.personal_info.location}")
            print(f"  Technical Skills: {len(analysis_result.technical_skills)}")
            print(f"  Soft Skills: {len(analysis_result.soft_skills)}")
            print(f"  Work Experience: {len(analysis_result.work_experience)}")
            print(f"  Education: {len(analysis_result.education)}")
            print(f"  Certifications: {len(analysis_result.certifications)}")
            print(f"  Analysis Confidence: {analysis_result.analysis_confidence:.2f}")
            
            # Quality checks
            quality_score = 0
            max_score = 10
            
            if analysis_result.personal_info.name:
                quality_score += 2
                print("  ✅ Name extracted")
            else:
                print("  ❌ Name not extracted")
            
            if analysis_result.personal_info.email:
                quality_score += 1
                print("  ✅ Email extracted")
            
            if analysis_result.technical_skills:
                quality_score += 2
                print(f"  ✅ Technical skills extracted: {analysis_result.technical_skills[:3]}")
            else:
                print("  ❌ No technical skills extracted")
            
            if analysis_result.work_experience:
                quality_score += 3
                print(f"  ✅ Work experience extracted: {len(analysis_result.work_experience)} positions")
            else:
                print("  ❌ No work experience extracted")
            
            if analysis_result.education:
                quality_score += 2
                print(f"  ✅ Education extracted: {len(analysis_result.education)} entries")
            
            final_score = quality_score / max_score
            print(f"\n🎯 CV Analysis Quality Score: {final_score:.2f} ({quality_score}/{max_score})")
            
            # Save analysis results
            analysis_file = TEST_OUTPUT_DIR / "cv_analysis_results.json"
            with open(analysis_file, 'w') as f:
                json.dump({
                    'personal_info': {
                        'name': analysis_result.personal_info.name,
                        'email': analysis_result.personal_info.email,
                        'phone': analysis_result.personal_info.phone,
                        'location': analysis_result.personal_info.location,
                        'linkedin': analysis_result.personal_info.linkedin,
                        'github': analysis_result.personal_info.github,
                        'website': analysis_result.personal_info.website
                    },
                    'professional_summary': analysis_result.professional_summary,
                    'technical_skills': analysis_result.technical_skills,
                    'soft_skills': analysis_result.soft_skills,
                    'work_experience': [
                        {
                            'company': exp.company,
                            'position': exp.position,
                            'start_date': exp.start_date,
                            'end_date': exp.end_date,
                            'description': exp.description,
                            'achievements': exp.achievements,
                            'technologies': exp.technologies
                        } for exp in analysis_result.work_experience
                    ],
                    'education': [
                        {
                            'institution': edu.institution,
                            'degree': edu.degree,
                            'field_of_study': edu.field_of_study,
                            'start_date': edu.start_date,
                            'end_date': edu.end_date
                        } for edu in analysis_result.education
                    ],
                    'certifications': [
                        {
                            'name': cert.name,
                            'issuer': cert.issuer,
                            'issue_date': cert.issue_date
                        } for cert in analysis_result.certifications
                    ],
                    'analysis_confidence': analysis_result.analysis_confidence,
                    'quality_score': final_score
                }, indent=2)
            
            print(f"💾 Analysis results saved to {analysis_file}")
            
            return final_score >= 0.6  # Pass if quality score is 60% or higher
            
        except Exception as e:
            print(f"❌ CV Analysis test failed: {e}")
            logger.exception("CV Analysis test error")
            return False
    
    def test_portfolio_generation_quality(self) -> bool:
        """Test portfolio generation quality with real AWS Bedrock."""
        print("\n🎨 Testing Portfolio Generation Quality with Real AWS Bedrock")
        print("=" * 70)
        
        try:
            from koroh_platform.utils.portfolio_generation_service import (
                PortfolioGenerationService, PortfolioGenerationOptions,
                PortfolioTemplate, PortfolioStyle, ContentSection
            )
            
            # Get CV analysis results from previous test
            cv_data = self.test_data.get('cv_analysis')
            if not cv_data:
                print("❌ No CV analysis data available. Run CV analysis test first.")
                return False
            
            # Initialize portfolio generation service
            service = PortfolioGenerationService()
            
            # Configure generation options
            options = PortfolioGenerationOptions(
                template=PortfolioTemplate.PROFESSIONAL,
                style=PortfolioStyle.FORMAL,
                include_sections=[
                    ContentSection.HERO,
                    ContentSection.ABOUT,
                    ContentSection.EXPERIENCE,
                    ContentSection.SKILLS,
                    ContentSection.EDUCATION,
                    ContentSection.CONTACT
                ],
                target_audience="recruiters",
                emphasize_achievements=True,
                include_metrics=True,
                include_call_to_action=True
            )
            
            # Generate portfolio with real AWS Bedrock
            print("🚀 Generating portfolio with AWS Bedrock...")
            portfolio = service.generate_portfolio(cv_data, options)
            
            # Store results for HTML generation
            self.test_data['portfolio'] = portfolio
            
            # Validate portfolio results
            print("\n📋 Portfolio Generation Results:")
            print(f"  Template: {portfolio.template_used}")
            print(f"  Style: {portfolio.style_used}")
            print(f"  Quality Score: {portfolio.content_quality_score:.2f}")
            print(f"  Generated At: {portfolio.generated_at}")
            
            # Quality checks
            quality_score = 0
            max_score = 12
            
            # Hero section
            if portfolio.hero_section.get('headline'):
                quality_score += 2
                print(f"  ✅ Hero headline: {portfolio.hero_section['headline'][:50]}...")
            else:
                print("  ❌ No hero headline generated")
            
            if portfolio.hero_section.get('value_proposition'):
                quality_score += 1
                print("  ✅ Value proposition generated")
            
            # About section
            if portfolio.about_section.get('main_content'):
                content_length = len(portfolio.about_section['main_content'])
                quality_score += 2
                print(f"  ✅ About content: {content_length} characters")
            else:
                print("  ❌ No about content generated")
            
            if portfolio.about_section.get('key_highlights'):
                quality_score += 1
                print(f"  ✅ Key highlights: {len(portfolio.about_section['key_highlights'])} items")
            
            # Experience section
            if portfolio.experience_section:
                quality_score += 3
                print(f"  ✅ Experience entries: {len(portfolio.experience_section)}")
                
                # Check for enhanced descriptions
                enhanced_count = sum(1 for exp in portfolio.experience_section 
                                   if exp.get('enhanced_description'))
                if enhanced_count > 0:
                    quality_score += 1
                    print(f"  ✅ Enhanced descriptions: {enhanced_count}")
            else:
                print("  ❌ No experience content generated")
            
            # Skills section
            if portfolio.skills_section.get('skill_categories'):
                quality_score += 2
                categories = len(portfolio.skills_section['skill_categories'])
                print(f"  ✅ Skill categories: {categories}")
            else:
                print("  ❌ No skills content generated")
            
            # Contact section
            if portfolio.contact_section.get('email'):
                quality_score += 1
                print("  ✅ Contact information included")
            
            final_score = quality_score / max_score
            print(f"\n🎯 Portfolio Generation Quality Score: {final_score:.2f} ({quality_score}/{max_score})")
            
            # Save portfolio results
            portfolio_file = TEST_OUTPUT_DIR / "portfolio_content.json"
            with open(portfolio_file, 'w') as f:
                json.dump({
                    'template_used': portfolio.template_used,
                    'style_used': portfolio.style_used,
                    'hero_section': portfolio.hero_section,
                    'about_section': portfolio.about_section,
                    'experience_section': portfolio.experience_section,
                    'skills_section': portfolio.skills_section,
                    'education_section': portfolio.education_section,
                    'contact_section': portfolio.contact_section,
                    'content_quality_score': portfolio.content_quality_score,
                    'generated_at': portfolio.generated_at,
                    'test_quality_score': final_score
                }, indent=2)
            
            print(f"💾 Portfolio content saved to {portfolio_file}")
            
            return final_score >= 0.7  # Pass if quality score is 70% or higher
            
        except Exception as e:
            print(f"❌ Portfolio Generation test failed: {e}")
            logger.exception("Portfolio Generation test error")
            return False    

    def generate_html_portfolio(self) -> bool:
        """Generate actual HTML/CSS/JavaScript portfolio for preview."""
        print("\n🌐 Generating HTML/CSS/JavaScript Portfolio")
        print("=" * 70)
        
        try:
            # Get portfolio data from previous test
            portfolio = self.test_data.get('portfolio')
            cv_data = self.test_data.get('cv_analysis')
            
            if not portfolio or not cv_data:
                print("❌ No portfolio or CV data available. Run previous tests first.")
                return False
            
            # Create portfolio directory
            portfolio_dir = TEST_OUTPUT_DIR / "portfolio_website"
            portfolio_dir.mkdir(exist_ok=True)
            
            # Generate HTML
            html_content = self._generate_html_template(portfolio, cv_data)
            html_file = portfolio_dir / "index.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Generate CSS
            css_content = self._generate_css_styles()
            css_file = portfolio_dir / "styles.css"
            with open(css_file, 'w', encoding='utf-8') as f:
                f.write(css_content)
            
            # Generate JavaScript
            js_content = self._generate_javascript()
            js_file = portfolio_dir / "script.js"
            with open(js_file, 'w', encoding='utf-8') as f:
                f.write(js_content)
            
            # Create README with instructions
            readme_content = self._generate_readme(cv_data.personal_info.name or "Professional")
            readme_file = portfolio_dir / "README.md"
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            print(f"✅ HTML portfolio generated successfully!")
            print(f"📁 Portfolio location: {portfolio_dir.absolute()}")
            print(f"🌐 Open {html_file.absolute()} in your browser to preview")
            print(f"📖 See {readme_file.absolute()} for instructions")
            
            # Validate generated files
            required_files = ['index.html', 'styles.css', 'script.js', 'README.md']
            all_files_exist = all((portfolio_dir / file).exists() for file in required_files)
            
            if all_files_exist:
                print("✅ All required files generated successfully")
                
                # Check file sizes
                for file in required_files:
                    file_path = portfolio_dir / file
                    size = file_path.stat().st_size
                    print(f"  {file}: {size} bytes")
                
                return True
            else:
                print("❌ Some required files are missing")
                return False
            
        except Exception as e:
            print(f"❌ HTML Portfolio generation failed: {e}")
            logger.exception("HTML Portfolio generation error")
            return False
    
    def _generate_html_template(self, portfolio, cv_data) -> str:
        """Generate HTML template for the portfolio."""
        name = cv_data.personal_info.name or "Professional Portfolio"
        hero = portfolio.hero_section
        about = portfolio.about_section
        experience = portfolio.experience_section
        skills = portfolio.skills_section
        education = portfolio.education_section
        contact = portfolio.contact_section
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - Professional Portfolio</title>
    <link rel="stylesheet" href="styles.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar">
        <div class="nav-container">
            <div class="nav-logo">{name.split()[0] if name else "Portfolio"}</div>
            <ul class="nav-menu">
                <li><a href="#home" class="nav-link">Home</a></li>
                <li><a href="#about" class="nav-link">About</a></li>
                <li><a href="#experience" class="nav-link">Experience</a></li>
                <li><a href="#skills" class="nav-link">Skills</a></li>
                <li><a href="#education" class="nav-link">Education</a></li>
                <li><a href="#contact" class="nav-link">Contact</a></li>
            </ul>
            <div class="hamburger">
                <span class="bar"></span>
                <span class="bar"></span>
                <span class="bar"></span>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section id="home" class="hero">
        <div class="hero-container">
            <div class="hero-content">
                <h1 class="hero-title">{hero.get('headline', name)}</h1>
                <p class="hero-subtitle">{hero.get('subheadline', 'Professional Portfolio')}</p>
                <p class="hero-description">{hero.get('value_proposition', 'Passionate about creating innovative solutions')}</p>
                <div class="hero-buttons">
                    <a href="#contact" class="btn btn-primary">{hero.get('call_to_action', 'Get In Touch')}</a>
                    <a href="#about" class="btn btn-secondary">Learn More</a>
                </div>
            </div>
        </div>
    </section>

    <!-- About Section -->
    <section id="about" class="about">
        <div class="container">
            <h2 class="section-title">About Me</h2>
            <div class="about-content">
                <div class="about-text">
                    <p>{about.get('main_content', 'Professional with extensive experience in technology and innovation.')}</p>
                    {self._format_highlights(about.get('key_highlights', []))}
                </div>
            </div>
        </div>
    </section>

    <!-- Experience Section -->
    <section id="experience" class="experience">
        <div class="container">
            <h2 class="section-title">Professional Experience</h2>
            <div class="timeline">
                {self._format_experience(experience)}
            </div>
        </div>
    </section>

    <!-- Skills Section -->
    <section id="skills" class="skills">
        <div class="container">
            <h2 class="section-title">Skills & Expertise</h2>
            <div class="skills-grid">
                {self._format_skills(skills)}
            </div>
        </div>
    </section>

    <!-- Education Section -->
    <section id="education" class="education">
        <div class="container">
            <h2 class="section-title">Education</h2>
            <div class="education-grid">
                {self._format_education(education)}
            </div>
        </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="contact">
        <div class="container">
            <h2 class="section-title">Get In Touch</h2>
            <div class="contact-content">
                <div class="contact-info">
                    {self._format_contact(contact, cv_data.personal_info)}
                </div>
                <div class="contact-form">
                    <form id="contactForm">
                        <div class="form-group">
                            <input type="text" id="name" name="name" placeholder="Your Name" required>
                        </div>
                        <div class="form-group">
                            <input type="email" id="email" name="email" placeholder="Your Email" required>
                        </div>
                        <div class="form-group">
                            <textarea id="message" name="message" placeholder="Your Message" rows="5" required></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary">Send Message</button>
                    </form>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <p>&copy; 2024 {name}. Generated by Koroh AI Platform.</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>'''    

    def _format_highlights(self, highlights) -> str:
        """Format key highlights as HTML."""
        if not highlights:
            return ""
        
        html = '<div class="highlights"><h3>Key Highlights</h3><ul>'
        for highlight in highlights:
            html += f'<li>{highlight}</li>'
        html += '</ul></div>'
        return html
    
    def _format_experience(self, experience) -> str:
        """Format experience entries as HTML."""
        if not experience:
            return '<div class="timeline-item"><p>No experience data available.</p></div>'
        
        html = ""
        for exp in experience:
            company = exp.get('company', 'Company')
            position = exp.get('position', 'Position')
            duration = exp.get('duration', f"{exp.get('start_date', '')} - {exp.get('end_date', '')}")
            description = exp.get('enhanced_description', exp.get('description', ''))
            achievements = exp.get('key_achievements', exp.get('achievements', []))
            
            html += f'''
            <div class="timeline-item">
                <div class="timeline-marker"></div>
                <div class="timeline-content">
                    <h3>{position}</h3>
                    <h4>{company}</h4>
                    <span class="timeline-date">{duration}</span>
                    <p>{description}</p>
                    {self._format_achievements(achievements)}
                </div>
            </div>'''
        
        return html
    
    def _format_achievements(self, achievements) -> str:
        """Format achievements as HTML."""
        if not achievements:
            return ""
        
        html = '<ul class="achievements">'
        for achievement in achievements[:3]:  # Limit to top 3
            html += f'<li>{achievement}</li>'
        html += '</ul>'
        return html
    
    def _format_skills(self, skills) -> str:
        """Format skills as HTML."""
        if not skills or not skills.get('skill_categories'):
            return '<div class="skill-category"><p>No skills data available.</p></div>'
        
        html = ""
        categories = skills.get('skill_categories', {})
        
        for category_name, category_data in categories.items():
            if isinstance(category_data, dict):
                skills_list = category_data.get('skills', [])
                proficiency = category_data.get('proficiency', 'Intermediate')
            else:
                skills_list = category_data if isinstance(category_data, list) else []
                proficiency = 'Intermediate'
            
            html += f'''
            <div class="skill-category">
                <h3>{category_name}</h3>
                <div class="skill-items">
                    {self._format_skill_items(skills_list)}
                </div>
                <div class="proficiency">{proficiency}</div>
            </div>'''
        
        return html
    
    def _format_skill_items(self, skills_list) -> str:
        """Format individual skill items."""
        if not skills_list:
            return ""
        
        html = ""
        for skill in skills_list[:6]:  # Limit to 6 skills per category
            html += f'<span class="skill-tag">{skill}</span>'
        
        return html
    
    def _format_education(self, education) -> str:
        """Format education entries as HTML."""
        if not education:
            return '<div class="education-item"><p>No education data available.</p></div>'
        
        html = ""
        for edu in education:
            institution = edu.get('institution', 'Institution')
            degree = edu.get('degree', 'Degree')
            field = edu.get('field', edu.get('field_of_study', ''))
            duration = edu.get('duration', f"{edu.get('start_date', '')} - {edu.get('end_date', '')}")
            details = edu.get('details', [])
            
            html += f'''
            <div class="education-item">
                <h3>{degree}</h3>
                <h4>{institution}</h4>
                {f'<p class="field">{field}</p>' if field else ''}
                <span class="education-date">{duration}</span>
                {self._format_education_details(details)}
            </div>'''
        
        return html
    
    def _format_education_details(self, details) -> str:
        """Format education details."""
        if not details:
            return ""
        
        html = '<ul class="education-details">'
        for detail in details:
            html += f'<li>{detail}</li>'
        html += '</ul>'
        return html
    
    def _format_contact(self, contact, personal_info) -> str:
        """Format contact information as HTML."""
        email = contact.get('email') or personal_info.email
        phone = contact.get('phone') or personal_info.phone
        location = contact.get('location') or personal_info.location
        linkedin = contact.get('linkedin') or personal_info.linkedin
        github = contact.get('github') or personal_info.github
        website = contact.get('website') or personal_info.website
        cta = contact.get('call_to_action', 'Feel free to reach out for opportunities or collaborations!')
        
        html = f'<p class="contact-cta">{cta}</p><div class="contact-details">'
        
        if email:
            html += f'<div class="contact-item"><i class="fas fa-envelope"></i><a href="mailto:{email}">{email}</a></div>'
        
        if phone:
            html += f'<div class="contact-item"><i class="fas fa-phone"></i><a href="tel:{phone}">{phone}</a></div>'
        
        if location:
            html += f'<div class="contact-item"><i class="fas fa-map-marker-alt"></i><span>{location}</span></div>'
        
        if linkedin:
            linkedin_url = linkedin if linkedin.startswith('http') else f'https://{linkedin}'
            html += f'<div class="contact-item"><i class="fab fa-linkedin"></i><a href="{linkedin_url}" target="_blank">LinkedIn</a></div>'
        
        if github:
            github_url = github if github.startswith('http') else f'https://{github}'
            html += f'<div class="contact-item"><i class="fab fa-github"></i><a href="{github_url}" target="_blank">GitHub</a></div>'
        
        if website:
            website_url = website if website.startswith('http') else f'https://{website}'
            html += f'<div class="contact-item"><i class="fas fa-globe"></i><a href="{website_url}" target="_blank">Website</a></div>'
        
        html += '</div>'
        return html    
    
def _generate_css_styles(self) -> str:
        """Generate CSS styles for the portfolio."""
        return '''/* Portfolio CSS Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #fff;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Navigation */
.navbar {
    position: fixed;
    top: 0;
    width: 100%;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    z-index: 1000;
    padding: 1rem 0;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.nav-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-logo {
    font-size: 1.5rem;
    font-weight: 700;
    color: #2563eb;
}

.nav-menu {
    display: flex;
    list-style: none;
    gap: 2rem;
}

.nav-link {
    text-decoration: none;
    color: #333;
    font-weight: 500;
    transition: color 0.3s ease;
}

.nav-link:hover {
    color: #2563eb;
}

/* Hero Section */
.hero {
    min-height: 100vh;
    display: flex;
    align-items: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-align: center;
}

.hero-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

.hero-title {
    font-size: 3.5rem;
    font-weight: 700;
    margin-bottom: 1rem;
    animation: fadeInUp 1s ease;
}

.hero-subtitle {
    font-size: 1.5rem;
    margin-bottom: 1rem;
    opacity: 0.9;
    animation: fadeInUp 1s ease 0.2s both;
}

.hero-description {
    font-size: 1.1rem;
    margin-bottom: 2rem;
    opacity: 0.8;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
    animation: fadeInUp 1s ease 0.4s both;
}

.hero-buttons {
    display: flex;
    gap: 1rem;
    justify-content: center;
    animation: fadeInUp 1s ease 0.6s both;
}

/* Buttons */
.btn {
    display: inline-block;
    padding: 12px 30px;
    border-radius: 50px;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.3s ease;
    border: 2px solid transparent;
}

.btn-primary {
    background: #2563eb;
    color: white;
    border-color: #2563eb;
}

.btn-primary:hover {
    background: transparent;
    color: #2563eb;
    border-color: #2563eb;
}

.btn-secondary {
    background: transparent;
    color: white;
    border-color: white;
}

.btn-secondary:hover {
    background: white;
    color: #2563eb;
}

/* Sections */
section {
    padding: 80px 0;
}

.section-title {
    font-size: 2.5rem;
    text-align: center;
    margin-bottom: 3rem;
    color: #2563eb;
}

/* About Section */
.about {
    background: #f8fafc;
}

.about-text {
    max-width: 800px;
    margin: 0 auto;
    font-size: 1.1rem;
    line-height: 1.8;
}

.highlights {
    margin-top: 2rem;
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.highlights h3 {
    color: #2563eb;
    margin-bottom: 1rem;
}

.highlights ul {
    list-style: none;
}

.highlights li {
    padding: 0.5rem 0;
    position: relative;
    padding-left: 1.5rem;
}

.highlights li:before {
    content: "✓";
    position: absolute;
    left: 0;
    color: #10b981;
    font-weight: bold;
}

/* Experience Section */
.timeline {
    position: relative;
    max-width: 800px;
    margin: 0 auto;
}

.timeline:before {
    content: '';
    position: absolute;
    left: 50%;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #2563eb;
    transform: translateX(-50%);
}

.timeline-item {
    position: relative;
    margin-bottom: 3rem;
    width: 50%;
}

.timeline-item:nth-child(odd) {
    left: 0;
    padding-right: 2rem;
}

.timeline-item:nth-child(even) {
    left: 50%;
    padding-left: 2rem;
}

.timeline-marker {
    position: absolute;
    width: 16px;
    height: 16px;
    background: #2563eb;
    border-radius: 50%;
    top: 0;
}

.timeline-item:nth-child(odd) .timeline-marker {
    right: -8px;
}

.timeline-item:nth-child(even) .timeline-marker {
    left: -8px;
}

.timeline-content {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.timeline-content h3 {
    color: #2563eb;
    margin-bottom: 0.5rem;
}

.timeline-content h4 {
    color: #64748b;
    margin-bottom: 0.5rem;
}

.timeline-date {
    color: #94a3b8;
    font-size: 0.9rem;
    font-weight: 500;
}

.achievements {
    margin-top: 1rem;
    list-style: none;
}

.achievements li {
    padding: 0.25rem 0;
    position: relative;
    padding-left: 1.5rem;
}

.achievements li:before {
    content: "→";
    position: absolute;
    left: 0;
    color: #2563eb;
}

/* Skills Section */
.skills {
    background: #f8fafc;
}

.skills-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    max-width: 1000px;
    margin: 0 auto;
}

.skill-category {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    text-align: center;
}

.skill-category h3 {
    color: #2563eb;
    margin-bottom: 1rem;
}

.skill-items {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    justify-content: center;
    margin-bottom: 1rem;
}

.skill-tag {
    background: #e0e7ff;
    color: #3730a3;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 500;
}

.proficiency {
    color: #64748b;
    font-weight: 500;
}

/* Education Section */
.education-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 2rem;
    max-width: 1000px;
    margin: 0 auto;
}

.education-item {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.education-item h3 {
    color: #2563eb;
    margin-bottom: 0.5rem;
}

.education-item h4 {
    color: #64748b;
    margin-bottom: 0.5rem;
}

.field {
    font-style: italic;
    color: #64748b;
    margin-bottom: 0.5rem;
}

.education-date {
    color: #94a3b8;
    font-size: 0.9rem;
    font-weight: 500;
}

.education-details {
    margin-top: 1rem;
    list-style: none;
}

.education-details li {
    padding: 0.25rem 0;
    color: #64748b;
}

/* Contact Section */
.contact {
    background: #1e293b;
    color: white;
}

.contact .section-title {
    color: white;
}

.contact-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4rem;
    max-width: 1000px;
    margin: 0 auto;
}

.contact-cta {
    font-size: 1.1rem;
    margin-bottom: 2rem;
    opacity: 0.9;
}

.contact-details {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.contact-item {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.contact-item i {
    width: 20px;
    color: #3b82f6;
}

.contact-item a {
    color: white;
    text-decoration: none;
    transition: color 0.3s ease;
}

.contact-item a:hover {
    color: #3b82f6;
}

/* Contact Form */
.contact-form {
    background: rgba(255, 255, 255, 0.1);
    padding: 2rem;
    border-radius: 10px;
}

.form-group {
    margin-bottom: 1.5rem;
}

.form-group input,
.form-group textarea {
    width: 100%;
    padding: 1rem;
    border: none;
    border-radius: 5px;
    background: rgba(255, 255, 255, 0.1);
    color: white;
    font-size: 1rem;
}

.form-group input::placeholder,
.form-group textarea::placeholder {
    color: rgba(255, 255, 255, 0.7);
}

/* Footer */
.footer {
    background: #0f172a;
    color: white;
    text-align: center;
    padding: 2rem 0;
}

/* Animations */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Responsive Design */
@media (max-width: 768px) {
    .hero-title {
        font-size: 2.5rem;
    }
    
    .hero-buttons {
        flex-direction: column;
        align-items: center;
    }
    
    .timeline:before {
        left: 20px;
    }
    
    .timeline-item {
        width: 100%;
        left: 0 !important;
        padding-left: 3rem !important;
        padding-right: 0 !important;
    }
    
    .timeline-marker {
        left: 12px !important;
    }
    
    .contact-content {
        grid-template-columns: 1fr;
        gap: 2rem;
    }
    
    .nav-menu {
        display: none;
    }
}'''
    
    def _generate_javascript(self) -> str:
        """Generate JavaScript for the portfolio."""
        return '''// Portfolio JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for navigation links
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Mobile menu toggle
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function() {
            hamburger.classList.toggle('active');
            navMenu.classList.toggle('active');
        });
    }

    // Contact form handling
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const name = formData.get('name');
            const email = formData.get('email');
            const message = formData.get('message');
            
            // Simple validation
            if (!name || !email || !message) {
                alert('Please fill in all fields.');
                return;
            }
            
            // Simulate form submission
            alert('Thank you for your message! This is a demo portfolio - in a real implementation, this would send your message.');
            
            // Reset form
            this.reset();
        });
    }

    // Scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe sections for animations
    const sections = document.querySelectorAll('section');
    sections.forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(20px)';
        section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(section);
    });

    // Active navigation highlighting
    window.addEventListener('scroll', function() {
        const sections = document.querySelectorAll('section');
        const navLinks = document.querySelectorAll('.nav-link');
        
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (scrollY >= (sectionTop - 200)) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + current) {
                link.classList.add('active');
            }
        });
    });

    // Typing effect for hero title (optional enhancement)
    const heroTitle = document.querySelector('.hero-title');
    if (heroTitle) {
        const originalText = heroTitle.textContent;
        heroTitle.textContent = '';
        
        let i = 0;
        const typeWriter = function() {
            if (i < originalText.length) {
                heroTitle.textContent += originalText.charAt(i);
                i++;
                setTimeout(typeWriter, 50);
            }
        };
        
        // Start typing effect after a short delay
        setTimeout(typeWriter, 1000);
    }
});

// Add CSS for active nav links
const style = document.createElement('style');
style.textContent = `
    .nav-link.active {
        color: #2563eb !important;
    }
    
    .hamburger {
        display: none;
        flex-direction: column;
        cursor: pointer;
    }
    
    .bar {
        width: 25px;
        height: 3px;
        background-color: #333;
        margin: 3px 0;
        transition: 0.3s;
    }
    
    @media (max-width: 768px) {
        .hamburger {
            display: flex;
        }
        
        .nav-menu {
            position: fixed;
            left: -100%;
            top: 70px;
            flex-direction: column;
            background-color: white;
            width: 100%;
            text-align: center;
            transition: 0.3s;
            box-shadow: 0 10px 27px rgba(0, 0, 0, 0.05);
            padding: 2rem 0;
        }
        
        .nav-menu.active {
            left: 0;
        }
        
        .nav-menu li {
            margin: 1rem 0;
        }
        
        .hamburger.active .bar:nth-child(2) {
            opacity: 0;
        }
        
        .hamburger.active .bar:nth-child(1) {
            transform: translateY(8px) rotate(45deg);
        }
        
        .hamburger.active .bar:nth-child(3) {
            transform: translateY(-8px) rotate(-45deg);
        }
    }
`;
document.head.appendChild(style);'''   
 
    def _generate_readme(self, name: str) -> str:
        """Generate README file for the portfolio."""
        return f'''# {name} - AI-Generated Portfolio

This portfolio was automatically generated by the Koroh AI Platform using AWS Bedrock for content generation.

## Features

- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Modern UI**: Clean, professional design with smooth animations
- **Interactive Elements**: Smooth scrolling navigation, contact form, mobile menu
- **AI-Generated Content**: All content was generated using AWS Bedrock based on CV analysis

## Files

- `index.html` - Main portfolio page
- `styles.css` - CSS styles and responsive design
- `script.js` - JavaScript for interactivity and animations
- `README.md` - This file

## How to View

1. Open `index.html` in any modern web browser
2. For best experience, use Chrome, Firefox, Safari, or Edge
3. The portfolio is fully responsive and works on mobile devices

## Local Development

To serve the portfolio locally with live reload:

```bash
# Using Python 3
python -m http.server 8000

# Using Node.js (if you have http-server installed)
npx http-server

# Using PHP
php -S localhost:8000
```

Then open http://localhost:8000 in your browser.

## Customization

The portfolio can be customized by editing:

- **Content**: Modify the HTML in `index.html`
- **Styling**: Update colors, fonts, and layout in `styles.css`
- **Functionality**: Add new features in `script.js`

## AI Generation Details

This portfolio was generated using:
- **CV Analysis**: AWS Bedrock Claude 3 Sonnet for extracting structured data from CV
- **Content Generation**: AWS Bedrock for creating professional portfolio content
- **Template**: Professional template with modern design
- **Style**: Formal tone optimized for recruiters

## Browser Compatibility

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## Performance

- Optimized images and assets
- Minimal JavaScript for fast loading
- CSS animations for smooth user experience
- Mobile-first responsive design

---

Generated by Koroh AI Platform - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
'''    

    def _get_fallback_cv_text(self) -> str:
        """Get fallback CV text for testing when PDF is not available."""
        return """
ALEX CHEN
Senior Full-Stack Developer
Email: alex.chen@email.com
Phone: +1-555-123-4567
Location: San Francisco, CA
LinkedIn: linkedin.com/in/alexchen
GitHub: github.com/alexchen
Website: alexchen.dev

PROFESSIONAL SUMMARY
Experienced full-stack developer with 7+ years of expertise in building scalable web applications. 
Specialized in React, Node.js, Python, and cloud technologies. Proven track record of leading 
development teams and delivering high-quality software solutions for startups and enterprise clients.

TECHNICAL SKILLS
Programming Languages: JavaScript, TypeScript, Python, Java, Go
Frontend: React, Vue.js, Angular, HTML5, CSS3, Sass, Tailwind CSS
Backend: Node.js, Express.js, Django, Flask, Spring Boot
Databases: PostgreSQL, MongoDB, Redis, MySQL
Cloud & DevOps: AWS, Docker, Kubernetes, Jenkins, GitHub Actions
Tools: Git, Webpack, Vite, Jest, Cypress, Figma

SOFT SKILLS
Leadership, Team Collaboration, Problem Solving, Agile Methodologies, Code Review, Mentoring

WORK EXPERIENCE

Senior Full-Stack Developer | TechCorp Inc. | Jan 2021 - Present
• Led development of microservices architecture serving 500K+ daily active users
• Implemented CI/CD pipelines reducing deployment time by 60%
• Mentored 5 junior developers and conducted technical interviews
• Built real-time analytics dashboard using React and WebSocket connections
• Technologies: React, Node.js, PostgreSQL, AWS, Docker, Kubernetes

Full-Stack Developer | StartupXYZ | Jun 2019 - Dec 2020
• Developed MVP for fintech application from concept to production
• Integrated payment processing systems handling $2M+ in transactions
• Optimized database queries improving application performance by 40%
• Collaborated with design team to implement responsive UI/UX
• Technologies: Vue.js, Django, PostgreSQL, Stripe API, AWS

Software Developer | WebSolutions Ltd. | Aug 2017 - May 2019
• Built e-commerce platforms for 20+ clients using modern web technologies
• Implemented automated testing suites achieving 90% code coverage
• Participated in agile development processes and sprint planning
• Created RESTful APIs and integrated third-party services
• Technologies: JavaScript, PHP, MySQL, jQuery, Bootstrap

EDUCATION

Master of Science in Computer Science | Stanford University | 2015 - 2017
• GPA: 3.8/4.0
• Thesis: "Scalable Web Application Architecture for Real-time Data Processing"
• Relevant Coursework: Algorithms, Database Systems, Software Engineering, Machine Learning

Bachelor of Science in Computer Science | UC Berkeley | 2011 - 2015
• GPA: 3.6/4.0
• Magna Cum Laude
• Relevant Coursework: Data Structures, Operating Systems, Computer Networks

CERTIFICATIONS
• AWS Certified Solutions Architect - Professional | Amazon Web Services | 2022
• Certified Kubernetes Administrator | Cloud Native Computing Foundation | 2021
• Google Cloud Professional Developer | Google Cloud | 2020

PROJECTS

E-Commerce Platform | 2023
• Built full-stack e-commerce solution with React and Node.js
• Implemented real-time inventory management and order processing
• Deployed on AWS with auto-scaling and load balancing
• URL: github.com/alexchen/ecommerce-platform

Real-Time Chat Application | 2022
• Developed WebSocket-based chat application with React and Socket.io
• Implemented user authentication and message encryption
• Supports file sharing and group conversations
• URL: github.com/alexchen/realtime-chat

Open Source Contributions | 2020-Present
• Contributed to React Router, Express.js, and Django REST Framework
• Maintained personal open source libraries with 1000+ GitHub stars
• Active participant in developer community and tech meetups

LANGUAGES
• English: Native
• Mandarin: Native
• Spanish: Intermediate

AWARDS & RECOGNITION
• Employee of the Year - TechCorp Inc. (2023)
• Best Innovation Award - StartupXYZ (2020)
• Dean's List - Stanford University (2016, 2017)

INTERESTS
Photography, Rock Climbing, Open Source Development, AI/Machine Learning, Cooking
"""
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all AI integration tests."""
        print("🚀 KOROH AI SERVICE INTEGRATION TEST SUITE")
        print("=" * 80)
        print("Testing real AWS Bedrock integration with CV analysis and portfolio generation")
        print("=" * 80)
        
        tests = [
            ("CV Analysis Accuracy", self.test_cv_analysis_accuracy),
            ("Portfolio Generation Quality", self.test_portfolio_generation_quality),
            ("HTML Portfolio Generation", self.generate_html_portfolio),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                print(f"\n🧪 Running: {test_name}")
                results[test_name] = test_func()
                status = "✅ PASSED" if results[test_name] else "❌ FAILED"
                print(f"Result: {status}")
            except Exception as e:
                print(f"❌ {test_name} crashed: {e}")
                logger.exception(f"{test_name} test error")
                results[test_name] = False
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("🎯 TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
            print("✨ AI Service Integration is working perfectly!")
            print("\n📁 Generated Files:")
            print(f"  • CV Analysis: {TEST_OUTPUT_DIR}/cv_analysis_results.json")
            print(f"  • Portfolio Content: {TEST_OUTPUT_DIR}/portfolio_content.json")
            print(f"  • HTML Portfolio: {TEST_OUTPUT_DIR}/portfolio_website/")
            print(f"\n🌐 To view the generated portfolio:")
            print(f"  Open {TEST_OUTPUT_DIR}/portfolio_website/index.html in your browser")
        else:
            print(f"\n⚠️ {total - passed} test(s) failed.")
            print("Please check AWS credentials and Bedrock configuration.")
        
        return passed == total


def main():
    """Main test execution."""
    test_suite = AIIntegrationTestSuite()
    results = test_suite.run_all_tests()
    success = test_suite.print_summary(results)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())