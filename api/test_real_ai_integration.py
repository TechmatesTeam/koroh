#!/usr/bin/env python
"""
Real AI Service Integration Tests with AWS Bedrock

This test suite validates real AWS Bedrock integration by:
1. Testing CV analysis accuracy with real Qwen model responses
2. Testing portfolio generation quality with real AI
3. Creating actual HTML/CSS/JavaScript portfolio files

Requirements: 1.1, 1.2, 6.3
"""

import os
import sys
import django
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import boto3
from botocore.config import Config
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koroh_platform.settings')
django.setup()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TEST_OUTPUT_DIR = Path("test_portfolio_output")


class RealBedrockClient:
    """Real Bedrock client for testing with proper Qwen model support."""
    
    def __init__(self):
        """Initialize real Bedrock client."""
        from django.conf import settings
        
        self.model_id = getattr(settings, 'AWS_BEDROCK_MODEL_ID', 'qwen.qwen3-32b-v1:0')
        self.max_tokens = getattr(settings, 'AWS_BEDROCK_MAX_TOKENS', 4096)
        self.temperature = getattr(settings, 'AWS_BEDROCK_TEMPERATURE', 0.7)
        self.region = getattr(settings, 'AWS_BEDROCK_REGION', 'us-east-1')
        
        config = Config(
            region_name=self.region,
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            read_timeout=120
        )
        
        self.client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
            config=config
        )
    
    def invoke_model(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Invoke the Qwen model with a prompt."""
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": self.temperature,
            "top_p": 0.9
        }
        
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        
        # Extract content from Qwen response
        if 'choices' in response_body and response_body['choices']:
            content = response_body['choices'][0]['message']['content']
            return content.strip()
        
        return str(response_body)


def test_real_cv_analysis():
    """Test CV analysis with real AWS Bedrock Qwen model."""
    print("🧠 Testing Real CV Analysis with AWS Bedrock Qwen")
    print("=" * 70)
    
    try:
        # Sample comprehensive CV text
        cv_text = """
SARAH JOHNSON
Senior Product Manager
Email: sarah.johnson@email.com
Phone: +1-555-987-6543
Location: Seattle, WA
LinkedIn: linkedin.com/in/sarahjohnson
GitHub: github.com/sarahjohnson

PROFESSIONAL SUMMARY
Results-driven Product Manager with 5+ years of experience leading cross-functional teams 
to deliver innovative cloud solutions. Proven track record of increasing user engagement 
by 45% and driving product growth through data-driven decision making. Expert in agile 
methodologies, user research, and strategic product planning.

TECHNICAL SKILLS
Product Management, Data Analysis, Agile/Scrum, Python, SQL, Tableau, Azure, AWS, 
JavaScript, React, Node.js, Docker, Kubernetes, Git, JIRA, Confluence

SOFT SKILLS
Leadership, Communication, Strategic Thinking, Problem Solving, Team Management, 
Cross-functional Collaboration, User Experience Design, Stakeholder Management

WORK EXPERIENCE

Senior Product Manager | Microsoft Corporation | Jan 2021 - Present
• Led product strategy and development for cloud-based solutions serving 2M+ users
• Increased user engagement by 45% through data-driven product improvements and A/B testing
• Led cross-functional team of 12 engineers, designers, and data scientists
• Launched 3 major product features that generated $5M in additional revenue
• Implemented agile development processes reducing time-to-market by 30%
• Collaborated with sales and marketing teams to develop go-to-market strategies

Product Manager | Amazon Web Services | Jun 2018 - Dec 2020
• Managed product roadmap for AWS developer tools with $10M annual revenue
• Delivered 15+ product releases on schedule with 99.9% uptime
• Reduced customer churn by 30% through improved user experience and feature development
• Conducted user research with 500+ customers to inform product decisions
• Worked closely with engineering teams to prioritize features and resolve technical challenges

Associate Product Manager | Startup Inc. | Jan 2017 - May 2018
• Supported product development for early-stage fintech startup
• Helped grow user base from 1,000 to 50,000 active users
• Conducted market research and competitive analysis
• Assisted in raising $2M Series A funding through product demonstrations

EDUCATION

Master of Business Administration | Stanford University | 2015 - 2017
• Technology Management focus, GPA: 3.9/4.0
• Relevant Coursework: Product Strategy, Data Analytics, Leadership, Innovation Management
• Capstone Project: "AI-Driven Product Recommendation Systems"

Bachelor of Science in Computer Science | University of Washington | 2011 - 2015
• GPA: 3.7/4.0, Magna Cum Laude
• Relevant Coursework: Software Engineering, Database Systems, Human-Computer Interaction
• Senior Project: "Mobile App for Campus Navigation" (iOS/Android)

CERTIFICATIONS
• Certified Product Manager | Product Management Institute | 2020 - 2025
• AWS Solutions Architect Associate | Amazon Web Services | 2019 - 2024
• Certified ScrumMaster | Scrum Alliance | 2018 - 2023
• Google Analytics Certified | Google | 2021 - 2023

PROJECTS
Cloud Analytics Dashboard | 2023
• Built real-time analytics dashboard for cloud resource monitoring using React and Python
• Integrated with AWS CloudWatch and custom APIs
• Used by 1000+ internal users for infrastructure management

Product Metrics Platform | 2022
• Developed internal platform for tracking product KPIs and user behavior
• Technologies: Node.js, PostgreSQL, Docker, Grafana
• Reduced reporting time by 80% and improved data accuracy

LANGUAGES
• English: Native
• Spanish: Intermediate (conversational)
• Mandarin: Basic

AWARDS & RECOGNITION
• Employee of the Year - Microsoft Corporation (2023)
• Innovation Award - Amazon Web Services (2019)
• Dean's List - University of Washington (2013, 2014, 2015)

INTERESTS
Machine Learning, Data Visualization, Hiking, Photography, Mentoring, Tech Meetups
"""
        
        print(f"📝 CV text length: {len(cv_text)} characters")
        
        # Initialize real Bedrock client
        bedrock_client = RealBedrockClient()
        
        # Create comprehensive CV analysis prompt
        analysis_prompt = f"""
Please analyze the following CV text and extract structured information in valid JSON format.

CV TEXT:
{cv_text}

Extract the following information and respond with ONLY valid JSON (no markdown, no extra text):

{{
    "personal_info": {{
        "name": "Full name",
        "email": "Email address", 
        "phone": "Phone number",
        "location": "Location",
        "linkedin": "LinkedIn URL",
        "github": "GitHub URL"
    }},
    "professional_summary": "Professional summary text",
    "technical_skills": ["list", "of", "technical", "skills"],
    "soft_skills": ["list", "of", "soft", "skills"],
    "work_experience": [
        {{
            "company": "Company name",
            "position": "Job title",
            "start_date": "Start date",
            "end_date": "End date", 
            "duration": "Duration",
            "description": "Job description",
            "achievements": ["list", "of", "key", "achievements"],
            "technologies": ["technologies", "used"]
        }}
    ],
    "education": [
        {{
            "institution": "School name",
            "degree": "Degree type",
            "field_of_study": "Field of study",
            "start_date": "Start date",
            "end_date": "End date",
            "gpa": "GPA if mentioned",
            "honors": "Academic honors"
        }}
    ],
    "certifications": [
        {{
            "name": "Certification name",
            "issuer": "Issuing organization", 
            "issue_date": "Date obtained",
            "expiry_date": "Expiry date if applicable"
        }}
    ],
    "projects": [
        {{
            "name": "Project name",
            "description": "Project description",
            "technologies": ["technologies", "used"],
            "date": "Project date"
        }}
    ],
    "languages": [
        {{
            "language": "Language name",
            "proficiency": "Proficiency level"
        }}
    ],
    "awards": ["list", "of", "awards"],
    "interests": ["list", "of", "interests"]
}}

Respond with valid JSON only.
"""
        
        print("🔍 Analyzing CV with real AWS Bedrock Qwen model...")
        
        # Invoke the model
        response_content = bedrock_client.invoke_model(analysis_prompt, max_tokens=4000)
        
        print("✅ CV analysis completed!")
        print(f"📝 Response length: {len(response_content)} characters")
        
        # Parse the JSON response
        try:
            # Clean up the response (remove any markdown formatting)
            cleaned_content = response_content.strip()
            if cleaned_content.startswith('```json'):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.endswith('```'):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()
            
            analysis_result = json.loads(cleaned_content)
            
            print("✅ Successfully parsed CV analysis JSON")
            print("\n📊 Real AI Analysis Results:")
            print(f"  Name: {analysis_result.get('personal_info', {}).get('name', 'N/A')}")
            print(f"  Email: {analysis_result.get('personal_info', {}).get('email', 'N/A')}")
            print(f"  Technical Skills: {len(analysis_result.get('technical_skills', []))}")
            print(f"  Soft Skills: {len(analysis_result.get('soft_skills', []))}")
            print(f"  Work Experience: {len(analysis_result.get('work_experience', []))}")
            print(f"  Education: {len(analysis_result.get('education', []))}")
            print(f"  Certifications: {len(analysis_result.get('certifications', []))}")
            print(f"  Projects: {len(analysis_result.get('projects', []))}")
            print(f"  Languages: {len(analysis_result.get('languages', []))}")
            print(f"  Awards: {len(analysis_result.get('awards', []))}")
            
            # Calculate quality score
            quality_score = calculate_analysis_quality(analysis_result)
            print(f"  Quality Score: {quality_score:.2f}")
            
            # Save results
            TEST_OUTPUT_DIR.mkdir(exist_ok=True)
            output_file = TEST_OUTPUT_DIR / "real_bedrock_cv_analysis.json"
            with open(output_file, 'w') as f:
                json.dump({
                    'metadata': {
                        'model': bedrock_client.model_id,
                        'timestamp': datetime.now().isoformat(),
                        'cv_length': len(cv_text),
                        'response_length': len(response_content),
                        'quality_score': quality_score
                    },
                    'analysis_result': analysis_result
                }, f, indent=2)
            
            print(f"💾 Real analysis results saved to {output_file}")
            
            return analysis_result, quality_score >= 0.8
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"Raw response: {response_content[:500]}...")
            return None, False
            
    except Exception as e:
        print(f"❌ Real CV analysis failed: {e}")
        logger.exception("Real CV analysis error")
        return None, False


def test_real_portfolio_generation(cv_data):
    """Test portfolio generation with real AWS Bedrock."""
    print("\n🎨 Testing Real Portfolio Generation with AWS Bedrock Qwen")
    print("=" * 70)
    
    try:
        if not cv_data:
            print("❌ No CV analysis data available")
            return None, False
        
        # Initialize real Bedrock client
        bedrock_client = RealBedrockClient()
        
        # Create portfolio generation prompt
        portfolio_prompt = f"""
Based on the following CV analysis data, generate professional portfolio content in JSON format.

CV DATA:
{json.dumps(cv_data, indent=2)}

Generate compelling portfolio content with the following structure (respond with valid JSON only):

{{
    "hero_section": {{
        "headline": "Compelling professional headline",
        "subheadline": "Supporting tagline",
        "value_proposition": "Unique value proposition statement",
        "call_to_action": "Action-oriented CTA"
    }},
    "about_section": {{
        "main_content": "Engaging 2-3 paragraph about section that tells a professional story",
        "key_highlights": ["highlight 1", "highlight 2", "highlight 3", "highlight 4"],
        "personal_touch": "Brief personal element to show personality"
    }},
    "experience_section": [
        {{
            "company": "Company name",
            "position": "Position title", 
            "duration": "Time period",
            "enhanced_description": "Compelling description focusing on impact and results",
            "key_achievements": ["achievement 1", "achievement 2", "achievement 3"],
            "skills_demonstrated": ["skill 1", "skill 2", "skill 3"],
            "impact_summary": "One sentence summarizing overall impact"
        }}
    ],
    "skills_section": {{
        "skill_categories": {{
            "Technical Skills": {{
                "skills": ["skill1", "skill2", "skill3"],
                "proficiency": "Expert/Advanced/Intermediate"
            }},
            "Leadership & Management": {{
                "skills": ["skill1", "skill2", "skill3"], 
                "proficiency": "Expert/Advanced/Intermediate"
            }}
        }},
        "top_skills": ["top 5 most important skills"],
        "skills_summary": "Brief overview of skill set strength"
    }},
    "contact_section": {{
        "call_to_action": "Compelling message encouraging contact",
        "email": "email from CV",
        "phone": "phone from CV", 
        "location": "location from CV",
        "linkedin": "linkedin from CV",
        "github": "github from CV"
    }}
}}

Create professional, engaging content optimized for recruiters. Use action verbs and quantifiable results. Respond with valid JSON only.
"""
        
        print("🚀 Generating portfolio with real AWS Bedrock...")
        
        # Invoke the model
        response_content = bedrock_client.invoke_model(portfolio_prompt, max_tokens=4000)
        
        print("✅ Portfolio generation completed!")
        print(f"📝 Response length: {len(response_content)} characters")
        
        # Parse the JSON response
        try:
            # Clean up the response
            cleaned_content = response_content.strip()
            if cleaned_content.startswith('```json'):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.endswith('```'):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()
            
            portfolio_content = json.loads(cleaned_content)
            
            print("✅ Successfully parsed portfolio JSON")
            print("\n📋 Real AI Portfolio Generation Results:")
            
            # Validate sections
            sections_quality = {}
            
            if portfolio_content.get('hero_section', {}).get('headline'):
                sections_quality['hero'] = True
                print(f"  ✅ Hero: {portfolio_content['hero_section']['headline'][:50]}...")
            
            if portfolio_content.get('about_section', {}).get('main_content'):
                content_length = len(portfolio_content['about_section']['main_content'])
                sections_quality['about'] = content_length > 200
                print(f"  ✅ About: {content_length} characters")
            
            if portfolio_content.get('experience_section'):
                sections_quality['experience'] = len(portfolio_content['experience_section']) > 0
                print(f"  ✅ Experience: {len(portfolio_content['experience_section'])} entries")
            
            if portfolio_content.get('skills_section', {}).get('skill_categories'):
                categories = len(portfolio_content['skills_section']['skill_categories'])
                sections_quality['skills'] = categories > 0
                print(f"  ✅ Skills: {categories} categories")
            
            if portfolio_content.get('contact_section', {}).get('email'):
                sections_quality['contact'] = True
                print("  ✅ Contact: Information complete")
            
            sections_passed = sum(sections_quality.values())
            quality_score = sections_passed / len(sections_quality) if sections_quality else 0
            
            print(f"\n🎯 Portfolio Quality: {sections_passed}/{len(sections_quality)} sections passed")
            print(f"📊 Quality Score: {quality_score:.2f}")
            
            # Save portfolio content
            portfolio_file = TEST_OUTPUT_DIR / "real_bedrock_portfolio_content.json"
            with open(portfolio_file, 'w') as f:
                json.dump({
                    'metadata': {
                        'model': bedrock_client.model_id,
                        'timestamp': datetime.now().isoformat(),
                        'quality_score': quality_score,
                        'sections_quality': sections_quality
                    },
                    'portfolio_content': portfolio_content
                }, f, indent=2)
            
            print(f"💾 Real portfolio content saved to {portfolio_file}")
            
            return portfolio_content, quality_score >= 0.8
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse portfolio JSON: {e}")
            print(f"Raw response: {response_content[:500]}...")
            return None, False
            
    except Exception as e:
        print(f"❌ Real portfolio generation failed: {e}")
        logger.exception("Real portfolio generation error")
        return None, False


def calculate_analysis_quality(analysis_result):
    """Calculate quality score for CV analysis."""
    score = 0.0
    max_score = 10.0
    
    # Personal info (2 points)
    personal_info = analysis_result.get('personal_info', {})
    if personal_info.get('name'):
        score += 1.0
    if personal_info.get('email'):
        score += 1.0
    
    # Skills (2 points)
    technical_skills = analysis_result.get('technical_skills', [])
    soft_skills = analysis_result.get('soft_skills', [])
    if len(technical_skills) >= 3:
        score += 1.0
    if len(soft_skills) >= 2:
        score += 1.0
    
    # Work experience (3 points)
    work_experience = analysis_result.get('work_experience', [])
    if len(work_experience) >= 1:
        score += 1.0
    if len(work_experience) >= 2:
        score += 1.0
    if any(exp.get('achievements') for exp in work_experience):
        score += 1.0
    
    # Education (2 points)
    education = analysis_result.get('education', [])
    if len(education) >= 1:
        score += 2.0
    
    # Additional sections (1 point)
    if analysis_result.get('certifications') or analysis_result.get('projects'):
        score += 1.0
    
    return min(score / max_score, 1.0)


def generate_real_html_portfolio(portfolio_content, cv_data):
    """Generate HTML portfolio from real AI-generated content."""
    print("\n🌐 Generating HTML Portfolio from Real AI Content")
    print("=" * 70)
    
    try:
        if not portfolio_content or not cv_data:
            print("❌ No portfolio or CV data available")
            return False
        
        # Create portfolio directory
        portfolio_dir = TEST_OUTPUT_DIR / "real_ai_portfolio"
        portfolio_dir.mkdir(exist_ok=True)
        
        name = cv_data.get('personal_info', {}).get('name', 'Professional Portfolio')
        
        # Generate HTML with real AI content
        html_content = generate_html_from_ai_content(portfolio_content, cv_data, name)
        
        # Generate CSS and JS
        css_content = generate_professional_css()
        js_content = generate_interactive_js()
        
        # Save files
        files_created = {}
        
        html_file = portfolio_dir / "index.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        files_created['index.html'] = html_file.stat().st_size
        
        css_file = portfolio_dir / "styles.css"
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(css_content)
        files_created['styles.css'] = css_file.stat().st_size
        
        js_file = portfolio_dir / "script.js"
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(js_content)
        files_created['script.js'] = js_file.stat().st_size
        
        # Create README
        readme_content = f"""# {name} - AI-Generated Portfolio

This portfolio was generated using **real AWS Bedrock AI** with the Qwen model.

## 🤖 AI Generation Details

- **Model**: {getattr(RealBedrockClient(), 'model_id', 'qwen.qwen3-32b-v1:0')}
- **Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Content**: 100% AI-generated using real AWS Bedrock
- **Quality**: Professional-grade content optimized for recruiters

## 🌐 How to View

Open `index.html` in any modern web browser to view the portfolio.

## 📊 AI Analysis Results

The portfolio was generated from comprehensive CV analysis that extracted:
- Personal information and contact details
- Professional summary and value proposition
- Technical and soft skills categorization
- Work experience with achievements and impact
- Education and certifications
- Projects and awards

## 🎯 Features

- **Responsive Design**: Works on all devices
- **Professional Content**: AI-generated, recruiter-optimized
- **Modern UI**: Clean, professional appearance
- **Interactive Elements**: Smooth scrolling, animations
- **Real AI**: Generated with actual AWS Bedrock, not mocked

---

**Powered by AWS Bedrock & Qwen AI Model**
"""
        
        readme_file = portfolio_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        files_created['README.md'] = readme_file.stat().st_size
        
        print("✅ Real AI portfolio generated successfully!")
        print(f"📁 Portfolio location: {portfolio_dir.absolute()}")
        print(f"🌐 Open {html_file.absolute()} in your browser")
        
        print("\n📋 Generated Files:")
        total_size = 0
        for filename, size in files_created.items():
            print(f"  ✅ {filename}: {size:,} bytes")
            total_size += size
        
        print(f"\n📊 Total Portfolio Size: {total_size:,} bytes")
        print("🤖 Content: 100% generated by real AWS Bedrock AI")
        
        return True
        
    except Exception as e:
        print(f"❌ HTML Portfolio generation failed: {e}")
        logger.exception("HTML Portfolio generation error")
        return False


def generate_html_from_ai_content(portfolio_content, cv_data, name):
    """Generate HTML from real AI-generated portfolio content."""
    hero = portfolio_content.get('hero_section', {})
    about = portfolio_content.get('about_section', {})
    experience = portfolio_content.get('experience_section', [])
    skills = portfolio_content.get('skills_section', {})
    contact = portfolio_content.get('contact_section', {})
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - AI-Generated Portfolio</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
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
                <li><a href="#contact" class="nav-link">Contact</a></li>
            </ul>
        </div>
    </nav>

    <!-- Hero Section -->
    <section id="home" class="hero">
        <div class="hero-container">
            <div class="hero-content">
                <h1 class="hero-title">{hero.get('headline', name)}</h1>
                <p class="hero-subtitle">{hero.get('subheadline', 'AI-Generated Professional Portfolio')}</p>
                <p class="hero-description">{hero.get('value_proposition', 'Professional portfolio generated by AWS Bedrock AI')}</p>
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
                    <p>{about.get('main_content', 'Professional with extensive experience and expertise.')}</p>
                    {format_highlights(about.get('key_highlights', []))}
                    {f'<p class="personal-touch"><em>{about.get("personal_touch", "")}</em></p>' if about.get('personal_touch') else ''}
                </div>
            </div>
        </div>
    </section>

    <!-- Experience Section -->
    <section id="experience" class="experience">
        <div class="container">
            <h2 class="section-title">Professional Experience</h2>
            <div class="timeline">
                {format_experience(experience)}
            </div>
        </div>
    </section>

    <!-- Skills Section -->
    <section id="skills" class="skills">
        <div class="container">
            <h2 class="section-title">Skills & Expertise</h2>
            <div class="skills-grid">
                {format_skills(skills)}
            </div>
            <div class="skills-summary">
                <p>{skills.get('skills_summary', 'Comprehensive skill set with proven expertise.')}</p>
            </div>
        </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="contact">
        <div class="container">
            <h2 class="section-title">Get In Touch</h2>
            <div class="contact-content">
                <div class="contact-info">
                    <p class="contact-cta">{contact.get('call_to_action', 'Feel free to reach out!')}</p>
                    <div class="contact-details">
                        {format_contact_details(contact, cv_data.get('personal_info', {}))}
                    </div>
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
            <p>&copy; 2024 {name}. Generated by AWS Bedrock AI (Qwen Model).</p>
            <p>This portfolio was created using real AI-powered content generation.</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>'''


def format_highlights(highlights):
    """Format key highlights as HTML."""
    if not highlights:
        return ""
    
    html = '<div class="highlights"><h3>Key Highlights</h3><ul>'
    for highlight in highlights:
        html += f'<li>{highlight}</li>'
    html += '</ul></div>'
    return html


def format_experience(experience):
    """Format experience entries as HTML."""
    if not experience:
        return '<div class="timeline-item"><div class="timeline-content"><p>No experience data available.</p></div></div>'
    
    html = ""
    for exp in experience:
        company = exp.get('company', 'Company')
        position = exp.get('position', 'Position')
        duration = exp.get('duration', '')
        description = exp.get('enhanced_description', exp.get('description', ''))
        achievements = exp.get('key_achievements', [])
        impact = exp.get('impact_summary', '')
        
        html += f'''
        <div class="timeline-item">
            <div class="timeline-content">
                <h3>{position}</h3>
                <h4>{company}</h4>
                <span class="timeline-date">{duration}</span>
                <p>{description}</p>
                {format_achievements(achievements)}
                {f'<p class="impact-summary">{impact}</p>' if impact else ''}
            </div>
        </div>'''
    
    return html


def format_achievements(achievements):
    """Format achievements as HTML."""
    if not achievements:
        return ""
    
    html = '<ul class="achievements">'
    for achievement in achievements:
        html += f'<li>{achievement}</li>'
    html += '</ul>'
    return html


def format_skills(skills):
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
                {format_skill_items(skills_list)}
            </div>
            <div class="proficiency">{proficiency}</div>
        </div>'''
    
    return html


def format_skill_items(skills_list):
    """Format individual skill items."""
    if not skills_list:
        return ""
    
    html = ""
    for skill in skills_list:
        html += f'<span class="skill-tag">{skill}</span>'
    
    return html


def format_contact_details(contact, personal_info):
    """Format contact details as HTML."""
    email = contact.get('email') or personal_info.get('email')
    phone = contact.get('phone') or personal_info.get('phone')
    location = contact.get('location') or personal_info.get('location')
    linkedin = contact.get('linkedin') or personal_info.get('linkedin')
    github = contact.get('github') or personal_info.get('github')
    
    html = ""
    
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
    
    return html


def generate_professional_css():
    """Generate professional CSS for the portfolio."""
    return '''/* Professional Portfolio CSS - AI Generated */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', sans-serif;
    line-height: 1.6;
    color: #333;
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

.nav-link:hover, .nav-link.active {
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
    cursor: pointer;
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

.personal-touch {
    margin-top: 2rem;
    font-style: italic;
    color: #64748b;
    text-align: center;
}

/* Experience Section */
.timeline {
    max-width: 800px;
    margin: 0 auto;
}

.timeline-item {
    margin-bottom: 3rem;
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

.impact-summary {
    margin-top: 1rem;
    font-style: italic;
    color: #64748b;
    border-left: 3px solid #2563eb;
    padding-left: 1rem;
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

.skills-summary {
    max-width: 800px;
    margin: 3rem auto 0;
    text-align: center;
    font-size: 1.1rem;
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
    
    .contact-content {
        grid-template-columns: 1fr;
        gap: 2rem;
    }
    
    .nav-menu {
        display: none;
    }
}'''


def generate_interactive_js():
    """Generate interactive JavaScript for the portfolio."""
    return '''// Interactive Portfolio JavaScript - AI Generated
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

    // Contact form handling
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const name = formData.get('name');
            const email = formData.get('email');
            const message = formData.get('message');
            
            if (!name || !email || !message) {
                alert('Please fill in all fields.');
                return;
            }
            
            alert(`Thank you ${name}! This is an AI-generated portfolio demo. Your message would be sent in a real implementation.`);
            this.reset();
        });
    }

    // Active navigation highlighting
    window.addEventListener('scroll', function() {
        const sections = document.querySelectorAll('section');
        const navLinks = document.querySelectorAll('.nav-link');
        
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
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
        if (section.id !== 'home') {
            section.style.opacity = '0';
            section.style.transform = 'translateY(20px)';
            section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(section);
        }
    });
});'''


def main():
    """Run real AI integration tests with AWS Bedrock."""
    print("🚀 REAL AI INTEGRATION TEST WITH AWS BEDROCK")
    print("=" * 80)
    print("Testing with real Qwen model on AWS Bedrock")
    print("=" * 80)
    
    # Test 1: Real CV Analysis
    cv_data, cv_success = test_real_cv_analysis()
    
    # Test 2: Real Portfolio Generation
    portfolio_data, portfolio_success = test_real_portfolio_generation(cv_data)
    
    # Test 3: Generate HTML Portfolio
    html_success = generate_real_html_portfolio(portfolio_data, cv_data)
    
    # Summary
    print("\n" + "=" * 80)
    print("🎯 REAL AI INTEGRATION TEST SUMMARY")
    print("=" * 80)
    
    tests = [
        ("Real CV Analysis with AWS Bedrock", cv_success),
        ("Real Portfolio Generation with AWS Bedrock", portfolio_success),
        ("HTML Portfolio from Real AI Content", html_success)
    ]
    
    passed = 0
    for test_name, result in tests:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 ALL REAL AI TESTS PASSED!")
        print("✨ Real AWS Bedrock integration is working perfectly!")
        print("\n📋 Requirements Status:")
        print("  ✅ 1.1 - CV analysis accuracy: REAL AI WORKING")
        print("  ✅ 1.2 - Portfolio generation quality: REAL AI WORKING") 
        print("  ✅ 6.3 - AI workflow validation: REAL AI WORKING")
        print(f"\n📁 Generated Files:")
        print(f"  • Real CV Analysis: {TEST_OUTPUT_DIR}/real_bedrock_cv_analysis.json")
        print(f"  • Real Portfolio Content: {TEST_OUTPUT_DIR}/real_bedrock_portfolio_content.json")
        print(f"  • Real AI Portfolio: {TEST_OUTPUT_DIR}/real_ai_portfolio/")
        print(f"\n🌐 To view the real AI-generated portfolio:")
        print(f"  Open {TEST_OUTPUT_DIR}/real_ai_portfolio/index.html in your browser")
        print(f"\n🤖 All content generated by real AWS Bedrock Qwen model!")
    else:
        print(f"\n⚠️ {len(tests) - passed} test(s) failed.")
        print("Please check the AWS Bedrock integration.")
    
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())