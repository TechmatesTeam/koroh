#!/usr/bin/env python
"""
Comprehensive CV Analysis Test with Real PDF Processing

This test performs a complete analysis of November Odero's resume:
1. Extracts text and images from the actual PDF
2. Analyzes content with real AWS Bedrock AI
3. Assesses social media links and online presence
4. Generates a professional portfolio website
5. Provides detailed feedback, criticism, and recommendations

Requirements: 1.1, 1.2, 6.3
"""

import os
import sys
import django
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import boto3
from botocore.config import Config
from datetime import datetime
import PyPDF2
import fitz  # PyMuPDF for better PDF processing and image extraction
import requests
from urllib.parse import urlparse
import re

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koroh_platform.settings')
django.setup()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TEST_OUTPUT_DIR = Path("comprehensive_cv_analysis")
PDF_PATH = Path("../November Odero-Resume.pdf")


class ComprehensiveCVAnalyzer:
    """Comprehensive CV analyzer with real AWS Bedrock integration."""
    
    def __init__(self):
        """Initialize the analyzer."""
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
        
        # Create output directory
        TEST_OUTPUT_DIR.mkdir(exist_ok=True)
    
    def invoke_ai_model(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Invoke the AI model with a prompt."""
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
        
        if 'choices' in response_body and response_body['choices']:
            content = response_body['choices'][0]['message']['content']
            return content.strip()
        
        return str(response_body)
    
    def extract_pdf_content(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract comprehensive content from PDF including text and images."""
        print(f"📄 Extracting content from {pdf_path}")
        
        content = {
            'text': '',
            'images': [],
            'metadata': {},
            'structure': {
                'pages': 0,
                'sections': [],
                'fonts': set(),
                'colors': set()
            }
        }
        
        try:
            # Open PDF with PyMuPDF for comprehensive extraction
            pdf_document = fitz.open(str(pdf_path))
            content['structure']['pages'] = len(pdf_document)
            
            print(f"📊 PDF has {len(pdf_document)} pages")
            
            all_text = []
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Extract text
                page_text = page.get_text()
                all_text.append(page_text)
                
                # Extract images
                image_list = page.get_images()
                print(f"📷 Page {page_num + 1}: Found {len(image_list)} images")
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Get image data
                        xref = img[0]
                        pix = fitz.Pixmap(pdf_document, xref)
                        
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_data = pix.tobytes("png")
                            img_filename = f"page_{page_num + 1}_img_{img_index + 1}.png"
                            img_path = TEST_OUTPUT_DIR / "images" / img_filename
                            
                            # Create images directory
                            img_path.parent.mkdir(exist_ok=True)
                            
                            # Save image
                            with open(img_path, "wb") as img_file:
                                img_file.write(img_data)
                            
                            content['images'].append({
                                'filename': img_filename,
                                'path': str(img_path),
                                'page': page_num + 1,
                                'size': len(img_data),
                                'dimensions': f"{pix.width}x{pix.height}"
                            })
                            
                            print(f"  💾 Saved image: {img_filename} ({pix.width}x{pix.height})")
                        
                        pix = None
                    except Exception as e:
                        print(f"  ⚠️ Could not extract image {img_index + 1}: {e}")
                
                # Extract font information
                blocks = page.get_text("dict")
                for block in blocks.get("blocks", []):
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line.get("spans", []):
                                font = span.get("font", "")
                                if font:
                                    content['structure']['fonts'].add(font)
            
            # Combine all text
            content['text'] = '\n'.join(all_text).strip()
            
            # Get PDF metadata
            metadata = pdf_document.metadata
            content['metadata'] = {
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'creator': metadata.get('creator', ''),
                'producer': metadata.get('producer', ''),
                'creation_date': metadata.get('creationDate', ''),
                'modification_date': metadata.get('modDate', '')
            }
            
            pdf_document.close()
            
            print(f"✅ Extracted {len(content['text'])} characters of text")
            print(f"📷 Extracted {len(content['images'])} images")
            print(f"🔤 Found {len(content['structure']['fonts'])} different fonts")
            
            return content
            
        except Exception as e:
            print(f"❌ PDF extraction failed: {e}")
            # Fallback to PyPDF2
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    content['text'] = text.strip()
                    content['structure']['pages'] = len(pdf_reader.pages)
                    print(f"✅ Fallback extraction: {len(content['text'])} characters")
                    return content
            except Exception as e2:
                print(f"❌ Fallback extraction also failed: {e2}")
                return content
    
    def analyze_cv_with_ai(self, cv_content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze CV content with real AWS Bedrock AI."""
        print("\n🧠 Analyzing CV with Real AWS Bedrock AI")
        print("=" * 60)
        
        cv_text = cv_content['text']
        
        analysis_prompt = f"""
Please perform a comprehensive analysis of this CV/Resume and provide detailed feedback.

CV TEXT:
{cv_text}

METADATA:
- Pages: {cv_content['structure']['pages']}
- Images: {len(cv_content['images'])}
- Author: {cv_content['metadata'].get('author', 'Not specified')}

Please provide a comprehensive analysis in JSON format with the following structure:

{{
    "personal_info": {{
        "name": "Full name",
        "email": "Email address",
        "phone": "Phone number",
        "location": "Location",
        "linkedin": "LinkedIn URL",
        "github": "GitHub URL",
        "instagram": "Instagram URL",
        "website": "Personal website",
        "other_links": ["any other social media or professional links"]
    }},
    "professional_summary": "Professional summary or objective",
    "technical_skills": ["list of technical skills"],
    "soft_skills": ["list of soft skills"],
    "work_experience": [
        {{
            "company": "Company name",
            "position": "Job title",
            "start_date": "Start date",
            "end_date": "End date",
            "duration": "Duration",
            "description": "Job description",
            "achievements": ["key achievements"],
            "technologies": ["technologies used"]
        }}
    ],
    "education": [
        {{
            "institution": "School/University name",
            "degree": "Degree type",
            "field_of_study": "Field of study",
            "start_date": "Start date",
            "end_date": "End date",
            "gpa": "GPA if mentioned",
            "honors": "Academic honors"
        }}
    ],
    "projects": [
        {{
            "name": "Project name",
            "description": "Project description",
            "technologies": ["technologies used"],
            "url": "Project URL if available",
            "date": "Project date"
        }}
    ],
    "certifications": [
        {{
            "name": "Certification name",
            "issuer": "Issuing organization",
            "date": "Date obtained",
            "expiry": "Expiry date if applicable"
        }}
    ],
    "languages": [
        {{
            "language": "Language name",
            "proficiency": "Proficiency level"
        }}
    ],
    "awards": ["list of awards and recognitions"],
    "interests": ["list of interests and hobbies"],
    "cv_analysis": {{
        "strengths": ["list of CV strengths"],
        "weaknesses": ["list of CV weaknesses"],
        "missing_elements": ["what's missing from the CV"],
        "formatting_feedback": "Feedback on CV formatting and structure",
        "content_quality": "Assessment of content quality",
        "overall_score": "Score out of 10",
        "recommendations": ["specific recommendations for improvement"]
    }}
}}

Provide honest, constructive feedback. Be specific about strengths and areas for improvement.
Respond with valid JSON only.
"""
        
        print("🔍 Processing CV with AI model...")
        response = self.invoke_ai_model(analysis_prompt, max_tokens=4000)
        
        try:
            # Clean and parse JSON response
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            analysis_result = json.loads(cleaned_response)
            
            print("✅ AI analysis completed successfully")
            print(f"📊 Extracted {len(analysis_result.get('technical_skills', []))} technical skills")
            print(f"💼 Found {len(analysis_result.get('work_experience', []))} work experiences")
            print(f"🎓 Found {len(analysis_result.get('education', []))} education entries")
            print(f"⭐ Overall CV Score: {analysis_result.get('cv_analysis', {}).get('overall_score', 'N/A')}/10")
            
            return analysis_result
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse AI response as JSON: {e}")
            print(f"Raw response: {response[:500]}...")
            return {'error': 'Failed to parse AI response', 'raw_response': response}
    
    def assess_online_presence(self, personal_info: Dict[str, Any]) -> Dict[str, Any]:
        """Assess online presence and social media links."""
        print("\n🌐 Assessing Online Presence and Social Media Links")
        print("=" * 60)
        
        assessment = {
            'links_found': {},
            'link_analysis': {},
            'recommendations': [],
            'overall_presence_score': 0
        }
        
        # Extract all links
        links_to_check = {}
        for key, value in personal_info.items():
            if value and isinstance(value, str) and ('http' in value or 'www.' in value or any(platform in value.lower() for platform in ['github', 'linkedin', 'instagram', 'twitter', 'facebook'])):
                links_to_check[key] = value
        
        # Add other_links if present
        if 'other_links' in personal_info and personal_info['other_links']:
            for i, link in enumerate(personal_info['other_links']):
                links_to_check[f'other_link_{i+1}'] = link
        
        print(f"🔍 Found {len(links_to_check)} links to analyze")
        
        for link_type, url in links_to_check.items():
            print(f"\n📱 Analyzing {link_type}: {url}")
            
            # Clean and validate URL
            clean_url = self.clean_url(url)
            assessment['links_found'][link_type] = clean_url
            
            # Analyze each platform
            if 'github' in url.lower():
                analysis = self.analyze_github_profile(clean_url)
            elif 'linkedin' in url.lower():
                analysis = self.analyze_linkedin_profile(clean_url)
            elif 'instagram' in url.lower():
                analysis = self.analyze_instagram_profile(clean_url)
            else:
                analysis = self.analyze_generic_link(clean_url)
            
            assessment['link_analysis'][link_type] = analysis
            print(f"  📊 {link_type} assessment: {analysis.get('status', 'Unknown')}")
        
        # Generate overall recommendations
        assessment['recommendations'] = self.generate_online_presence_recommendations(assessment)
        assessment['overall_presence_score'] = self.calculate_presence_score(assessment)
        
        print(f"\n🎯 Overall Online Presence Score: {assessment['overall_presence_score']}/10")
        
        return assessment
    
    def clean_url(self, url: str) -> str:
        """Clean and normalize URL."""
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            if url.startswith('www.'):
                url = 'https://' + url
            elif any(platform in url.lower() for platform in ['github.com', 'linkedin.com', 'instagram.com']):
                url = 'https://' + url
            else:
                url = 'https://' + url
        return url
    
    def analyze_github_profile(self, url: str) -> Dict[str, Any]:
        """Analyze GitHub profile."""
        analysis = {
            'platform': 'GitHub',
            'url': url,
            'status': 'Unknown',
            'accessibility': False,
            'profile_completeness': 0,
            'activity_level': 'Unknown',
            'recommendations': []
        }
        
        try:
            # Extract username from URL
            username_match = re.search(r'github\.com/([^/]+)', url)
            if not username_match:
                analysis['status'] = 'Invalid URL format'
                analysis['recommendations'].append('Fix GitHub URL format')
                return analysis
            
            username = username_match.group(1)
            
            # Check if profile is accessible (basic check)
            try:
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    analysis['accessibility'] = True
                    analysis['status'] = 'Accessible'
                elif response.status_code == 404:
                    analysis['status'] = 'Profile not found'
                    analysis['recommendations'].append('Verify GitHub username is correct')
                else:
                    analysis['status'] = f'HTTP {response.status_code}'
            except requests.RequestException:
                analysis['status'] = 'Connection failed'
                analysis['recommendations'].append('Check if GitHub profile is public')
            
            # General GitHub recommendations
            analysis['recommendations'].extend([
                'Ensure profile has a professional photo',
                'Add a comprehensive README to your profile',
                'Pin your best repositories',
                'Use descriptive commit messages',
                'Add README files to all repositories',
                'Include live demo links in project descriptions'
            ])
            
        except Exception as e:
            analysis['status'] = f'Analysis failed: {e}'
        
        return analysis
    
    def analyze_linkedin_profile(self, url: str) -> Dict[str, Any]:
        """Analyze LinkedIn profile."""
        analysis = {
            'platform': 'LinkedIn',
            'url': url,
            'status': 'Unknown',
            'accessibility': False,
            'profile_completeness': 0,
            'recommendations': []
        }
        
        try:
            # Check if URL format is correct
            if 'linkedin.com/in/' not in url:
                analysis['status'] = 'Invalid LinkedIn URL format'
                analysis['recommendations'].append('Use proper LinkedIn profile URL format: linkedin.com/in/username')
                return analysis
            
            # Basic accessibility check
            try:
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    analysis['accessibility'] = True
                    analysis['status'] = 'Accessible'
                else:
                    analysis['status'] = f'HTTP {response.status_code}'
            except requests.RequestException:
                analysis['status'] = 'Connection failed'
            
            # LinkedIn recommendations
            analysis['recommendations'].extend([
                'Ensure profile photo is professional and high-quality',
                'Write a compelling headline that goes beyond job title',
                'Craft a detailed summary that tells your professional story',
                'Add all relevant work experience with detailed descriptions',
                'Include education, certifications, and skills',
                'Get recommendations from colleagues and supervisors',
                'Post regularly about industry topics',
                'Connect with professionals in your field'
            ])
            
        except Exception as e:
            analysis['status'] = f'Analysis failed: {e}'
        
        return analysis
    
    def analyze_instagram_profile(self, url: str) -> Dict[str, Any]:
        """Analyze Instagram profile."""
        analysis = {
            'platform': 'Instagram',
            'url': url,
            'status': 'Unknown',
            'accessibility': False,
            'professional_relevance': 'Low',
            'recommendations': []
        }
        
        try:
            # Check URL format
            if 'instagram.com/' not in url:
                analysis['status'] = 'Invalid Instagram URL format'
                analysis['recommendations'].append('Use proper Instagram URL format')
                return analysis
            
            # Basic accessibility check
            try:
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    analysis['accessibility'] = True
                    analysis['status'] = 'Accessible'
                else:
                    analysis['status'] = f'HTTP {response.status_code}'
            except requests.RequestException:
                analysis['status'] = 'Connection failed'
            
            # Instagram recommendations for professional use
            analysis['recommendations'].extend([
                'Consider if Instagram adds value to your professional profile',
                'If included, ensure content is professional and appropriate',
                'Use Instagram to showcase creative work or company culture',
                'Maintain consistent branding across all social platforms',
                'Consider making account private if content is personal'
            ])
            
        except Exception as e:
            analysis['status'] = f'Analysis failed: {e}'
        
        return analysis
    
    def analyze_generic_link(self, url: str) -> Dict[str, Any]:
        """Analyze generic website or link."""
        analysis = {
            'platform': 'Website/Other',
            'url': url,
            'status': 'Unknown',
            'accessibility': False,
            'recommendations': []
        }
        
        try:
            response = requests.head(url, timeout=10)
            if response.status_code == 200:
                analysis['accessibility'] = True
                analysis['status'] = 'Accessible'
            else:
                analysis['status'] = f'HTTP {response.status_code}'
        except requests.RequestException:
            analysis['status'] = 'Connection failed'
            analysis['recommendations'].append('Verify URL is correct and website is online')
        
        # General website recommendations
        analysis['recommendations'].extend([
            'Ensure website loads quickly and is mobile-friendly',
            'Include clear contact information',
            'Showcase your best work prominently',
            'Keep content updated and relevant',
            'Use professional design and typography'
        ])
        
        return analysis
    
    def generate_online_presence_recommendations(self, assessment: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving online presence."""
        recommendations = []
        
        # Check for missing platforms
        platforms_found = set()
        for link_type in assessment['links_found'].keys():
            if 'github' in link_type.lower():
                platforms_found.add('github')
            elif 'linkedin' in link_type.lower():
                platforms_found.add('linkedin')
            elif 'instagram' in link_type.lower():
                platforms_found.add('instagram')
        
        if 'github' not in platforms_found:
            recommendations.append('Add GitHub profile to showcase coding projects and contributions')
        
        if 'linkedin' not in platforms_found:
            recommendations.append('Create LinkedIn profile for professional networking')
        
        # Check accessibility issues
        inaccessible_links = []
        for link_type, analysis in assessment['link_analysis'].items():
            if not analysis.get('accessibility', False):
                inaccessible_links.append(link_type)
        
        if inaccessible_links:
            recommendations.append(f'Fix inaccessible links: {", ".join(inaccessible_links)}')
        
        # General recommendations
        recommendations.extend([
            'Ensure all social media profiles have professional photos',
            'Maintain consistent branding across all platforms',
            'Regularly update profiles with latest achievements',
            'Remove or make private any unprofessional content'
        ])
        
        return recommendations
    
    def calculate_presence_score(self, assessment: Dict[str, Any]) -> int:
        """Calculate overall online presence score."""
        score = 0
        max_score = 10
        
        # Points for having key platforms
        platforms_found = set()
        for link_type in assessment['links_found'].keys():
            if 'github' in link_type.lower():
                platforms_found.add('github')
                score += 3  # GitHub is important for developers
            elif 'linkedin' in link_type.lower():
                platforms_found.add('linkedin')
                score += 4  # LinkedIn is crucial for professionals
            elif 'website' in link_type.lower() or 'portfolio' in link_type.lower():
                score += 2  # Personal website/portfolio
        
        # Points for accessibility
        accessible_count = sum(1 for analysis in assessment['link_analysis'].values() 
                             if analysis.get('accessibility', False))
        total_links = len(assessment['link_analysis'])
        
        if total_links > 0:
            accessibility_score = (accessible_count / total_links) * 1
            score += accessibility_score
        
        return min(int(score), max_score)
    
    def generate_portfolio_with_ai(self, cv_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate professional portfolio content with AI."""
        print("\n🎨 Generating Professional Portfolio with AI")
        print("=" * 60)
        
        portfolio_prompt = f"""
Based on the comprehensive CV analysis, generate professional portfolio content that addresses the identified strengths and weaknesses.

CV ANALYSIS DATA:
{json.dumps(cv_analysis, indent=2)}

Generate compelling, professional portfolio content in JSON format:

{{
    "hero_section": {{
        "headline": "Compelling professional headline that highlights key strengths",
        "subheadline": "Supporting tagline that addresses career goals",
        "value_proposition": "Unique value proposition that differentiates the candidate",
        "call_to_action": "Action-oriented CTA"
    }},
    "about_section": {{
        "main_content": "Engaging 3-4 paragraph about section that tells a compelling professional story, addresses any CV weaknesses, and highlights unique strengths",
        "key_highlights": ["4-5 most impressive achievements and strengths"],
        "personal_touch": "Brief personal element that shows personality while remaining professional"
    }},
    "experience_section": [
        {{
            "company": "Company name",
            "position": "Position title",
            "duration": "Time period",
            "enhanced_description": "Compelling description that focuses on impact, results, and addresses any gaps or weaknesses identified in the CV analysis",
            "key_achievements": ["3-4 quantified achievements"],
            "skills_demonstrated": ["relevant skills"],
            "impact_summary": "One sentence summarizing overall impact and value delivered"
        }}
    ],
    "skills_section": {{
        "skill_categories": {{
            "Technical Skills": {{
                "skills": ["organized technical skills"],
                "proficiency_notes": "Brief note on expertise level"
            }},
            "Professional Skills": {{
                "skills": ["soft skills and professional competencies"],
                "proficiency_notes": "Brief note on expertise level"
            }}
        }},
        "skills_summary": "Brief overview that positions skills strategically and addresses any skill gaps mentioned in CV analysis"
    }},
    "projects_section": [
        {{
            "name": "Project name",
            "description": "Enhanced project description that demonstrates skills and impact",
            "technologies": ["technologies used"],
            "outcomes": ["measurable outcomes or results"],
            "url": "project URL if available"
        }}
    ],
    "contact_section": {{
        "call_to_action": "Compelling message that encourages contact and addresses the target audience",
        "professional_message": "Brief message that reinforces value proposition"
    }},
    "portfolio_improvements": {{
        "cv_weaknesses_addressed": ["how the portfolio addresses CV weaknesses"],
        "strengths_amplified": ["how the portfolio amplifies CV strengths"],
        "strategic_positioning": "How the portfolio positions the candidate strategically in the market"
    }}
}}

Create content that:
1. Addresses weaknesses identified in the CV analysis
2. Amplifies the candidate's strengths
3. Uses compelling, action-oriented language
4. Includes quantifiable results where possible
5. Positions the candidate competitively in their field

Respond with valid JSON only.
"""
        
        print("🚀 Generating portfolio content with AI...")
        response = self.invoke_ai_model(portfolio_prompt, max_tokens=4000)
        
        try:
            # Clean and parse JSON response
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            portfolio_content = json.loads(cleaned_response)
            
            print("✅ Portfolio content generated successfully")
            print(f"📝 Generated {len(portfolio_content.get('experience_section', []))} experience entries")
            print(f"🎯 Generated {len(portfolio_content.get('projects_section', []))} project entries")
            
            return portfolio_content
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse portfolio JSON: {e}")
            print(f"Raw response: {response[:500]}...")
            return {'error': 'Failed to parse portfolio response', 'raw_response': response}
    
    def create_comprehensive_html_portfolio(self, cv_analysis: Dict[str, Any], portfolio_content: Dict[str, Any], online_assessment: Dict[str, Any], cv_content: Dict[str, Any]) -> bool:
        """Create comprehensive HTML portfolio with all analysis results."""
        print("\n🌐 Creating Comprehensive HTML Portfolio")
        print("=" * 60)
        
        try:
            # Create portfolio directory
            portfolio_dir = TEST_OUTPUT_DIR / "portfolio_website"
            portfolio_dir.mkdir(exist_ok=True)
            
            name = cv_analysis.get('personal_info', {}).get('name', 'Professional Portfolio')
            
            # Generate comprehensive HTML
            html_content = self.generate_comprehensive_html(cv_analysis, portfolio_content, online_assessment, name)
            
            # Generate enhanced CSS
            css_content = self.generate_enhanced_css()
            
            # Generate interactive JavaScript
            js_content = self.generate_enhanced_js()
            
            # Save main files
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
            
            # Create detailed analysis report
            analysis_report = self.generate_analysis_report(cv_analysis, online_assessment, cv_content)
            report_file = portfolio_dir / "cv_analysis_report.html"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(analysis_report)
            files_created['cv_analysis_report.html'] = report_file.stat().st_size
            
            # Copy extracted images to portfolio
            if cv_content['images']:
                images_dir = portfolio_dir / "images"
                images_dir.mkdir(exist_ok=True)
                
                for img_info in cv_content['images']:
                    src_path = Path(img_info['path'])
                    if src_path.exists():
                        dst_path = images_dir / img_info['filename']
                        import shutil
                        shutil.copy2(src_path, dst_path)
                        print(f"📷 Copied image: {img_info['filename']}")
            
            # Create comprehensive README
            readme_content = self.generate_comprehensive_readme(name, cv_analysis, online_assessment, files_created)
            readme_file = portfolio_dir / "README.md"
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            files_created['README.md'] = readme_file.stat().st_size
            
            print("✅ Comprehensive portfolio generated successfully!")
            print(f"📁 Portfolio location: {portfolio_dir.absolute()}")
            print(f"🌐 Main portfolio: {html_file.absolute()}")
            print(f"📊 Analysis report: {report_file.absolute()}")
            
            print("\n📋 Generated Files:")
            total_size = 0
            for filename, size in files_created.items():
                print(f"  ✅ {filename}: {size:,} bytes")
                total_size += size
            
            print(f"\n📊 Total Portfolio Size: {total_size:,} bytes")
            print("🤖 Content: Generated by real AWS Bedrock AI with comprehensive analysis")
            
            return True
            
        except Exception as e:
            print(f"❌ Portfolio generation failed: {e}")
            logger.exception("Portfolio generation error")
            return False
    
    def generate_comprehensive_html(self, cv_analysis: Dict[str, Any], portfolio_content: Dict[str, Any], online_assessment: Dict[str, Any], name: str) -> str:
        """Generate comprehensive HTML with all features."""
        personal_info = cv_analysis.get('personal_info', {})
        hero = portfolio_content.get('hero_section', {})
        about = portfolio_content.get('about_section', {})
        experience = portfolio_content.get('experience_section', [])
        skills = portfolio_content.get('skills_section', {})
        projects = portfolio_content.get('projects_section', [])
        contact = portfolio_content.get('contact_section', {})
        cv_feedback = cv_analysis.get('cv_analysis', {})
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - AI-Enhanced Professional Portfolio</title>
    <meta name="description" content="Professional portfolio for {name} - Generated and enhanced by AI analysis">
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
                <li><a href="#projects" class="nav-link">Projects</a></li>
                <li><a href="#contact" class="nav-link">Contact</a></li>
                <li><a href="cv_analysis_report.html" class="nav-link analysis-link">📊 CV Analysis</a></li>
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
                <div class="ai-badge">🤖 AI-Enhanced Portfolio</div>
                <h1 class="hero-title">{hero.get('headline', name)}</h1>
                <p class="hero-subtitle">{hero.get('subheadline', 'Professional Portfolio Enhanced by AI Analysis')}</p>
                <p class="hero-description">{hero.get('value_proposition', 'Professional portfolio created with comprehensive AI analysis and optimization')}</p>
                <div class="hero-stats">
                    <div class="stat">
                        <span class="stat-number">{cv_feedback.get('overall_score', 'N/A')}</span>
                        <span class="stat-label">CV Score</span>
                    </div>
                    <div class="stat">
                        <span class="stat-number">{online_assessment.get('overall_presence_score', 0)}</span>
                        <span class="stat-label">Online Presence</span>
                    </div>
                    <div class="stat">
                        <span class="stat-number">{len(cv_analysis.get('technical_skills', []))}</span>
                        <span class="stat-label">Skills</span>
                    </div>
                </div>
                <div class="hero-buttons">
                    <a href="#contact" class="btn btn-primary">{hero.get('call_to_action', 'Get In Touch')}</a>
                    <a href="cv_analysis_report.html" class="btn btn-secondary">📊 View AI Analysis</a>
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
                    {self.format_highlights(about.get('key_highlights', []))}
                    {f'<p class="personal-touch"><em>{about.get("personal_touch", "")}</em></p>' if about.get('personal_touch') else ''}
                </div>
                <div class="ai-insights">
                    <h3>🤖 AI Analysis Insights</h3>
                    <div class="insights-grid">
                        <div class="insight-card strength">
                            <h4>💪 Key Strengths</h4>
                            <ul>
                                {self.format_list_items(cv_feedback.get('strengths', [])[:3])}
                            </ul>
                        </div>
                        <div class="insight-card improvement">
                            <h4>🎯 Areas for Growth</h4>
                            <ul>
                                {self.format_list_items(cv_feedback.get('recommendations', [])[:3])}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Experience Section -->
    <section id="experience" class="experience">
        <div class="container">
            <h2 class="section-title">Professional Experience</h2>
            <div class="timeline">
                {self.format_enhanced_experience(experience)}
            </div>
        </div>
    </section>

    <!-- Skills Section -->
    <section id="skills" class="skills">
        <div class="container">
            <h2 class="section-title">Skills & Expertise</h2>
            <div class="skills-grid">
                {self.format_enhanced_skills(skills)}
            </div>
            <div class="skills-summary">
                <p>{skills.get('skills_summary', 'Comprehensive skill set with proven expertise.')}</p>
            </div>
        </div>
    </section>

    <!-- Projects Section -->
    <section id="projects" class="projects">
        <div class="container">
            <h2 class="section-title">Featured Projects</h2>
            <div class="projects-grid">
                {self.format_projects(projects)}
            </div>
        </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="contact">
        <div class="container">
            <h2 class="section-title">Get In Touch</h2>
            <div class="contact-content">
                <div class="contact-info">
                    <p class="contact-cta">{contact.get('call_to_action', 'Feel free to reach out for opportunities!')}</p>
                    <p class="professional-message">{contact.get('professional_message', '')}</p>
                    <div class="contact-details">
                        {self.format_enhanced_contact_details(personal_info, online_assessment)}
                    </div>
                    <div class="online-presence-score">
                        <h4>🌐 Online Presence Score: {online_assessment.get('overall_presence_score', 0)}/10</h4>
                        <div class="presence-recommendations">
                            {self.format_list_items(online_assessment.get('recommendations', [])[:2])}
                        </div>
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
            <p>&copy; 2024 {name}. Portfolio enhanced by AWS Bedrock AI Analysis.</p>
            <p>Generated from comprehensive CV analysis including PDF extraction, content analysis, and online presence assessment.</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>'''  
  
    def format_highlights(self, highlights: List[str]) -> str:
        """Format key highlights as HTML."""
        if not highlights:
            return ""
        
        html = '<div class="highlights"><h3>Key Highlights</h3><ul>'
        for highlight in highlights:
            html += f'<li>{highlight}</li>'
        html += '</ul></div>'
        return html
    
    def format_list_items(self, items: List[str]) -> str:
        """Format list items as HTML."""
        if not items:
            return '<li>No items available</li>'
        
        return ''.join(f'<li>{item}</li>' for item in items)
    
    def format_enhanced_experience(self, experience: List[Dict[str, Any]]) -> str:
        """Format experience entries with enhancements."""
        if not experience:
            return '<div class="timeline-item"><div class="timeline-content"><p>No experience data available.</p></div></div>'
        
        html = ""
        for exp in experience:
            company = exp.get('company', 'Company')
            position = exp.get('position', 'Position')
            duration = exp.get('duration', '')
            description = exp.get('enhanced_description', exp.get('description', ''))
            achievements = exp.get('key_achievements', [])
            skills = exp.get('skills_demonstrated', [])
            impact = exp.get('impact_summary', '')
            
            html += f'''
            <div class="timeline-item">
                <div class="timeline-content">
                    <h3>{position}</h3>
                    <h4>{company}</h4>
                    <span class="timeline-date">{duration}</span>
                    <p>{description}</p>
                    {self.format_achievements(achievements)}
                    {self.format_skills_demonstrated(skills)}
                    {f'<p class="impact-summary">{impact}</p>' if impact else ''}
                </div>
            </div>'''
        
        return html
    
    def format_achievements(self, achievements: List[str]) -> str:
        """Format achievements as HTML."""
        if not achievements:
            return ""
        
        html = '<div class="achievements"><h5>Key Achievements:</h5><ul>'
        for achievement in achievements:
            html += f'<li>{achievement}</li>'
        html += '</ul></div>'
        return html
    
    def format_skills_demonstrated(self, skills: List[str]) -> str:
        """Format skills demonstrated as HTML."""
        if not skills:
            return ""
        
        html = '<div class="skills-demonstrated"><h5>Skills Demonstrated:</h5><div class="skill-tags">'
        for skill in skills:
            html += f'<span class="skill-tag">{skill}</span>'
        html += '</div></div>'
        return html
    
    def format_enhanced_skills(self, skills: Dict[str, Any]) -> str:
        """Format skills with enhancements."""
        if not skills or not skills.get('skill_categories'):
            return '<div class="skill-category"><p>No skills data available.</p></div>'
        
        html = ""
        categories = skills.get('skill_categories', {})
        
        for category_name, category_data in categories.items():
            if isinstance(category_data, dict):
                skills_list = category_data.get('skills', [])
                proficiency_notes = category_data.get('proficiency_notes', '')
            else:
                skills_list = category_data if isinstance(category_data, list) else []
                proficiency_notes = ''
            
            html += f'''
            <div class="skill-category">
                <h3>{category_name}</h3>
                <div class="skill-items">
                    {self.format_skill_items(skills_list)}
                </div>
                {f'<p class="proficiency-notes">{proficiency_notes}</p>' if proficiency_notes else ''}
            </div>'''
        
        return html
    
    def format_skill_items(self, skills_list: List[str]) -> str:
        """Format individual skill items."""
        if not skills_list:
            return ""
        
        html = ""
        for skill in skills_list:
            html += f'<span class="skill-tag">{skill}</span>'
        
        return html
    
    def format_projects(self, projects: List[Dict[str, Any]]) -> str:
        """Format projects section."""
        if not projects:
            return '<div class="project-card"><p>No projects data available.</p></div>'
        
        html = ""
        for project in projects:
            name = project.get('name', 'Project')
            description = project.get('description', '')
            technologies = project.get('technologies', [])
            outcomes = project.get('outcomes', [])
            url = project.get('url', '')
            
            html += f'''
            <div class="project-card">
                <h3>{name}</h3>
                <p>{description}</p>
                {self.format_project_technologies(technologies)}
                {self.format_project_outcomes(outcomes)}
                {f'<a href="{url}" target="_blank" class="project-link">View Project</a>' if url else ''}
            </div>'''
        
        return html
    
    def format_project_technologies(self, technologies: List[str]) -> str:
        """Format project technologies."""
        if not technologies:
            return ""
        
        html = '<div class="project-technologies"><h5>Technologies:</h5><div class="tech-tags">'
        for tech in technologies:
            html += f'<span class="tech-tag">{tech}</span>'
        html += '</div></div>'
        return html
    
    def format_project_outcomes(self, outcomes: List[str]) -> str:
        """Format project outcomes."""
        if not outcomes:
            return ""
        
        html = '<div class="project-outcomes"><h5>Outcomes:</h5><ul>'
        for outcome in outcomes:
            html += f'<li>{outcome}</li>'
        html += '</ul></div>'
        return html
    
    def format_enhanced_contact_details(self, personal_info: Dict[str, Any], online_assessment: Dict[str, Any]) -> str:
        """Format enhanced contact details with online presence analysis."""
        html = ""
        
        # Basic contact info
        email = personal_info.get('email')
        phone = personal_info.get('phone')
        location = personal_info.get('location')
        
        if email:
            html += f'<div class="contact-item"><i class="fas fa-envelope"></i><a href="mailto:{email}">{email}</a></div>'
        
        if phone:
            html += f'<div class="contact-item"><i class="fas fa-phone"></i><a href="tel:{phone}">{phone}</a></div>'
        
        if location:
            html += f'<div class="contact-item"><i class="fas fa-map-marker-alt"></i><span>{location}</span></div>'
        
        # Social media links with status
        links_analysis = online_assessment.get('link_analysis', {})
        
        for link_type, analysis in links_analysis.items():
            url = analysis.get('url', '')
            status = analysis.get('accessibility', False)
            platform = analysis.get('platform', 'Website')
            
            if url:
                status_class = 'accessible' if status else 'inaccessible'
                status_icon = '✅' if status else '❌'
                
                if 'github' in link_type.lower():
                    icon = 'fab fa-github'
                elif 'linkedin' in link_type.lower():
                    icon = 'fab fa-linkedin'
                elif 'instagram' in link_type.lower():
                    icon = 'fab fa-instagram'
                else:
                    icon = 'fas fa-globe'
                
                html += f'''
                <div class="contact-item {status_class}">
                    <i class="{icon}"></i>
                    <a href="{url}" target="_blank">{platform}</a>
                    <span class="status-indicator">{status_icon}</span>
                </div>'''
        
        return html
    
    def generate_enhanced_css(self) -> str:
        """Generate enhanced CSS with AI analysis features."""
        return '''/* Enhanced Portfolio CSS with AI Analysis Features */
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

.analysis-link {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white !important;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.9rem;
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

.ai-badge {
    background: rgba(255, 255, 255, 0.2);
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.9rem;
    margin-bottom: 1rem;
    display: inline-block;
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

.hero-stats {
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin-bottom: 2rem;
    animation: fadeInUp 1s ease 0.5s both;
}

.stat {
    text-align: center;
}

.stat-number {
    display: block;
    font-size: 2rem;
    font-weight: 700;
    color: #fbbf24;
}

.stat-label {
    font-size: 0.9rem;
    opacity: 0.8;
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

.about-content {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 3rem;
    max-width: 1200px;
    margin: 0 auto;
}

.about-text {
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
}

.ai-insights {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.ai-insights h3 {
    color: #2563eb;
    margin-bottom: 1.5rem;
}

.insights-grid {
    display: grid;
    gap: 1rem;
}

.insight-card {
    padding: 1.5rem;
    border-radius: 8px;
    border-left: 4px solid;
}

.insight-card.strength {
    background: #f0fdf4;
    border-left-color: #10b981;
}

.insight-card.improvement {
    background: #fef3c7;
    border-left-color: #f59e0b;
}

.insight-card h4 {
    margin-bottom: 1rem;
    font-size: 1.1rem;
}

.insight-card ul {
    list-style: none;
}

.insight-card li {
    padding: 0.25rem 0;
    font-size: 0.9rem;
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
    background: #f8fafc;
    padding: 1rem;
    border-radius: 8px;
}

.achievements h5 {
    color: #2563eb;
    margin-bottom: 0.5rem;
    font-size: 1rem;
}

.achievements ul {
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

.skills-demonstrated {
    margin-top: 1rem;
}

.skills-demonstrated h5 {
    color: #2563eb;
    margin-bottom: 0.5rem;
    font-size: 1rem;
}

.skill-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.skill-tag {
    background: #e0e7ff;
    color: #3730a3;
    padding: 0.25rem 0.75rem;
    border-radius: 15px;
    font-size: 0.8rem;
    font-weight: 500;
}

.impact-summary {
    margin-top: 1rem;
    font-style: italic;
    color: #64748b;
    border-left: 3px solid #2563eb;
    padding-left: 1rem;
    background: #f1f5f9;
    padding: 1rem;
    border-radius: 0 8px 8px 0;
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

.proficiency-notes {
    color: #64748b;
    font-style: italic;
    font-size: 0.9rem;
}

.skills-summary {
    max-width: 800px;
    margin: 3rem auto 0;
    text-align: center;
    font-size: 1.1rem;
    color: #64748b;
}

/* Projects Section */
.projects-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 2rem;
    max-width: 1200px;
    margin: 0 auto;
}

.project-card {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease;
}

.project-card:hover {
    transform: translateY(-5px);
}

.project-card h3 {
    color: #2563eb;
    margin-bottom: 1rem;
}

.project-technologies {
    margin-top: 1rem;
}

.project-technologies h5 {
    color: #2563eb;
    margin-bottom: 0.5rem;
    font-size: 1rem;
}

.tech-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.tech-tag {
    background: #ddd6fe;
    color: #5b21b6;
    padding: 0.25rem 0.75rem;
    border-radius: 15px;
    font-size: 0.8rem;
    font-weight: 500;
}

.project-outcomes {
    margin-top: 1rem;
}

.project-outcomes h5 {
    color: #2563eb;
    margin-bottom: 0.5rem;
    font-size: 1rem;
}

.project-outcomes ul {
    list-style: none;
}

.project-outcomes li {
    padding: 0.25rem 0;
    position: relative;
    padding-left: 1.5rem;
}

.project-outcomes li:before {
    content: "✓";
    position: absolute;
    left: 0;
    color: #10b981;
    font-weight: bold;
}

.project-link {
    display: inline-block;
    margin-top: 1rem;
    color: #2563eb;
    text-decoration: none;
    font-weight: 500;
}

.project-link:hover {
    text-decoration: underline;
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
    margin-bottom: 1rem;
    opacity: 0.9;
}

.professional-message {
    margin-bottom: 2rem;
    opacity: 0.8;
}

.contact-details {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 2rem;
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

.contact-item.accessible {
    opacity: 1;
}

.contact-item.inaccessible {
    opacity: 0.6;
}

.status-indicator {
    margin-left: auto;
    font-size: 0.8rem;
}

.online-presence-score {
    background: rgba(255, 255, 255, 0.1);
    padding: 1.5rem;
    border-radius: 10px;
}

.online-presence-score h4 {
    margin-bottom: 1rem;
    color: #fbbf24;
}

.presence-recommendations {
    font-size: 0.9rem;
    opacity: 0.8;
}

.presence-recommendations li {
    padding: 0.25rem 0;
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
    
    .hero-stats {
        flex-direction: column;
        gap: 1rem;
    }
    
    .about-content {
        grid-template-columns: 1fr;
        gap: 2rem;
    }
    
    .contact-content {
        grid-template-columns: 1fr;
        gap: 2rem;
    }
    
    .nav-menu {
        display: none;
    }
}'''  
  
    def generate_enhanced_js(self) -> str:
        """Generate enhanced JavaScript with additional features."""
        return '''// Enhanced Portfolio JavaScript with AI Features
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for navigation links
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            
            // Handle external links
            if (targetId.includes('.html')) {
                window.open(targetId, '_blank');
                return;
            }
            
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
            
            if (!name || !email || !message) {
                alert('Please fill in all fields.');
                return;
            }
            
            alert(`Thank you ${name}! This is an AI-enhanced portfolio demo. Your message would be sent in a real implementation.`);
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

    // AI insights animation
    const insightCards = document.querySelectorAll('.insight-card');
    insightCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.2}s`;
        card.classList.add('fade-in-up');
    });

    // Project cards hover effects
    const projectCards = document.querySelectorAll('.project-card');
    projectCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
});

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    .fade-in-up {
        animation: fadeInUp 0.6s ease forwards;
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
    
    def generate_analysis_report(self, cv_analysis: Dict[str, Any], online_assessment: Dict[str, Any], cv_content: Dict[str, Any]) -> str:
        """Generate detailed analysis report HTML."""
        cv_feedback = cv_analysis.get('cv_analysis', {})
        personal_info = cv_analysis.get('personal_info', {})
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CV Analysis Report - {personal_info.get('name', 'Professional')}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f8fafc;
            margin: 0;
            padding: 2rem;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }}
        .content {{
            padding: 2rem;
        }}
        .section {{
            margin-bottom: 2rem;
            padding: 1.5rem;
            border-radius: 8px;
            border-left: 4px solid #2563eb;
        }}
        .section.strength {{
            background: #f0fdf4;
            border-left-color: #10b981;
        }}
        .section.weakness {{
            background: #fef2f2;
            border-left-color: #ef4444;
        }}
        .section.recommendation {{
            background: #fef3c7;
            border-left-color: #f59e0b;
        }}
        .score-circle {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 80px;
            height: 80px;
            border-radius: 50%;
            font-size: 1.5rem;
            font-weight: 700;
            margin: 0 1rem;
        }}
        .score-excellent {{ background: #10b981; color: white; }}
        .score-good {{ background: #f59e0b; color: white; }}
        .score-poor {{ background: #ef4444; color: white; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin: 1.5rem 0;
        }}
        .card {{
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .link-status {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin: 0.5rem 0;
        }}
        .status-good {{ color: #10b981; }}
        .status-bad {{ color: #ef4444; }}
        ul {{
            padding-left: 1.5rem;
        }}
        li {{
            margin: 0.5rem 0;
        }}
        .back-link {{
            display: inline-block;
            margin-bottom: 2rem;
            color: #2563eb;
            text-decoration: none;
            font-weight: 500;
        }}
        .back-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI-Powered CV Analysis Report</h1>
            <p>Comprehensive analysis of {personal_info.get('name', 'Professional')}'s CV</p>
            <p>Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
        </div>
        
        <div class="content">
            <a href="index.html" class="back-link">← Back to Portfolio</a>
            
            <div class="section">
                <h2>📊 Overall Assessment</h2>
                <div style="text-align: center; margin: 2rem 0;">
                    <div class="score-circle {self.get_score_class(cv_feedback.get('overall_score', '0'))}">
                        {cv_feedback.get('overall_score', 'N/A')}/10
                    </div>
                    <div class="score-circle {self.get_score_class(online_assessment.get('overall_presence_score', 0))}">
                        {online_assessment.get('overall_presence_score', 0)}/10
                    </div>
                </div>
                <div style="text-align: center;">
                    <p><strong>CV Quality Score</strong> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <strong>Online Presence Score</strong></p>
                </div>
            </div>
            
            <div class="grid">
                <div class="section strength">
                    <h3>💪 Strengths Identified</h3>
                    <ul>
                        {self.format_list_items(cv_feedback.get('strengths', ['No strengths identified']))}
                    </ul>
                </div>
                
                <div class="section weakness">
                    <h3>⚠️ Areas for Improvement</h3>
                    <ul>
                        {self.format_list_items(cv_feedback.get('weaknesses', ['No weaknesses identified']))}
                    </ul>
                </div>
            </div>
            
            <div class="section recommendation">
                <h3>🎯 Specific Recommendations</h3>
                <ul>
                    {self.format_list_items(cv_feedback.get('recommendations', ['No specific recommendations']))}
                </ul>
            </div>
            
            <div class="section">
                <h3>📄 CV Structure Analysis</h3>
                <div class="grid">
                    <div class="card">
                        <h4>Document Information</h4>
                        <p><strong>Pages:</strong> {cv_content['structure']['pages']}</p>
                        <p><strong>Images:</strong> {len(cv_content['images'])}</p>
                        <p><strong>Text Length:</strong> {len(cv_content['text'])} characters</p>
                        <p><strong>Author:</strong> {cv_content['metadata'].get('author', 'Not specified')}</p>
                    </div>
                    
                    <div class="card">
                        <h4>Content Quality</h4>
                        <p><strong>Technical Skills:</strong> {len(cv_analysis.get('technical_skills', []))}</p>
                        <p><strong>Work Experience:</strong> {len(cv_analysis.get('work_experience', []))}</p>
                        <p><strong>Education:</strong> {len(cv_analysis.get('education', []))}</p>
                        <p><strong>Certifications:</strong> {len(cv_analysis.get('certifications', []))}</p>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h3>🌐 Online Presence Analysis</h3>
                <div class="card">
                    <h4>Social Media & Professional Links</h4>
                    {self.format_online_presence_analysis(online_assessment)}
                </div>
                
                <div style="margin-top: 1.5rem;">
                    <h4>Recommendations for Online Presence:</h4>
                    <ul>
                        {self.format_list_items(online_assessment.get('recommendations', ['No recommendations available']))}
                    </ul>
                </div>
            </div>
            
            <div class="section">
                <h3>📝 Content Feedback</h3>
                <p><strong>Formatting:</strong> {cv_feedback.get('formatting_feedback', 'No formatting feedback available')}</p>
                <p><strong>Content Quality:</strong> {cv_feedback.get('content_quality', 'No content quality assessment available')}</p>
                
                <h4>Missing Elements:</h4>
                <ul>
                    {self.format_list_items(cv_feedback.get('missing_elements', ['No missing elements identified']))}
                </ul>
            </div>
            
            <div class="section">
                <h3>🚀 Next Steps</h3>
                <ol>
                    <li>Address the weaknesses identified in the analysis</li>
                    <li>Implement the specific recommendations provided</li>
                    <li>Improve online presence based on the assessment</li>
                    <li>Update CV with missing elements</li>
                    <li>Consider professional portfolio creation (like this one!)</li>
                </ol>
            </div>
        </div>
    </div>
</body>
</html>'''
    
    def get_score_class(self, score) -> str:
        """Get CSS class based on score."""
        try:
            score_num = float(str(score))
            if score_num >= 8:
                return 'score-excellent'
            elif score_num >= 6:
                return 'score-good'
            else:
                return 'score-poor'
        except (ValueError, TypeError):
            return 'score-poor'
    
    def format_online_presence_analysis(self, online_assessment: Dict[str, Any]) -> str:
        """Format online presence analysis for the report."""
        html = ""
        
        links_analysis = online_assessment.get('link_analysis', {})
        
        if not links_analysis:
            return "<p>No social media or professional links found in CV.</p>"
        
        for link_type, analysis in links_analysis.items():
            url = analysis.get('url', '')
            status = analysis.get('accessibility', False)
            platform = analysis.get('platform', 'Website')
            
            status_class = 'status-good' if status else 'status-bad'
            status_icon = '✅' if status else '❌'
            status_text = 'Accessible' if status else 'Inaccessible'
            
            html += f'''
            <div class="link-status">
                <span class="{status_class}">{status_icon}</span>
                <strong>{platform}:</strong>
                <a href="{url}" target="_blank">{url}</a>
                <span class="{status_class}">({status_text})</span>
            </div>'''
        
        return html
    
    def generate_comprehensive_readme(self, name: str, cv_analysis: Dict[str, Any], online_assessment: Dict[str, Any], files_created: Dict[str, int]) -> str:
        """Generate comprehensive README."""
        cv_feedback = cv_analysis.get('cv_analysis', {})
        
        return f'''# {name} - AI-Enhanced Professional Portfolio

This portfolio was generated through comprehensive AI analysis of {name}'s CV using real AWS Bedrock technology.

## 🤖 AI Analysis Summary

### CV Quality Assessment
- **Overall Score**: {cv_feedback.get('overall_score', 'N/A')}/10
- **Online Presence Score**: {online_assessment.get('overall_presence_score', 0)}/10
- **Technical Skills Identified**: {len(cv_analysis.get('technical_skills', []))}
- **Work Experience Entries**: {len(cv_analysis.get('work_experience', []))}

### Key Findings
**Strengths:**
{self.format_readme_list(cv_feedback.get('strengths', []))}

**Areas for Improvement:**
{self.format_readme_list(cv_feedback.get('recommendations', []))}

## 📁 Generated Files

{self.format_files_list(files_created)}

## 🌐 How to View

1. **Main Portfolio**: Open `index.html` in any modern web browser
2. **Analysis Report**: Open `cv_analysis_report.html` for detailed AI analysis
3. **Local Server** (recommended for best experience):
   ```bash
   python -m http.server 8000
   # Then open http://localhost:8000
   ```

## 🎯 Features

### Portfolio Features
- **Responsive Design**: Works perfectly on all devices
- **AI-Enhanced Content**: All content optimized based on CV analysis
- **Professional Styling**: Modern, clean design optimized for recruiters
- **Interactive Elements**: Smooth scrolling, animations, contact form
- **Analysis Integration**: CV insights embedded throughout the portfolio

### Analysis Features
- **PDF Content Extraction**: Text and images extracted from original PDF
- **Comprehensive CV Analysis**: Strengths, weaknesses, and recommendations
- **Online Presence Assessment**: Social media and professional links analysis
- **Detailed Reporting**: Comprehensive analysis report with actionable insights

## 🔧 Technical Implementation

### AI Processing Pipeline
1. **PDF Extraction**: PyMuPDF for comprehensive content extraction
2. **AI Analysis**: AWS Bedrock Qwen model for intelligent CV analysis
3. **Content Generation**: AI-powered portfolio content creation
4. **Online Assessment**: Automated social media and link validation
5. **Portfolio Generation**: Complete HTML/CSS/JavaScript website creation

### Technologies Used
- **AI Model**: {cv_analysis.get('model', 'qwen.qwen3-32b-v1:0')}
- **PDF Processing**: PyMuPDF (fitz) for text and image extraction
- **Web Technologies**: HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Modern CSS with animations and responsive design
- **Icons**: Font Awesome 6.0
- **Fonts**: Inter (Google Fonts)

## 📊 Analysis Methodology

### CV Analysis Criteria
- Content completeness and structure
- Professional presentation quality
- Skills and experience alignment
- Missing elements identification
- Formatting and readability assessment

### Online Presence Evaluation
- Link accessibility and validity
- Platform appropriateness for professional use
- Profile completeness indicators
- Recommendations for improvement

## 🎨 Design Philosophy

The portfolio design addresses specific weaknesses identified in the CV analysis:
- Enhanced visual hierarchy for better readability
- Strategic content placement to highlight strengths
- Professional color scheme and typography
- Mobile-first responsive design
- Accessibility considerations throughout

## 📈 Recommendations Implemented

Based on the AI analysis, this portfolio:
- Addresses identified CV weaknesses through enhanced presentation
- Amplifies strengths with strategic content placement
- Provides professional online presence
- Includes comprehensive contact information
- Showcases skills and experience effectively

## 🔮 Future Enhancements

Potential improvements based on analysis:
- Integration with live social media feeds
- Dynamic content updates from professional platforms
- Advanced analytics and visitor tracking
- Multi-language support
- PDF resume generation from portfolio content

---

**Generated by Koroh AI Platform**  
**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Analysis Model**: AWS Bedrock Qwen 3-32B  
**Processing**: Comprehensive PDF extraction + AI analysis + Portfolio generation  
**Status**: ✅ Complete professional portfolio with AI insights
'''
    
    def format_readme_list(self, items: List[str]) -> str:
        """Format list for README."""
        if not items:
            return "- No items identified"
        
        return '\n'.join(f'- {item}' for item in items[:5])  # Limit to top 5
    
    def format_files_list(self, files_created: Dict[str, int]) -> str:
        """Format files list for README."""
        lines = []
        for filename, size in files_created.items():
            lines.append(f'- **{filename}**: {size:,} bytes')
        
        total_size = sum(files_created.values())
        lines.append(f'\n**Total Size**: {total_size:,} bytes')
        
        return '\n'.join(lines)


def main():
    """Run comprehensive CV analysis with November Odero's resume."""
    print("🚀 COMPREHENSIVE CV ANALYSIS WITH REAL AWS BEDROCK")
    print("=" * 80)
    print(f"Analyzing: {PDF_PATH}")
    print("=" * 80)
    
    if not PDF_PATH.exists():
        print(f"❌ PDF file not found: {PDF_PATH}")
        return 1
    
    # Initialize analyzer
    analyzer = ComprehensiveCVAnalyzer()
    
    try:
        # Step 1: Extract PDF content
        print("📄 Step 1: Extracting PDF Content")
        cv_content = analyzer.extract_pdf_content(PDF_PATH)
        
        if not cv_content['text']:
            print("❌ No text content extracted from PDF")
            return 1
        
        # Step 2: Analyze CV with AI
        print("\n🧠 Step 2: AI Analysis of CV Content")
        cv_analysis = analyzer.analyze_cv_with_ai(cv_content)
        
        if 'error' in cv_analysis:
            print(f"❌ AI analysis failed: {cv_analysis['error']}")
            return 1
        
        # Step 3: Assess online presence
        print("\n🌐 Step 3: Assessing Online Presence")
        online_assessment = analyzer.assess_online_presence(cv_analysis.get('personal_info', {}))
        
        # Step 4: Generate portfolio with AI
        print("\n🎨 Step 4: Generating AI-Enhanced Portfolio")
        portfolio_content = analyzer.generate_portfolio_with_ai(cv_analysis)
        
        if 'error' in portfolio_content:
            print(f"❌ Portfolio generation failed: {portfolio_content['error']}")
            return 1
        
        # Step 5: Create comprehensive HTML portfolio
        print("\n🌐 Step 5: Creating Comprehensive HTML Portfolio")
        html_success = analyzer.create_comprehensive_html_portfolio(
            cv_analysis, portfolio_content, online_assessment, cv_content
        )
        
        # Step 6: Save comprehensive analysis results
        print("\n💾 Step 6: Saving Analysis Results")
        
        # Save all analysis data
        analysis_data = {
            'metadata': {
                'pdf_file': str(PDF_PATH),
                'analysis_date': datetime.now().isoformat(),
                'model_used': analyzer.model_id,
                'total_processing_time': 'Complete'
            },
            'pdf_content': {
                'text_length': len(cv_content['text']),
                'images_extracted': len(cv_content['images']),
                'pages': cv_content['structure']['pages'],
                'metadata': cv_content['metadata']
            },
            'cv_analysis': cv_analysis,
            'online_assessment': online_assessment,
            'portfolio_content': portfolio_content
        }
        
        analysis_file = TEST_OUTPUT_DIR / "comprehensive_analysis_results.json"
        with open(analysis_file, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        print(f"💾 Complete analysis saved to {analysis_file}")
        
        # Summary
        print("\n" + "=" * 80)
        print("🎯 COMPREHENSIVE ANALYSIS SUMMARY")
        print("=" * 80)
        
        cv_feedback = cv_analysis.get('cv_analysis', {})
        
        print(f"📊 CV Quality Score: {cv_feedback.get('overall_score', 'N/A')}/10")
        print(f"🌐 Online Presence Score: {online_assessment.get('overall_presence_score', 0)}/10")
        print(f"📝 Technical Skills Found: {len(cv_analysis.get('technical_skills', []))}")
        print(f"💼 Work Experience Entries: {len(cv_analysis.get('work_experience', []))}")
        print(f"🎓 Education Entries: {len(cv_analysis.get('education', []))}")
        print(f"📷 Images Extracted: {len(cv_content['images'])}")
        print(f"🔗 Social Links Analyzed: {len(online_assessment.get('link_analysis', {}))}")
        
        print(f"\n📁 Generated Files:")
        print(f"  • Main Portfolio: {TEST_OUTPUT_DIR}/portfolio_website/index.html")
        print(f"  • Analysis Report: {TEST_OUTPUT_DIR}/portfolio_website/cv_analysis_report.html")
        print(f"  • Complete Data: {analysis_file}")
        
        print(f"\n🌐 To view results:")
        print(f"  Open {TEST_OUTPUT_DIR}/portfolio_website/index.html in your browser")
        
        if html_success:
            print("\n🎉 COMPREHENSIVE ANALYSIS COMPLETED SUCCESSFULLY!")
            print("✨ Real AWS Bedrock AI analysis with complete portfolio generation!")
            print("📊 Detailed feedback and recommendations provided!")
            return 0
        else:
            print("\n⚠️ Analysis completed but portfolio generation had issues.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Comprehensive analysis failed: {e}")
        logger.exception("Comprehensive analysis error")
        return 1


if __name__ == "__main__":
    sys.exit(main())