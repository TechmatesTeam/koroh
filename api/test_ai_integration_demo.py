#!/usr/bin/env python
"""
AI Service Integration Demo for Koroh Platform

This demo shows the AI integration workflow by:
1. Using mock CV analysis results (simulating AWS Bedrock)
2. Using mock portfolio generation (simulating AWS Bedrock)
3. Creating actual HTML/CSS/JavaScript portfolio files for preview

This demonstrates the complete workflow without requiring AWS credentials.
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


def create_mock_cv_analysis():
    """Create mock CV analysis results to simulate AWS Bedrock processing."""
    print("🧠 Creating Mock CV Analysis Results (Simulating AWS Bedrock)")
    print("=" * 70)
    
    try:
        from koroh_platform.utils.cv_analysis_service import (
            CVAnalysisResult, PersonalInfo, WorkExperience, Education, Certification
        )
        
        # Create realistic mock data as if processed by AWS Bedrock
        personal_info = PersonalInfo(
            name="Alex Chen",
            email="alex.chen@email.com",
            phone="+1-555-123-4567",
            location="San Francisco, CA",
            linkedin="linkedin.com/in/alexchen",
            github="github.com/alexchen",
            website="alexchen.dev"
        )
        
        work_experience = [
            WorkExperience(
                company="TechCorp Inc.",
                position="Senior Full-Stack Developer",
                start_date="Jan 2021",
                end_date="Present",
                duration="3+ years",
                description="Led development of microservices architecture serving 500K+ daily active users",
                achievements=[
                    "Increased system performance by 60% through optimization",
                    "Led team of 5 developers and mentored junior staff",
                    "Implemented CI/CD pipelines reducing deployment time"
                ],
                technologies=["React", "Node.js", "PostgreSQL", "AWS", "Docker"]
            ),
            WorkExperience(
                company="StartupXYZ",
                position="Full-Stack Developer",
                start_date="Jun 2019",
                end_date="Dec 2020",
                duration="1.5 years",
                description="Developed MVP for fintech application from concept to production",
                achievements=[
                    "Built application handling $2M+ in transactions",
                    "Optimized database queries improving performance by 40%",
                    "Collaborated with design team on responsive UI/UX"
                ],
                technologies=["Vue.js", "Django", "PostgreSQL", "Stripe API"]
            )
        ]
        
        education = [
            Education(
                institution="Stanford University",
                degree="Master of Science",
                field_of_study="Computer Science",
                start_date="2015",
                end_date="2017",
                gpa="3.8/4.0",
                honors="Magna Cum Laude"
            ),
            Education(
                institution="UC Berkeley",
                degree="Bachelor of Science",
                field_of_study="Computer Science",
                start_date="2011",
                end_date="2015",
                gpa="3.6/4.0"
            )
        ]
        
        certifications = [
            Certification(
                name="AWS Certified Solutions Architect",
                issuer="Amazon Web Services",
                issue_date="2022"
            ),
            Certification(
                name="Certified Kubernetes Administrator",
                issuer="Cloud Native Computing Foundation",
                issue_date="2021"
            )
        ]
        
        # Create comprehensive CV analysis result
        cv_result = CVAnalysisResult(
            personal_info=personal_info,
            professional_summary="Experienced full-stack developer with 7+ years of expertise in building scalable web applications. Specialized in React, Node.js, Python, and cloud technologies with proven track record of leading development teams.",
            skills=["JavaScript", "Python", "React", "Node.js", "PostgreSQL", "AWS", "Docker", "Leadership"],
            technical_skills=["JavaScript", "TypeScript", "Python", "React", "Vue.js", "Node.js", "Django", "PostgreSQL", "MongoDB", "AWS", "Docker", "Kubernetes"],
            soft_skills=["Leadership", "Team Collaboration", "Problem Solving", "Mentoring", "Agile Methodologies"],
            work_experience=work_experience,
            education=education,
            certifications=certifications,
            languages=[
                {"language": "English", "proficiency": "Native"},
                {"language": "Mandarin", "proficiency": "Native"},
                {"language": "Spanish", "proficiency": "Intermediate"}
            ],
            projects=[
                {
                    "name": "E-Commerce Platform",
                    "description": "Built full-stack e-commerce solution with React and Node.js",
                    "technologies": ["React", "Node.js", "PostgreSQL", "AWS"],
                    "date": "2023",
                    "url": "github.com/alexchen/ecommerce-platform"
                },
                {
                    "name": "Real-Time Chat Application",
                    "description": "Developed WebSocket-based chat application with encryption",
                    "technologies": ["React", "Socket.io", "Node.js", "MongoDB"],
                    "date": "2022"
                }
            ],
            awards=["Employee of the Year - TechCorp Inc. (2023)", "Best Innovation Award - StartupXYZ (2020)"],
            interests=["Photography", "Rock Climbing", "Open Source Development", "AI/Machine Learning"],
            analysis_confidence=0.95,
            extracted_sections=["personal_info", "summary", "experience", "skills", "education", "certifications"],
            processing_notes=["High confidence analysis", "All major sections identified", "Comprehensive data extraction"]
        )
        
        print("✅ Mock CV analysis created successfully")
        print(f"  Name: {cv_result.personal_info.name}")
        print(f"  Technical Skills: {len(cv_result.technical_skills)}")
        print(f"  Work Experience: {len(cv_result.work_experience)} positions")
        print(f"  Education: {len(cv_result.education)} degrees")
        print(f"  Analysis Confidence: {cv_result.analysis_confidence:.2f}")
        
        return cv_result, True
        
    except Exception as e:
        print(f"❌ Mock CV analysis creation failed: {e}")
        logger.exception("Mock CV analysis error")
        return None, False


def create_mock_portfolio_content(cv_data):
    """Create mock portfolio content to simulate AWS Bedrock generation."""
    print("\n🎨 Creating Mock Portfolio Content (Simulating AWS Bedrock)")
    print("=" * 70)
    
    try:
        from koroh_platform.utils.portfolio_generation_service import PortfolioContent
        
        if not cv_data:
            print("❌ No CV data available")
            return None, False
        
        # Create realistic portfolio content as if generated by AWS Bedrock
        portfolio = PortfolioContent(
            hero_section={
                "headline": "Senior Full-Stack Developer & Technology Leader",
                "subheadline": "Building scalable web applications that serve millions of users",
                "value_proposition": "7+ years of expertise in modern web technologies with proven track record of leading high-performing development teams",
                "call_to_action": "Let's build something amazing together"
            },
            about_section={
                "main_content": "I'm a passionate full-stack developer who thrives on solving complex technical challenges and building products that make a real impact. With over 7 years of experience at leading tech companies, I've learned that the best software comes from understanding both user needs and business objectives.\n\nMy approach combines technical excellence with collaborative leadership, always focusing on scalable solutions that drive measurable results. I enjoy mentoring other developers and contributing to the broader tech community through open source projects.",
                "key_highlights": [
                    "Led development of systems serving 500K+ daily active users",
                    "Improved system performance by 60% through strategic optimizations",
                    "Successfully mentored and led cross-functional teams of 5+ developers",
                    "Built fintech applications handling $2M+ in secure transactions"
                ],
                "personal_touch": "When I'm not coding, you'll find me rock climbing in the Bay Area or contributing to open source projects that help other developers."
            },
            experience_section=[
                {
                    "company": "TechCorp Inc.",
                    "position": "Senior Full-Stack Developer",
                    "duration": "Jan 2021 - Present",
                    "enhanced_description": "Spearheaded the development of a microservices architecture that revolutionized our platform's scalability, enabling us to serve over 500,000 daily active users with 99.9% uptime. Led cross-functional initiatives that resulted in significant performance improvements and streamlined development processes.",
                    "key_achievements": [
                        "Architected and implemented microservices infrastructure serving 500K+ daily users",
                        "Boosted system performance by 60% through strategic code optimization and caching",
                        "Led and mentored a team of 5 developers, fostering a culture of technical excellence",
                        "Established CI/CD pipelines that reduced deployment time from hours to minutes"
                    ],
                    "skills_demonstrated": ["React", "Node.js", "PostgreSQL", "AWS", "Docker", "Team Leadership", "System Architecture"],
                    "impact_summary": "Transformed platform scalability and team productivity through technical leadership and innovative solutions."
                },
                {
                    "company": "StartupXYZ",
                    "position": "Full-Stack Developer",
                    "duration": "Jun 2019 - Dec 2020",
                    "enhanced_description": "Played a pivotal role in building a fintech MVP from the ground up, taking it from concept to production while ensuring security, scalability, and user experience excellence. Collaborated closely with product and design teams to deliver features that directly contributed to business growth.",
                    "key_achievements": [
                        "Developed secure fintech application processing $2M+ in transactions",
                        "Optimized database performance by 40% through query optimization and indexing",
                        "Collaborated with design team to create intuitive, responsive user interfaces",
                        "Implemented robust payment processing integration with multiple providers"
                    ],
                    "skills_demonstrated": ["Vue.js", "Django", "PostgreSQL", "Stripe API", "Payment Processing", "Security"],
                    "impact_summary": "Delivered mission-critical fintech features that enabled secure, large-scale transaction processing."
                }
            ],
            skills_section={
                "skill_categories": {
                    "Frontend Development": {
                        "name": "Frontend Development",
                        "skills": ["React", "Vue.js", "TypeScript", "HTML5", "CSS3", "Responsive Design"],
                        "proficiency": "Expert"
                    },
                    "Backend Development": {
                        "name": "Backend Development",
                        "skills": ["Node.js", "Django", "Python", "RESTful APIs", "GraphQL", "Microservices"],
                        "proficiency": "Expert"
                    },
                    "Database & Cloud": {
                        "name": "Database & Cloud Technologies",
                        "skills": ["PostgreSQL", "MongoDB", "Redis", "AWS", "Docker", "Kubernetes"],
                        "proficiency": "Advanced"
                    },
                    "Leadership & Soft Skills": {
                        "name": "Leadership & Communication",
                        "skills": ["Team Leadership", "Mentoring", "Agile Methodologies", "Code Review", "Technical Writing"],
                        "proficiency": "Expert"
                    }
                },
                "top_skills": ["JavaScript", "React", "Node.js", "Python", "AWS", "Team Leadership"],
                "skills_summary": "Comprehensive full-stack expertise spanning modern web technologies, cloud infrastructure, and team leadership with proven ability to deliver scalable solutions in fast-paced environments."
            },
            education_section=[
                {
                    "institution": "Stanford University",
                    "degree": "Master of Science in Computer Science",
                    "field": "Computer Science",
                    "duration": "2015 - 2017",
                    "details": ["GPA: 3.8/4.0", "Magna Cum Laude", "Thesis: Scalable Web Application Architecture"]
                },
                {
                    "institution": "UC Berkeley",
                    "degree": "Bachelor of Science in Computer Science",
                    "field": "Computer Science", 
                    "duration": "2011 - 2015",
                    "details": ["GPA: 3.6/4.0", "Dean's List (2014, 2015)"]
                }
            ],
            contact_section={
                "email": cv_data.personal_info.email,
                "phone": cv_data.personal_info.phone,
                "location": cv_data.personal_info.location,
                "linkedin": cv_data.personal_info.linkedin,
                "github": cv_data.personal_info.github,
                "website": cv_data.personal_info.website,
                "call_to_action": "I'm always excited to discuss new opportunities and innovative projects. Whether you're looking for technical leadership, full-stack development expertise, or someone passionate about building great products, I'd love to connect!"
            },
            template_used="professional",
            style_used="formal",
            content_quality_score=0.92
        )
        
        print("✅ Mock portfolio content created successfully")
        print(f"  Template: {portfolio.template_used}")
        print(f"  Style: {portfolio.style_used}")
        print(f"  Quality Score: {portfolio.content_quality_score:.2f}")
        print(f"  Hero headline: {portfolio.hero_section['headline'][:50]}...")
        print(f"  About content: {len(portfolio.about_section['main_content'])} characters")
        print(f"  Experience entries: {len(portfolio.experience_section)}")
        print(f"  Skill categories: {len(portfolio.skills_section['skill_categories'])}")
        
        return portfolio, True
        
    except Exception as e:
        print(f"❌ Mock portfolio creation failed: {e}")
        logger.exception("Mock portfolio creation error")
        return None, False


def generate_professional_html_portfolio(portfolio, cv_data):
    """Generate a professional HTML portfolio with modern design."""
    print("\n🌐 Generating Professional HTML Portfolio")
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
        
        # Generate comprehensive HTML
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
                <p>{skills.get('skills_summary', 'Comprehensive skilllseurn Fa       ret
  error")rationlio gene PortfoML"HTeption(excogger.)
        l: {e}"ledon faio generatiML Portfoliint(f"❌ HT  pr:
       eception as  except Ex    
  False
      return           sing")
 misiles areired fome requ"❌ S   print(:
          else       rn True
        retu            
es")
    {size:,} byte}: f"  ✅ {fil  print(             t_size
 .stat().spathsize = file_      
          ileolio_dir / f= portfth    file_pa     s:
        red_filee in requifor fil       s:")
     ted Filenera"\n📋 Get(      prin      les_exist:
_fi  if all    
      )
    ilesquired_f file in re() forstsxi file).efolio_dir /l((portalles_exist =    all_fi    ]
 md', 'README.ipt.js'crcss', 'ses.tml', 'styl['index.hs = ile required_f    iles
    fgenerated# Validate    
           ")
  atione documentetmplte()} for co.absolueadme_file📖 See {r print(f"")
        preview browser to} in youre()ile.absolutn {html_ft(f"🌐 Operin   p   
  solute()}")r.abfolio_diortocation: {polio lrtfPorint(f"📁  p)
       !"sfullyed succeseratfolio genl HTML portsiona Profesint("✅  pr          
  
  ntent)coeadme_ f.write(r      
     as f:utf-8') encoding='_file, 'w', eadmepen(r     with oE.md"
   "READMolio_dir /  = portfe_file     readm  
      '
   .0
'' v1 PortfolioProfessionalmplate: Teocessing  
k AI Pr Bedrocimulated AWSechnology: S:%S")}  
T %H:%MY-%m-%de("%strftimme.now(). {datetie:rm**  
DatI Platfoh Aated by Koroener*G---

*t.js`

cripnality in `snctiong new fus`
- Addiles.csstyles in `d stylors an co
- Modifyinghtml` in `index.tentting con
- Ediized by:ily custom can be easfolio porttion

Thestomiza

## 🔧 Cuge 79+ 12+
- Ed+
- Safari 55- Firefox60+
me Chro
- patibility
rowser Com

## 📱 Bsenceline pressional onprofewanting a Anyone tunities
- new opporls seeking  professionaologyers
- Technhnical leadnd tec managers aoducteers
- Prrs and engine develope
- Softwarect for:te is perfplaolio temhis portf
TUse Cases

## 🎯 proach
 design apile-firste**: Mobsiv
- **Respon iconsmeesoont Aw) and F (Intergle Fonts: Goo**Fonts**formance
- mal peror optila JS f: Vanilpt**- **JavaScrid Grid
x anith Flexbon styling w Moder**: **CSS3s
-aturessibility fewith acceic markup : Semant**

- **HTML5 Stack 🛠 Technical##ers

itecruzed for rtyle optimiFormal s*:  Tone*nal*Professio
- *n, Contact)catio Skills, Edurience, About, Expe6 (Hero,ated**: 6/ner Geions **Sect: 92%
-ity Score**ual*Content Q 95%
- **:onfidence*sis CAnalyy

- **ualittent QCon# 📊 ontent

#, engaging clityd high-quan**: EnsuretiomizaQuality Optie
4. **n templatsigweb deed modern *: Applipplication**Template A
3. *lio contentonal portfo professi Created**:t Generation**Conten. 
2contentom CV d data frructureExtracted stAnalysis**: CV 
1. **flow:
roh AI work complete Kos theemonstratelio drtfohis porocess

T Pneration## 🤖 AI Germation

tact info conns forAwesome ico Font Icons**:**y
- d hierarchng anpaci sroper pstem with syrid*: Clean gout*ons
- **Laysitianver tr and hon effectse-iooth fads**: Sm **Animationons
-cti white seh clean witentlue gradifessional bro Pcheme**: S **Color
-ncenal appearafessioy for pro font famil: Interphy**n Typograer
- **Mods
 Featuresign
## 🎨 De8000
ost:tp://localhpen ht Then o   ```
  :8000
ostp -S localhg PHP
   ph# Usin   
   r
http-serve
   npx e.js # Using Nod0
   
  server 800 -m http.
   pythonon 3 Using Pyth``bash
   #
   `xperience): eor bested fcommendreer** (cal Servr
2. **Lon web browseder` in any modex.htmlpen `inwing**: Ocal VieLoew

1. **Vi🌐 How to file

## ntation his docume` - TEADME.md `Rence
-er experimooth usnd s ativity interacaScript forjs` - Javipt.ions
- `scrmatd ani design andernS with moCSl sionass` - Profes `styles.ct
-contenlete ith comp wgetfolio webpaain por` - Mtml.h

- `index## 📁 Filese sizes

icfor all devOptimized e**: e Responsiv **Mobiltact
-n, Conioducat Es,ence, Skill, ExperiAbouts**: Hero, ve SectionComprehensirm
- **t fo contacmobile menu,tion, igaing navoth scrollnts**: Smoactive Eleme**Interimations
-  an smoothesign with desponsivedern, rign**: Mosional Desfes*Prong
- *ock processited AWS Bedrg simulad usinategenerontent was t**: All cntenred CoPowe

- **AI- Featuresion.

## 🚀 generatnd portfolionalysis a a for CVlowrkfered woAI-powhe complete ate t to demonstrPlatformoroh AI  the Ked byatally genermaticwas autortfolio 

This pooliosional Portfated Profes} - AI Gener{namet = f'''# ontendme_creaE
         READMiverehensCreate comp #              
 _content)
 (jsitef.wr        f:
     f-8') asencoding='ut, 'w', open(js_fileth       wi     
  ent)
   te(css_contwri   f.         -8') as f:
ng='utf'w', encodiss_file, (copenth     wi 
    t)
       html_conten   f.write(
         ) as f:utf-8'coding='ile, 'w', entml_fn(hith ope      w
          js"
ript.dir / "sc portfolio_ js_file ="
       les.css "styir /ortfolio_dcss_file = p   "
     ml.ht / "indexio_dirle = portfoll_fi        htmiles
 # Save f   
       
     );'''    });
}
      }  ;
ection)serve(server.obbs      o
      ease';s  0.6sformtrans ease, opacity 0.6ion = 'sittyle.trantion.s    sec     px)';
   (20translateYm = 'orransfe.ton.stylti        sec   = '0';
  .opacityyle  section.st   n
        sectioip hero Ske') { // !== 'hom.id (section       if=> {
 ach(section ons.forE  section');
  ll('sectiSelectorAent.querys = documectionconst s
    ionsmatfor anions  sective/ Obser    /);

verOptions  }, obser
         });   }
        ';
  anslateY(0)= 'tr.transform et.stylery.targnt   e          ';
    '1le.opacity =.styentry.target              
  rsecting) {ntry.isInte     if (e  => {
     ntry ach(es.forEie       entr {
 (entries)ver(functionsectionObser new Interbserver =  const o
  
x'
    }; 0ppx 0px -50pxotMargin: '0      ro
  .1,hold: 0    thres= {
    ions  observerOpt    const
 animationsrollSc
    // );
 }    });
   
           }e');
     t.add('activnk.classLis          li) {
      ' + current= '#') ==efhr('tributetAtink.ge  if (l        
  ('active');ist.removelink.classL           
 k => {ch(lininks.forEa        navL    });

   }
            ;
 e('id')Attributgetction.t = seenrr  cu               {
00))onTop - 2tiY >= (secf (scroll   i        ;
 tHeightienion.clt = sectnHeighconst sectio          op;
  .offsetTonecti s =ctionToponst se           c> {
 ion =rEach(sections.fo       sect';
 rrent = 'let cu        
    k');
    inav-lectorAll('.nt.querySelmenocus = dt navLink   cons');
     ctionll('sectorAerySelent.quocumeons = dst secti   con
      {ction()croll', fun'sListener(w.addEvent
    windotinghighlighion gatActive navi    //   }

  });
  ;
      reset()     this.      
 set form     // Re   
        );
        essage.`ur msend yo would thismentation, le a real imp - inioo portfols a dem This i received.has beenr message You}! ou ${nameert(`Thank y          alission
   subm formlate// Simu  
              
               }
     n;ur      ret    .');
      ieldsn all fse fill ilert('Plea    a          ssage) {
  | !me || !email | (!name      if      ation
imple valid      // S      
          
  ');get('messageormData.sage = f mesonst  c      );
    ('email'Data.getrml = foonst emai    c      );
  a.get('name'at = formDme   const na
         is);a(thrmDatFow  neata =formD const           
          t();
   entDefaulrev.p   e    (e) {
     tionmit', functener('subdEventLisorm.ad contactF    
   orm) {tF if (contac);
   orm'tactFd('conementByIt.getEl documenactForm =nst cont
    coorm handling/ Contact f
    /    }
   });

     );ctive'.toggle('assListnavMenu.cla          );
  'active'toggle(st.rger.classLiambu h          {
 on()  functiner('click',ister.addEventL    hamburge    vMenu) {
 naer &&urg if (hamb      
 v-menu');
r('.naSelectouery= document.qMenu nst nav  co;
  .hamburger')ySelector('erment.quurger = docu  const hamb  nu toggle
/ Mobile me    /   });

 });
      }
            });
                t'
  block: 'star               
     oth',smohavior: '     be          ew({
     ollIntoViion.scrgetSect         tar {
       rgetSection)    if (ta     
   etId);(targerySelectorment.quction = docutSegeconst tar            );
ef'te('hrtAttribu.geisargetId = th  const t
          Default();   e.prevent     
    (e) {tionk', funcener('clicntListlink.addEve      > {
  h(link =nks.forEac  navLi');
  av-linkectorAll('.nSelment.queryocuavLinks = donst n   cinks
 navigation lr ng foth scrollimoo
    // Stion() {ed', funcMContentLoader('DOentListencument.addEvaScript
doJavio nal Portfolssio Profetent = '''//onjs_c        ript
ate JavaScner  # Ge   
      '
     }''m;
    }
  gap: 2re
      fr;: 1te-columnsrid-templa{
        gntent act-co
    .cont
    ;
    } !important2px left: 1    arker {
   imeline-m   
    .t  }
 ;
  rtantmpo: 0 !i-rightdingad      p
  tant;m !imporng-left: 3re       paddiortant;
 impt: 0 ! lef       dth: 100%;
  wim {
      meline-ite  .ti
    
  px;
    }   left: 20
     e {ine:befor  .timel}
    
  deg);
     rotate(-45ateY(-8px)ranslm: tfor       trans{
 3) d(:nth-chilve .barmburger.acti
    .ha   }
    5deg);
 e(4 rotatteY(8px)transla: sform      tranild(1) {
  bar:nth-cher.active ..hamburg    }
    
 ;
   pacity: 0  o     
 -child(2) {nthe .bar:rger.activambu    .h  

    }
  : flex;lay       disp {
 burger   .ham    
   }
em 0;
    margin: 1r   
   nu li {nav-me
    . }
    eft: 0;
   
        lactive {nu. .nav-me
     }
    
   0; 2remng:      paddi);
  , 0, 0, 0.057px rgba(0ow: 0 10px 2ox-shad  b;
      sition: 0.3s     tran  
 : center; text-align
       100%;    width: white;
    color: d-oungr    back   mn;
  coluection:x-dir fle;
         top: 70px
      t: -100%;ef     l  
  fixed; position:     
   {.nav-menu
    
        }er;
items: cent    align-   lumn;
 tion: colex-direc
        f {ttonsro-bu  
    .he
  rem;
    }nt-size: 2.5   fo {
     tle   .hero-ti 768px) {
 max-width: (media
@Design */ive ons* Resp
/
}

    }teY(0);anslaansform: tr
        trity: 1;pac{
        o to }
     30px);
  teY(la: trans  transform   ;
   ty: 0   opacirom {
        fUp {
 Indes faeyframe */
@kimations
/* Anm 0;
}
: 2reing   paddnter;
 n: ce text-alig
   white;olor: 172a;
    c: #0f  backgroundfooter {
  er */
.}

/* Foot);
5, 255, 0.7a(255, 25olor: rgb    clder {
ceho:platextarea:group .form-er,
placeholdt::-group inpu

.form 1rem;
}size:;
    font-olor: white;
    c0.1) 255, 255, : rgba(255,ackground  bpx;
  adius: 5  border-r
   none;der:   bor1rem;
 : 
    paddingth: 100%;
    widrea {ta-group tex
.formp input,orm-grou
.frem;
}
m: 1.5in-botto
    marg {roupm-g.for0px;
}

ius: 1der-rad;
    borng: 2rem    paddi
1);55, 0.255, 2gba(255, ckground: r    baorm {
ontact-form */
.cct F

/* Conta;
}: #3b82f6 color{
   r em a:hoventact-itcoase;
}

. 0.3s etion: color  transi;
  n: noneoratioxt-decite;
    tecolor: wh
    m a {iteontact-6;
}

.c82f color: #3b  20px;
 : 
    widthi {t-item ntac
}

.co1rem;: ap
    gems: center;it
    align-lay: flex; {
    dispontact-item

.cm;
}p: 1re   ga;
 columnon: directilex-flex;
    f: 
    displays {ntact-detail

.co9;
}city: 0.
    opaom: 2rem;gin-bott;
    marze: 1.1remnt-si fo
   -cta {ontact
}

.cuto;: 0 a
    margin000px;dth: 1-wi   max
 em;  gap: 4r1fr 1fr;
  umns: template-col   grid-y: grid;
 
    displact-content {nta
}

.co;iteor: wh   col
 e {titlction-ct .se

.contate;
}hi color: w1e293b;
   ground: # {
    backcontactction */
.Contact Se
/* 
}
48b; #647
    color:m 0;25reg: 0.
    paddindetails li {on-ducatie;
}

.eyle: non   list-st 1rem;
 n-top:
    margin-details {
.educatio00;
}
ight: 5t-wem;
    fonsize: 0.9re;
    font-or: #94a3b8 col-date {
   .education
}

 0.5rem;m:ottomargin-b4748b;
     #6  color:
  ic;tyle: ital   font-s
 ield {}

.f0.5rem;
om: bott   margin-;
  #64748br:
    colotem h4 {n-iio

.educatem;
}om: 0.5rottgin-bmar63eb;
    color: #25m h3 {
    tion-ite.educa}


.1); 0ba(0, 0, 0, 4px 6px rgw: 0-shado   boxus: 10px;
 er-radi
    bord 2rem;dding:
    pawhite;: ndbackgroutem {
    cation-i}

.edu
o;gin: 0 aut    marh: 1000px;
dt   max-wi
 : 2rem;  gap);
  (400px, 1fr)inmaxo-fit, mrepeat(aut: mnslate-colud-temp;
    griiday: grpld {
    distion-grin */
.educa SectioationEduc
}

/* 8b;olor: #6474m;
    ce: 1.1re font-siznter;
   t-align: ceex0;
    t 3rem auto   margin:   800px;
x-width: ma
   ry {s-summa
.skill
00;
}-weight: 5nt  fo
  64748b;olor: #ncy {
    ccie

.profi0;
}ight: 50-we   font
 .9rem;ont-size: 0px;
    fadius: 20er-r
    bordem 1rem;0.5rdding:    paa3;
 3730 color: #  #e0e7ff;
 ckground: g {
    baskill-tam;
}

.rein-bottom: 1
    margr;ente-content: cfy   justi.5rem;
 ap: 0 gap;
   lex-wrap: wr   fy: flex;
    displaitems {
 }

.skill-om: 1rem;
bott    margin-b;
563eor: #2ol c
   egory h3 {skill-cat
}

.gn: center;li text-a  0, 0.1);
 ba(0, 0, x rgw: 0 4px 6p  box-shado10px;
  der-radius: borrem;
    ding: 2te;
    padd: whi backgroun
   category {}

.skill-0 auto;
gin: mar;
    idth: 1000px
    max-wem;ap: 2r   gr));
 1f, nmax(300pxt, miuto-firepeat(a: te-columnsd-templa
    gririd;display: g   {
 lls-grid 
.ski
}
: #f8fafc;backgroundlls {
    ion */
.ski Skills Sect

/*em;
}1rng-left: 
    paddieb; #2563x solid-left: 3p  border4748b;
    color: #6alic;
  : itfont-style1rem;
    argin-top:  m
   mary {ct-sum
}

.impa#2563eb;color: ;
     left: 0  absolute;
 ition: os"→";
    ptent:   conefore {
  ements li:bachiev
.}
m;
-left: 1.5repaddinge;
    on: relativ   positi25rem 0;
 0.ng:  paddi{
   ements li chieve;
}

.a: nonist-style
    l-top: 1rem; margin{
   chievements 00;
}

.at-weight: 5    fon0.9rem;
ze: t-si   fon
 ;: #94a3b8or    col
ate {line-d

.timem;
}re-bottom: 0.5rgin
    ma8b;or: #6474ol
    c4 {nt hmeline-conte
}

.ti: 0.5rem;argin-bottom3eb;
    m#256color: 
    content h3 {
.timeline-1);
}
0., 0, a(0, 0 4px 6px rgb-shadow: 0;
    boxdius: 10px   border-rarem;
  padding: 2;
   round: white{
    backgnt e-contemelin}

.ti: -8px;
  leftker {
  arine-meven) .timelh-child(tem:nt.timeline-i


}8px;ight: - r   e-marker {
elin .timh-child(odd)line-item:nttime0;
}

.: ;
    top0%r-radius: 5orde63eb;
    bnd: #25 backgroupx;
     height: 166px;
  width: 1   ute;
 : absolosition {
    parkermeline-m

.ti
} 2rem;ding-left:0%;
    pad: 5left
    ld(even) {h-chiem:ntine-it
}

.timelm;reght: 2ing-ri
    paddeft: 0;
    l(odd) {m:nth-childe-ite
.timelin;
}
th: 50% wid: 3rem;
   argin-bottom
    mtive;ition: relam {
    posimeline-ite

.t}
0%);-5ranslateX(: t  transformeb;
   #2563background:2px;
        width: bottom: 0;

    top: 0; 50%;
    t:efte;
    lion: absolu    posit'';
:    content:before {
 .timeline}


auto;n: 0   margi
  : 800px;idth max-w  relative;
 on: siti{
    poeline n */
.timSectioExperience 
}

/* center;ext-align:     t4748b;
   color: #6italic;
 style:   font-  : 2rem;
rgin-top
    ma {al-touch

.persont: bold;
}ont-weigh81;
    fcolor: #10b9
    left: 0;e;
    : absolutposition   ";
 : "✓ent    cont{
li:before .highlights m;
}

left: 1.5repadding-  ive;
  ion: relat   positrem 0;
 ing: 0.5  padd
  ts li {ighligh.h
 none;
}
yle:ist-st  l
   ul {tsgh
.highli
}
 1rem;m:-botto
    margineb;563r: #2 colo h3 {
   
.highlights
0, 0.1);
}ba(0, 0,  rg6pxw: 0 4px -shadooxx;
    badius: 10p border-r   2rem;
 padding: 
   nd: white;  backgrou
  em;-top: 2rinrg   ma {
 lights

.high.8;
}e-height: 1m;
    lin 1.1rent-size:to;
    fo aumargin: 0   
 dth: 800px;x-wixt {
    ma

.about-teafc;
}nd: #f8fgrou
    back
.about {on */cti
/* About Se
}eb;
or: #2563 col   ;
emottom: 3rargin-bnter;
    m: cext-align  terem;
  t-size: 2.5 {
    fon-titlesection0;
}

.dding: 80px 
    pa
section {ctions */Se
}

/* 3eb;56 #2  color:white;
  und: grock {
    bary:hovereconda

.btn-shite;
}r-color: w
    bordete;or: whi  colt;
   transparen background:
   y {darecon
}

.btn-s: #2563eb;rder-color
    bo#2563eb;or:    colarent;
 und: transp  backgroer {
  ry:hovprima.btn-b;
}

#2563erder-color:  boite;
   or: whcolb;
    d: #2563eackgroun   bmary {
 prin-bt

.ointer;
}   cursor: pnsparent;
  trax solid: 2porder    bs ease;
 0.3sition: allran t00;
   nt-weight: 6fo none;
    tion:ecora   text-d0px;
 r-radius: 5
    bordepx;x 302pg: 1 paddin
   line-block;play: in    dis{
btn 
.*/
/* Buttons 
s both;
}ase 0.6Up 1s efadeInation: 
    animt: center;conten justify-   
: 1rem;;
    gapsplay: flex    diuttons {


.hero-b;
}e 0.4s botheInUp 1s eas: fadon    animatight: auto;
gin-ri  marto;
  ft: auargin-le;
    mth: 600pxmax-wid  ty: 0.8;
  aciop  ;
  emom: 2rbott  margin-  1rem;
1.ze:  font-sition {
   -descrip

.heroth;
}.2s boease 0adeInUp 1s mation: f
    ani;opacity: 0.9m;
    m: 1re-botto
    marginize: 1.5rem;nt-s {
    foubtitleo-s
}

.herase; 1s efadeInUpon: animati  m: 1rem;
  gin-bottomar0;
    ht: 70-weig   font;
 3.5reme: siz
    font--title {

.hero
}x;ing: 0 20p paddauto;
   : 0 in;
    marg00px: 12 max-width {
   nerntai.hero-co

nter;
}align: ce text-hite;
    wolor:;
    ca2 100%)0%, #764beg, #667eea 35dadient(1ear-grnd: lin backgrounter;
   s: cealign-item    ;
flex   display: h;
 : 100v  min-heightro {
  ion */
.he Sectero
}

/* H: 0.3s;ransition    tn: 3px 0;
gi   maror: #333;
 nd-colrou
    backgght: 3px;    heidth: 25px;
wibar {
    
}

.pointer;r: urso column;
   n: crectiolex-di  f: none;
      displaymburger {


.ha}: #2563eb;
    colorve {
av-link.actik:hover, .nin.nav-l;
}

ease.3s on: color 0    transitit: 500;
 font-weigh#333;
   olor: ;
    cration: none-decoxt{
    te
.nav-link em;
}
ap: 2r   g none;
 t-style:ex;
    lis fl display:
   nu {
.nav-me
}
eb;6325or: #00;
    colweight: 7t-  fonrem;
  : 1.5size    font- {
ogo
.nav-l
}
ter;ems: cen-it  align  between;
 space-t:tify-conten jus
   lex;splay: f
    ding: 0 20px; paddito;
   rgin: 0 au ma00px;
   width: 12  max-
  er {inonta
}

.nav-c 0.1);, 0, 0, 10px rgba(0ow: 0 2pxshad;
    box-g: 1rem 0
    paddindex: 1000;in
    z-x);0pur(1: bllter backdrop-fi);
    0.95, 255,55rgba(255, 2round: backg    %;
100    width:  0;
op:  t: fixed;
   positionvbar {
   /
.naavigation * N}

/* 20px;
adding: 0  pto;
  : 0 au
    margin 1200px;th:max-wider {
    ontain;
}

.c: #fffound-colorackgr    bor: #333;
.6;
    colheight: 1ne-    li
serif;r', sans-amily: 'Inte
    font-f}

body {-box;
zing: border
    box-sipadding: 0;n: 0;
      margi
* {
  CSS */Portfolio ssional fe '''/* Pros_content =
        csSSnerate C   # Ge      
  >'''
     
</html/body>pt>
<scris"></pt.j"scri=ript src

    <scooter>  </fiv>
     </d>
     ies.</pnologrn web techd modeion an generatontentAI-powered csing created uo was his portfoli>T         <p>
   Platform.</poroh AI ted by K Genera4 {name}.>&copy; 202    <p">
        nertaiclass="con       <div er">
 s="footer clas    <footer -->
oot  <!-- F

  n></sectio  
  </div>v>
        </di            </div>
          
      form>        </        
    tton>Message</bund ry">Sepriman-ss="btn btit" cla type="submutton       <b              /div>
     <                      area>
ed></text" requir="5ge" rows Messaourlder="Yge" placeho"messa name=sage"d="mesextarea i      <t                      -group">
lass="formiv c <d                      
   </div>                 
     >" required Email"Yourr= placeholdel"ame="email" nemaiail" id="type="emt   <inpu                    p">
      "form-grou class=      <div                  iv>
    </d           
         >ed" requiramer="Your Nplaceholde"name" ame="name" nxt" id="teinput type=     <                    
   group">lass="form-iv c      <d            
      ">ntactFormd="corm i         <fo       orm">
    ct-f="contadiv class         <         </div>
      
        iv> </d         
          o)}nal_infa.perso cv_datact,ontls(ctact_detai_conormat {_f              
         tails">act-de="contclassdiv          <         p>
  </rations!')}or collabonities for opportureach out o e tFeel freion', 'to_act('call_get>{contact."ctaontact-ss="c<p cla                   -info">
 s="contact  <div clas        t">
      entact-contlass="con<div c           </h2>
 ch Tou Initle">Gettion-t"sec <h2 class=   >
        r"ineontass="c <div cla
       ontact">" class="cacton id="contcti-->
    <seact Section  Cont!--n>

    <  </sectiov>
    </di      iv>
/d  <  )}
        on(educationti_educamat    {_for            ">
rid-gducation="ediv class   <
         ion</h2>>Educat-title"ionss="sect <h2 cla          
 er">inta"conss=  <div cla      n">
tios="educa" clas"educationid=ction 
    <seection -->Education S<!-- ion>

      </sect</div>
          div>
   </       /p>
  tise.')}<xperith proven e set w