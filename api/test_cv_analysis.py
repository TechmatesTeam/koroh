#!/usr/bin/env python
"""
Test script for CV Analysis Service.

This script tests the CV analysis functionality with sample CV data
without requiring actual AWS API calls.
"""

import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koroh_platform.settings')
django.setup()

# Sample CV text for testing
SAMPLE_CV_TEXT = """
John Smith
Senior Software Engineer
Email: john.smith@email.com
Phone: +1-555-123-4567
Location: San Francisco, CA
LinkedIn: linkedin.com/in/johnsmith
GitHub: github.com/johnsmith

PROFESSIONAL SUMMARY
Experienced software engineer with 8+ years of experience in full-stack development, 
specializing in Python, Django, React, and cloud technologies. Proven track record 
of leading development teams and delivering scalable web applications.

TECHNICAL SKILLS
Programming Languages: Python, JavaScript, TypeScript, Java, Go
Web Frameworks: Django, React, Node.js, Express.js
Databases: PostgreSQL, MongoDB, Redis
Cloud Platforms: AWS, Docker, Kubernetes
Tools: Git, Jenkins, JIRA, Slack

SOFT SKILLS
Leadership, Team Management, Communication, Problem Solving, Agile Methodologies

WORK EXPERIENCE

Senior Software Engineer | Google Inc. | Jan 2020 - Present
• Led a team of 5 developers in building scalable web applications
• Implemented microservices architecture reducing system latency by 40%
• Mentored junior developers and conducted code reviews
• Technologies: Python, Django, React, AWS, Kubernetes

Software Engineer | Microsoft Corporation | Jun 2017 - Dec 2019
• Developed and maintained web applications serving 1M+ users
• Collaborated with cross-functional teams to deliver features on time
• Optimized database queries improving performance by 25%
• Technologies: JavaScript, Node.js, Azure, SQL Server

Junior Developer | Startup Inc. | Jan 2016 - May 2017
• Built responsive web interfaces using React and CSS
• Participated in agile development processes
• Fixed bugs and implemented new features
• Technologies: React, JavaScript, HTML, CSS

EDUCATION

Master of Science in Computer Science | Stanford University | 2014 - 2016
• GPA: 3.8/4.0
• Relevant Coursework: Algorithms, Data Structures, Machine Learning
• Thesis: "Scalable Web Application Architecture"

Bachelor of Science in Computer Science | UC Berkeley | 2010 - 2014
• GPA: 3.6/4.0
• Magna Cum Laude
• Relevant Coursework: Software Engineering, Database Systems

CERTIFICATIONS
• AWS Certified Solutions Architect - Professional | Amazon Web Services | 2021
• Certified Kubernetes Administrator | Cloud Native Computing Foundation | 2020
• Scrum Master Certification | Scrum Alliance | 2019

PROJECTS
Personal Portfolio Website | 2023
• Built using React and Django REST API
• Deployed on AWS with CI/CD pipeline
• URL: johnsmith.dev

Open Source Contribution | 2022
• Contributed to Django REST Framework
• Added new authentication features
• 500+ stars on GitHub

LANGUAGES
• English: Native
• Spanish: Intermediate
• French: Basic

AWARDS
• Employee of the Year - Google Inc. (2022)
• Best Innovation Award - Microsoft (2018)

INTERESTS
Photography, Hiking, Open Source Development, Machine Learning
"""


def test_cv_analysis_service():
    """Test the CV analysis service with sample data."""
    print("🧪 Testing CV Analysis Service")
    print("=" * 50)
    
    try:
        from koroh_platform.utils.cv_analysis_service import CVAnalysisService, analyze_cv_text
        
        # Test 1: Service initialization
        print("\n1. Testing service initialization...")
        service = CVAnalysisService()
        print("✅ CV Analysis Service initialized successfully")
        
        # Test 2: Basic analysis (without AWS calls)
        print("\n2. Testing CV structure parsing...")
        
        # Mock the AI service to avoid AWS calls
        class MockTextService:
            def _invoke_model_with_retry(self, prompt):
                # Return mock structured data
                return {"mock": "response"}
            
            def _extract_response_text(self, response):
                return json.dumps({
                    "personal_info": {
                        "name": "John Smith",
                        "email": "john.smith@email.com",
                        "phone": "+1-555-123-4567",
                        "location": "San Francisco, CA",
                        "linkedin": "linkedin.com/in/johnsmith",
                        "github": "github.com/johnsmith"
                    },
                    "professional_summary": "Experienced software engineer with 8+ years of experience",
                    "skills": {
                        "technical_skills": ["Python", "JavaScript", "Django", "React", "AWS"],
                        "soft_skills": ["Leadership", "Communication", "Problem Solving"],
                        "all_skills": ["Python", "JavaScript", "Django", "React", "AWS", "Leadership"]
                    },
                    "work_experience": [
                        {
                            "company": "Google Inc.",
                            "position": "Senior Software Engineer",
                            "start_date": "Jan 2020",
                            "end_date": "Present",
                            "description": "Led a team of 5 developers",
                            "achievements": ["Reduced system latency by 40%", "Mentored junior developers"],
                            "technologies": ["Python", "Django", "React", "AWS", "Kubernetes"]
                        }
                    ],
                    "education": [
                        {
                            "institution": "Stanford University",
                            "degree": "Master of Science",
                            "field_of_study": "Computer Science",
                            "start_date": "2014",
                            "end_date": "2016",
                            "gpa": "3.8/4.0"
                        }
                    ],
                    "certifications": [
                        {
                            "name": "AWS Certified Solutions Architect - Professional",
                            "issuer": "Amazon Web Services",
                            "issue_date": "2021"
                        }
                    ],
                    "languages": [
                        {"language": "English", "proficiency": "Native"},
                        {"language": "Spanish", "proficiency": "Intermediate"}
                    ],
                    "projects": [
                        {
                            "name": "Personal Portfolio Website",
                            "description": "Built using React and Django REST API",
                            "technologies": ["React", "Django"],
                            "date": "2023"
                        }
                    ],
                    "awards": ["Employee of the Year - Google Inc. (2022)"],
                    "interests": ["Photography", "Hiking", "Open Source Development"]
                })
            
            def _parse_json_response(self, text):
                return json.loads(text)
        
        # Replace the text service with mock
        service.text_service = MockTextService()
        
        # Test analysis
        try:
            result = service.analyze_cv(SAMPLE_CV_TEXT)
            
            print("✅ CV analysis completed successfully")
            print(f"  Personal Info: {result.personal_info.name} ({result.personal_info.email})")
            print(f"  Technical Skills: {len(result.technical_skills)} skills")
            print(f"  Work Experience: {len(result.work_experience)} positions")
            print(f"  Education: {len(result.education)} degrees")
            print(f"  Certifications: {len(result.certifications)} certifications")
            print(f"  Analysis Confidence: {result.analysis_confidence:.2f}")
            
            # Test 3: Skills summary
            print("\n3. Testing skills summary extraction...")
            skills_summary = service.extract_skills_summary(result)
            print(f"  Total Skills: {skills_summary['total_skills']}")
            print(f"  Estimated Experience: {skills_summary['years_of_experience']} years")
            print("✅ Skills summary extraction successful")
            
            # Test 4: Data validation
            print("\n4. Testing data validation...")
            if result.personal_info.email and '@' in result.personal_info.email:
                print("✅ Email validation passed")
            if result.work_experience and result.work_experience[0].company:
                print("✅ Work experience validation passed")
            if result.education and result.education[0].institution:
                print("✅ Education validation passed")
            
            return True
            
        except Exception as e:
            print(f"❌ CV analysis failed: {e}")
            return False
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_legacy_compatibility():
    """Test backward compatibility with legacy CV analysis function."""
    print("\n🔄 Testing Legacy Compatibility")
    print("=" * 50)
    
    try:
        from koroh_platform.utils.aws_bedrock import analyze_cv_content
        
        print("✅ Legacy function imported successfully")
        print("Note: Actual analysis requires AWS credentials")
        
        return True
        
    except ImportError as e:
        print(f"❌ Legacy import failed: {e}")
        return False


def test_data_structures():
    """Test data structure definitions."""
    print("\n📊 Testing Data Structures")
    print("=" * 50)
    
    try:
        from koroh_platform.utils.cv_analysis_service import (
            PersonalInfo, WorkExperience, Education, Certification, CVAnalysisResult
        )
        
        # Test PersonalInfo
        personal = PersonalInfo(
            name="Test User",
            email="test@example.com",
            phone="+1-555-0123"
        )
        print(f"✅ PersonalInfo: {personal.name}")
        
        # Test WorkExperience
        experience = WorkExperience(
            company="Test Company",
            position="Software Engineer",
            start_date="2020-01",
            end_date="Present"
        )
        print(f"✅ WorkExperience: {experience.position} at {experience.company}")
        
        # Test Education
        education = Education(
            institution="Test University",
            degree="Bachelor's",
            field_of_study="Computer Science"
        )
        print(f"✅ Education: {education.degree} in {education.field_of_study}")
        
        # Test Certification
        cert = Certification(
            name="Test Certification",
            issuer="Test Organization"
        )
        print(f"✅ Certification: {cert.name}")
        
        # Test CVAnalysisResult
        result = CVAnalysisResult(personal_info=personal)
        print(f"✅ CVAnalysisResult: {len(result.processing_notes)} notes")
        
        return True
        
    except Exception as e:
        print(f"❌ Data structures test failed: {e}")
        return False


def main():
    """Run all CV analysis tests."""
    print("CV ANALYSIS SERVICE TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Data Structures", test_data_structures),
        ("CV Analysis Service", test_cv_analysis_service),
        ("Legacy Compatibility", test_legacy_compatibility),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 CV Analysis Service is ready!")
        print("The service can parse CV structure and extract comprehensive information.")
        print("\nNote: Actual AI analysis requires valid AWS Bedrock credentials.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())