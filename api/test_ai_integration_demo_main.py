#!/usr/bin/env python
"""
AI Service Integration Demo - Main Execution

This demo creates a complete AI-generated portfolio without requiring AWS credentials.
It demonstrates the full workflow that would be used with real AWS Bedrock integration.
"""

import os
import sys
import django
import json
from pathlib import Path
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koroh_platform.settings')
django.setup()

# Import demo functions
from test_ai_integration_demo import create_mock_cv_analysis, create_mock_portfolio_content
from test_ai_integration_demo_helpers import (
    _format_highlights, _format_experience, _format_skills, 
    _format_education, _format_contact_details
)

# Test configuration
TEST_OUTPUT_DIR = Path("test_portfolio_output")


def generate_complete_portfolio(portfolio, cv_data):
    """Generate a complete professional HTML portfolio."""
    print("\n🌐 Generating Complete Professional Portfolio")
    print("=" * 70)
    
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
        experience = portfolio.experience_section
        skills = portfolio.skills_section
        education = portfolio.education_section
        contact = portfolio.contact_section
        
        # Generate HTML with all sections
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - Professional Portfolio</title>
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
                    {_format_highlights(about.get('key_highlights', []))}
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
                {_format_experience(experience)}
            </div>
        </div>
    </section>

    <!-- Skills Section -->
    <section id="skills" class="skills">
        <div class="container">
            <h2 class="section-title">Skills & Expertise</h2>
            <div class="skills-grid">
                {_format_skills(skills)}
            </div>
            <div class="skills-summary">
                <p>{skills.get('skills_summary', 'Comprehensive skill set with proven expertise.')}</p>
            </div>
        </div>
    </section>

    <!-- Education Section -->
    <section id="education" class="education">
        <div class="container">
            <h2 class="section-title">Education</h2>
            <div class="education-grid">
                {_format_education(education)}
            </div>
        </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="contact">
        <div class="container">
            <h2 class="section-title">Get In Touch</h2>
            <div class="contact-content">
                <div class="contact-info">
                    <p class="contact-cta">{contact.get('call_to_action', 'Feel free to reach out for opportunities or collaborations!')}</p>
                    <div class="contact-details">
                        {_format_contact_details(contact, cv_data.personal_info)}
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
            <p>&copy; 2024 {name}. Generated by Koroh AI Platform.</p>
            <p>This portfolio demonstrates AI-powered content generation and modern web technologies.</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>'''
        
        # Save HTML file
        html_file = portfolio_dir / "index.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Copy CSS and JS from existing files or create them
        create_portfolio_assets(portfolio_dir)
        
        # Create comprehensive README
        readme_content = f'''# {name} - AI Generated Professional Portfolio

This portfolio was automatically generated by the Koroh AI Platform to demonstrate the complete AI-powered workflow for CV analysis and portfolio generation.

## 🚀 Demo Features

- **AI-Powered Content**: All content generated using simulated AWS Bedrock processing
- **Professional Design**: Modern, responsive design with smooth animations  
- **Complete Workflow**: Demonstrates CV analysis → Content generation → HTML portfolio
- **Interactive Elements**: Smooth scrolling, mobile menu, contact form
- **Production Ready**: Professional-quality output suitable for real use

## 📊 Generation Results

- **CV Analysis Confidence**: {cv_data.analysis_confidence:.0%}
- **Portfolio Quality Score**: {portfolio.content_quality_score:.0%}
- **Sections Generated**: 6/6 (Hero, About, Experience, Skills, Education, Contact)
- **Content Style**: {portfolio.style_used.title()} tone optimized for {getattr(portfolio, 'target_audience', 'professionals')}

## 🌐 How to View

1. **Direct**: Open `index.html` in any modern web browser
2. **Local Server** (recommended):
   ```bash
   python -m http.server 8000
   # Then open http://localhost:8000
   ```

## 🎯 What This Demonstrates

This portfolio showcases the complete Koroh AI integration:

1. **CV Analysis**: Extracted structured data from CV content
2. **Content Generation**: Created professional, engaging portfolio content
3. **Template Application**: Applied modern, responsive web design
4. **Quality Assurance**: Ensured high-quality, professional output

## 📁 Generated Files

- `index.html` - Complete portfolio webpage ({html_file.stat().st_size:,} bytes)
- `styles.css` - Professional CSS styling
- `script.js` - Interactive JavaScript functionality
- `README.md` - This documentation

## 🛠 Technical Implementation

- **HTML5**: Semantic markup with accessibility features
- **CSS3**: Modern styling with animations and responsive design
- **JavaScript**: Smooth interactions and mobile-friendly navigation
- **Performance**: Optimized for fast loading and smooth user experience

---

**Generated by Koroh AI Platform**  
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
Workflow: CV Analysis → AI Content Generation → Professional Portfolio  
Status: ✅ Complete and Ready for Use
'''
        
        readme_file = portfolio_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print("✅ Complete professional portfolio generated successfully!")
        print(f"📁 Portfolio location: {portfolio_dir.absolute()}")
        print(f"🌐 Open {html_file.absolute()} in your browser to preview")
        
        return True
        
    except Exception as e:
        print(f"❌ Portfolio generation failed: {e}")
        return False


def create_portfolio_assets(portfolio_dir):
    """Create CSS and JavaScript assets for the portfolio."""
    
    # CSS content (simplified for demo)
    css_content = '''/* Professional Portfolio CSS */
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
}

.hero-subtitle {
    font-size: 1.5rem;
    margin-bottom: 1rem;
    opacity: 0.9;
}

.hero-description {
    font-size: 1.1rem;
    margin-bottom: 2rem;
    opacity: 0.8;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
}

.hero-buttons {
    display: flex;
    gap: 1rem;
    justify-content: center;
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
    position: relative;
    max-width: 800px;
    margin: 0 auto;
}

.timeline-item {
    position: relative;
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
    
    # JavaScript content
    js_content = '''// Professional Portfolio JavaScript
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
            
            alert(`Thank you ${name}! This is a demo portfolio - your message would be sent in a real implementation.`);
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
});'''
    
    # Save CSS and JS files
    css_file = portfolio_dir / "styles.css"
    js_file = portfolio_dir / "script.js"
    
    with open(css_file, 'w', encoding='utf-8') as f:
        f.write(css_content)
    
    with open(js_file, 'w', encoding='utf-8') as f:
        f.write(js_content)


def save_test_results(cv_data, portfolio):
    """Save test results for analysis."""
    TEST_OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Save CV analysis results
    cv_file = TEST_OUTPUT_DIR / "cv_analysis_results.json"
    with open(cv_file, 'w') as f:
        json.dump({
            'personal_info': {
                'name': cv_data.personal_info.name,
                'email': cv_data.personal_info.email,
                'phone': cv_data.personal_info.phone,
                'location': cv_data.personal_info.location,
                'linkedin': cv_data.personal_info.linkedin,
                'github': cv_data.personal_info.github,
                'website': cv_data.personal_info.website
            },
            'professional_summary': cv_data.professional_summary,
            'technical_skills_count': len(cv_data.technical_skills),
            'work_experience_count': len(cv_data.work_experience),
            'education_count': len(cv_data.education),
            'certifications_count': len(cv_data.certifications),
            'analysis_confidence': cv_data.analysis_confidence,
            'extracted_sections': cv_data.extracted_sections
        }, indent=2)
    
    # Save portfolio content
    portfolio_file = TEST_OUTPUT_DIR / "portfolio_content.json"
    with open(portfolio_file, 'w') as f:
        json.dump({
            'template_used': portfolio.template_used,
            'style_used': portfolio.style_used,
            'content_quality_score': portfolio.content_quality_score,
            'hero_section': portfolio.hero_section,
            'about_section': portfolio.about_section,
            'experience_entries': len(portfolio.experience_section),
            'skill_categories': len(portfolio.skills_section.get('skill_categories', {})),
            'education_entries': len(portfolio.education_section),
            'contact_info_complete': bool(portfolio.contact_section.get('email'))
        }, indent=2)


def main():
    """Main demo execution."""
    print("🚀 KOROH AI SERVICE INTEGRATION DEMO")
    print("=" * 80)
    print("Demonstrating complete AI-powered CV analysis and portfolio generation workflow")
    print("=" * 80)
    
    # Step 1: Create mock CV analysis (simulating AWS Bedrock)
    cv_data, cv_success = create_mock_cv_analysis()
    
    # Step 2: Create mock portfolio content (simulating AWS Bedrock)
    portfolio_data, portfolio_success = create_mock_portfolio_content(cv_data)
    
    # Step 3: Generate complete HTML portfolio
    html_success = generate_complete_portfolio(portfolio_data, cv_data)
    
    # Step 4: Save test results
    if cv_data and portfolio_data:
        save_test_results(cv_data, portfolio_data)
    
    # Summary
    print("\n" + "=" * 80)
    print("🎯 DEMO SUMMARY")
    print("=" * 80)
    
    tests = [
        ("CV Analysis Simulation", cv_success),
        ("Portfolio Content Generation", portfolio_success),
        ("HTML Portfolio Creation", html_success)
    ]
    
    passed = 0
    for test_name, result in tests:
        status = "✅ SUCCESS" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} steps completed successfully")
    
    if passed == len(tests):
        print("\n🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("✨ Complete AI workflow demonstrated!")
        print(f"\n📁 Generated Files:")
        print(f"  • CV Analysis: {TEST_OUTPUT_DIR}/cv_analysis_results.json")
        print(f"  • Portfolio Content: {TEST_OUTPUT_DIR}/portfolio_content.json")
        print(f"  • HTML Portfolio: {TEST_OUTPUT_DIR}/portfolio_website/")
        print(f"\n🌐 To view the generated portfolio:")
        print(f"  Open {TEST_OUTPUT_DIR}/portfolio_website/index.html in your browser")
        print(f"\n💡 This demonstrates the complete workflow that would be used with real AWS Bedrock integration!")
    else:
        print(f"\n⚠️ {len(tests) - passed} step(s) failed.")
    
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())