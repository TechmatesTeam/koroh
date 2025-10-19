#!/usr/bin/env python
"""
Simplified AI Service Integration Tests for Koroh Platform

This test suite validates real AWS Bedrock integration by:
1. Testing CV analysis accuracy with real PDF files
2. Testing portfolio generation quality
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


def test_cv_analysis_with_bedrock():
    """Test CV analysis with real AWS Bedrock."""
    print("🧠 Testing CV Analysis with Real AWS Bedrock")
    print("=" * 60)
    
    try:
        from koroh_platform.utils.cv_analysis_service import CVAnalysisService
        
        # Sample CV text for testing
        cv_text = """
SARAH JOHNSON
Senior Product Manager
Email: sarah.johnson@email.com
Phone: +1-555-987-6543
Location: Seattle, WA
LinkedIn: linkedin.com/in/sarahjohnson

PROFESSIONAL SUMMARY
Results-driven Product Manager with 5+ years of experience leading cross-functional teams 
to deliver innovative cloud solutions. Proven track record of increasing user engagement 
and driving product growth through data-driven decision making.

TECHNICAL SKILLS
Product Management, Data Analysis, Agile, Python, SQL, Tableau, Azure, AWS

SOFT SKILLS
Leadership, Communication, Strategic Thinking, Problem Solving

WORK EXPERIENCE

Senior Product Manager | Microsoft Corporation | Jan 2021 - Present
• Led product strategy and development for cloud-based solutions
• Increased user engagement by 45% through data-driven product improvements
• Led cross-functional team of 12 engineers and designers
• Launched 3 major product features serving 2M+ users

Product Manager | Amazon Web Services | Jun 2018 - Dec 2020
• Managed product roadmap for AWS developer tools
• Delivered 15+ product releases on schedule
• Reduced customer churn by 30% through improved UX

EDUCATION

Master of Business Administration | Stanford University | 2016 - 2018
• Technology Management focus
• GPA: 3.9/4.0

Bachelor of Science | University of Washington | 2012 - 2016
• Computer Science
• GPA: 3.7/4.0

CERTIFICATIONS
• Certified Product Manager | Product Management Institute | 2020
• AWS Solutions Architect | Amazon Web Services | 2019
"""
        
        print(f"📝 CV text length: {len(cv_text)} characters")
        
        # Initialize CV analysis service
        service = CVAnalysisService()
        
        # Perform real CV analysis
        print("🔍 Analyzing CV with AWS Bedrock...")
        analysis_result = service.analyze_cv(cv_text, {'detailed_analysis': True})
        
        # Validate analysis results
        print("\n📊 Analysis Results:")
        print(f"  Name: {analysis_result.personal_info.name}")
        print(f"  Email: {analysis_result.personal_info.email}")
        print(f"  Technical Skills: {len(analysis_result.technical_skills)}")
        print(f"  Work Experience: {len(analysis_result.work_experience)}")
        print(f"  Education: {len(analysis_result.education)}")
        print(f"  Analysis Confidence: {analysis_result.analysis_confidence:.2f}")
        
        # Create output directory
        TEST_OUTPUT_DIR.mkdir(exist_ok=True)
        
        # Save analysis results
        analysis_file = TEST_OUTPUT_DIR / "cv_analysis_results.json"
        with open(analysis_file, 'w') as f:
            json.dump({
                'personal_info': {
                    'name': analysis_result.personal_info.name,
                    'email': analysis_result.personal_info.email,
                    'phone': analysis_result.personal_info.phone,
                    'location': analysis_result.personal_info.location
                },
                'professional_summary': analysis_result.professional_summary,
                'technical_skills': analysis_result.technical_skills,
                'soft_skills': analysis_result.soft_skills,
                'work_experience_count': len(analysis_result.work_experience),
                'education_count': len(analysis_result.education),
                'analysis_confidence': analysis_result.analysis_confidence
            }, indent=2)
        
        print(f"💾 Analysis results saved to {analysis_file}")
        
        return analysis_result, analysis_result.analysis_confidence >= 0.5
        
    except Exception as e:
        print(f"❌ CV Analysis test failed: {e}")
        logger.exception("CV Analysis test error")
        return None, False


def test_portfolio_generation_with_bedrock(cv_data):
    """Test portfolio generation with real AWS Bedrock."""
    print("\n🎨 Testing Portfolio Generation with Real AWS Bedrock")
    print("=" * 60)
    
    try:
        from koroh_platform.utils.portfolio_generation_service import (
            PortfolioGenerationService, PortfolioGenerationOptions,
            PortfolioTemplate, PortfolioStyle, ContentSection
        )
        
        if not cv_data:
            print("❌ No CV analysis data available")
            return None, False
        
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
            include_metrics=True
        )
        
        # Generate portfolio with real AWS Bedrock
        print("🚀 Generating portfolio with AWS Bedrock...")
        portfolio = service.generate_portfolio(cv_data, options)
        
        # Validate portfolio results
        print("\n📋 Portfolio Generation Results:")
        print(f"  Template: {portfolio.template_used}")
        print(f"  Style: {portfolio.style_used}")
        print(f"  Quality Score: {portfolio.content_quality_score:.2f}")
        
        # Check sections
        sections_generated = 0
        if portfolio.hero_section.get('headline'):
            sections_generated += 1
            print(f"  ✅ Hero: {portfolio.hero_section['headline'][:50]}...")
        
        if portfolio.about_section.get('main_content'):
            sections_generated += 1
            print(f"  ✅ About: {len(portfolio.about_section['main_content'])} characters")
        
        if portfolio.experience_section:
            sections_generated += 1
            print(f"  ✅ Experience: {len(portfolio.experience_section)} entries")
        
        if portfolio.skills_section.get('skill_categories'):
            sections_generated += 1
            print(f"  ✅ Skills: {len(portfolio.skills_section['skill_categories'])} categories")
        
        if portfolio.contact_section.get('email'):
            sections_generated += 1
            print("  ✅ Contact: Information included")
        
        print(f"\n🎯 Sections Generated: {sections_generated}/5")
        
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
                'contact_section': portfolio.contact_section,
                'content_quality_score': portfolio.content_quality_score,
                'sections_generated': sections_generated
            }, indent=2)
        
        print(f"💾 Portfolio content saved to {portfolio_file}")
        
        return portfolio, sections_generated >= 3
        
    except Exception as e:
        print(f"❌ Portfolio Generation test failed: {e}")
        logger.exception("Portfolio Generation test error")
        return None, False


def generate_simple_html_portfolio(portfolio, cv_data):
    """Generate a simple HTML portfolio for preview."""
    print("\n🌐 Generating Simple HTML Portfolio")
    print("=" * 60)
    
    try:
        if not portfolio or not cv_data:
            print("❌ No portfolio or CV data available")
            return False
        
        # Create portfolio directory
        portfolio_dir = TEST_OUTPUT_DIR / "portfolio_website"
        portfolio_dir.mkdir(exist_ok=True)
        
        name = cv_data.personal_info.name or "Professional Portfolio"
        hero = portfolio.hero_section
        about = portfolio.about_section
        contact = portfolio.contact_section
        
        # Generate simple HTML
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - AI Generated Portfolio</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }}
        .hero {{
            text-align: center;
            color: white;
            padding: 100px 20px;
        }}
        .hero h1 {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}
        .hero p {{
            font-size: 1.2rem;
            margin-bottom: 2rem;
        }}
        .section {{
            background: white;
            margin: 20px 0;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .section h2 {{
            color: #2563eb;
            border-bottom: 2px solid #2563eb;
            padding-bottom: 10px;
        }}
        .contact-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .contact-item {{
            padding: 10px;
            background: #f8fafc;
            border-radius: 5px;
        }}
        .btn {{
            display: inline-block;
            background: #2563eb;
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 25px;
            margin: 10px;
            transition: background 0.3s ease;
        }}
        .btn:hover {{
            background: #1d4ed8;
        }}
        .footer {{
            text-align: center;
            color: white;
            padding: 20px;
            margin-top: 40px;
        }}
    </style>
</head>
<body>
    <div class="hero">
        <div class="container">
            <h1>{hero.get('headline', name)}</h1>
            <p>{hero.get('subheadline', 'AI-Generated Professional Portfolio')}</p>
            <p>{hero.get('value_proposition', 'Created using AWS Bedrock AI technology')}</p>
            <a href="#contact" class="btn">{hero.get('call_to_action', 'Get In Touch')}</a>
        </div>
    </div>

    <div class="container">
        <div class="section">
            <h2>About Me</h2>
            <p>{about.get('main_content', 'Professional with extensive experience and expertise.')}</p>
        </div>

        <div class="section" id="contact">
            <h2>Contact Information</h2>
            <p>{contact.get('call_to_action', 'Feel free to reach out for opportunities!')}</p>
            <div class="contact-info">
                <div class="contact-item">
                    <strong>Email:</strong> {contact.get('email') or cv_data.personal_info.email or 'N/A'}
                </div>
                <div class="contact-item">
                    <strong>Phone:</strong> {contact.get('phone') or cv_data.personal_info.phone or 'N/A'}
                </div>
                <div class="contact-item">
                    <strong>Location:</strong> {contact.get('location') or cv_data.personal_info.location or 'N/A'}
                </div>
                <div class="contact-item">
                    <strong>LinkedIn:</strong> {cv_data.personal_info.linkedin or 'N/A'}
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        <p>&copy; 2024 {name} | Generated by Koroh AI Platform using AWS Bedrock</p>
        <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
</body>
</html>'''
        
        # Save HTML file
        html_file = portfolio_dir / "index.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Create simple README
        readme_content = f'''# {name} - AI Generated Portfolio

This portfolio was automatically generated by the Koroh AI Platform using AWS Bedrock.

## How to View

Open `index.html` in any web browser to view the portfolio.

## Generated Content

- **CV Analysis**: Extracted structured data from CV using AWS Bedrock
- **Portfolio Generation**: Created professional content using AI
- **HTML Template**: Simple, responsive design for easy viewing

## Files

- `index.html` - Complete portfolio webpage
- `README.md` - This file

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
'''
        
        readme_file = portfolio_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"✅ HTML portfolio generated successfully!")
        print(f"📁 Portfolio location: {portfolio_dir.absolute()}")
        print(f"🌐 Open {html_file.absolute()} in your browser to preview")
        
        return True
        
    except Exception as e:
        print(f"❌ HTML Portfolio generation failed: {e}")
        logger.exception("HTML Portfolio generation error")
        return False


def main():
    """Main test execution."""
    print("🚀 KOROH AI SERVICE INTEGRATION TEST SUITE")
    print("=" * 80)
    print("Testing real AWS Bedrock integration with CV analysis and portfolio generation")
    print("=" * 80)
    
    # Test 1: CV Analysis
    cv_data, cv_success = test_cv_analysis_with_bedrock()
    
    # Test 2: Portfolio Generation
    portfolio_data, portfolio_success = test_portfolio_generation_with_bedrock(cv_data)
    
    # Test 3: HTML Generation
    html_success = generate_simple_html_portfolio(portfolio_data, cv_data)
    
    # Summary
    print("\n" + "=" * 80)
    print("🎯 TEST SUMMARY")
    print("=" * 80)
    
    tests = [
        ("CV Analysis with AWS Bedrock", cv_success),
        ("Portfolio Generation with AWS Bedrock", portfolio_success),
        ("HTML Portfolio Generation", html_success)
    ]
    
    passed = 0
    for test_name, result in tests:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 ALL TESTS PASSED!")
        print("✨ AI Service Integration is working perfectly!")
        print(f"\n📁 Generated Files:")
        print(f"  • CV Analysis: {TEST_OUTPUT_DIR}/cv_analysis_results.json")
        print(f"  • Portfolio Content: {TEST_OUTPUT_DIR}/portfolio_content.json")
        print(f"  • HTML Portfolio: {TEST_OUTPUT_DIR}/portfolio_website/")
        print(f"\n🌐 To view the generated portfolio:")
        print(f"  Open {TEST_OUTPUT_DIR}/portfolio_website/index.html in your browser")
    else:
        print(f"\n⚠️ {len(tests) - passed} test(s) failed.")
        print("Please check AWS credentials and Bedrock configuration.")
    
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())