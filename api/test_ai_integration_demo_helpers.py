#!/usr/bin/env python
"""
Helper functions for AI Integration Demo
"""

def _format_highlights(highlights):
    """Format key highlights as HTML."""
    if not highlights:
        return ""
    
    html = '<div class="highlights"><h3>Key Highlights</h3><ul>'
    for highlight in highlights:
        html += f'<li>{highlight}</li>'
    html += '</ul></div>'
    return html


def _format_experience(experience):
    """Format experience entries as HTML."""
    if not experience:
        return '<div class="timeline-item"><div class="timeline-marker"></div><div class="timeline-content"><p>No experience data available.</p></div></div>'
    
    html = ""
    for exp in experience:
        company = exp.get('company', 'Company')
        position = exp.get('position', 'Position')
        duration = exp.get('duration', '')
        description = exp.get('enhanced_description', exp.get('description', ''))
        achievements = exp.get('key_achievements', exp.get('achievements', []))
        impact = exp.get('impact_summary', '')
        
        html += f'''
        <div class="timeline-item">
            <div class="timeline-marker"></div>
            <div class="timeline-content">
                <h3>{position}</h3>
                <h4>{company}</h4>
                <span class="timeline-date">{duration}</span>
                <p>{description}</p>
                {_format_achievements(achievements)}
                {f'<p class="impact-summary">{impact}</p>' if impact else ''}
            </div>
        </div>'''
    
    return html


def _format_achievements(achievements):
    """Format achievements as HTML."""
    if not achievements:
        return ""
    
    html = '<ul class="achievements">'
    for achievement in achievements[:4]:  # Limit to top 4
        html += f'<li>{achievement}</li>'
    html += '</ul>'
    return html


def _format_skills(skills):
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
                {_format_skill_items(skills_list)}
            </div>
            <div class="proficiency">{proficiency}</div>
        </div>'''
    
    return html


def _format_skill_items(skills_list):
    """Format individual skill items."""
    if not skills_list:
        return ""
    
    html = ""
    for skill in skills_list[:8]:  # Limit to 8 skills per category
        html += f'<span class="skill-tag">{skill}</span>'
    
    return html


def _format_education(education):
    """Format education entries as HTML."""
    if not education:
        return '<div class="education-item"><p>No education data available.</p></div>'
    
    html = ""
    for edu in education:
        institution = edu.get('institution', 'Institution')
        degree = edu.get('degree', 'Degree')
        field = edu.get('field', '')
        duration = edu.get('duration', '')
        details = edu.get('details', [])
        
        html += f'''
        <div class="education-item">
            <h3>{degree}</h3>
            <h4>{institution}</h4>
            {f'<p class="field">{field}</p>' if field else ''}
            <span class="education-date">{duration}</span>
            {_format_education_details(details)}
        </div>'''
    
    return html


def _format_education_details(details):
    """Format education details."""
    if not details:
        return ""
    
    html = '<ul class="education-details">'
    for detail in details:
        html += f'<li>{detail}</li>'
    html += '</ul>'
    return html


def _format_contact_details(contact, personal_info):
    """Format contact details as HTML."""
    email = contact.get('email') or personal_info.email
    phone = contact.get('phone') or personal_info.phone
    location = contact.get('location') or personal_info.location
    linkedin = contact.get('linkedin') or personal_info.linkedin
    github = contact.get('github') or personal_info.github
    website = contact.get('website') or personal_info.website
    
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
    
    if website:
        website_url = website if website.startswith('http') else f'https://{website}'
        html += f'<div class="contact-item"><i class="fas fa-globe"></i><a href="{website_url}" target="_blank">Website</a></div>'
    
    return html