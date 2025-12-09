import os
import re
from datetime import datetime


def escape_latex(text):
    """Escape LaTeX special characters in text."""
    if not text:
        return ""
    
    # Convert to string if not already
    text = str(text)
    
    # LaTeX special characters that need escaping
    special_chars = {
        '\\': r'\textbackslash{}',
        '{': r'\{',
        '}': r'\}',
        '$': r'\$',
        '&': r'\&',
        '%': r'\%',
        '#': r'\#',
        '^': r'\textasciicircum{}',
        '_': r'\_',
        '~': r'\textasciitilde{}',
    }
    
    # Escape special characters
    for char, replacement in special_chars.items():
        text = text.replace(char, replacement)
    
    return text


def format_date_for_latex(date_str):
    """Format date string (YYYY-MM or 'Present') to LaTeX format like 'Aug. 2019 -- Present'."""
    if not date_str or date_str == "Present":
        return "Present"
    
    try:
        # Parse YYYY-MM format
        if '-' in date_str:
            year, month = date_str.split('-')
            month_num = int(month)
            month_names = [
                'Jan.', 'Feb.', 'Mar.', 'Apr.', 'May', 'June',
                'July', 'Aug.', 'Sept.', 'Oct.', 'Nov.', 'Dec.'
            ]
            if 1 <= month_num <= 12:
                return f"{month_names[month_num - 1]} {year}"
            else:
                return year
        else:
            # Just year
            return date_str
    except (ValueError, AttributeError):
        return date_str


def format_date_range(start, end):
    """Format date range for LaTeX."""
    start_str = format_date_for_latex(start) if start else ""
    end_str = format_date_for_latex(end) if end else "Present"
    
    if start_str and end_str:
        return f"{start_str} -- {end_str}"
    elif start_str:
        return start_str
    elif end_str:
        return end_str
    else:
        return ""


def fill_jake_template(structured_data, template_path):
    """Fill the Jake template with structured data."""
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Comment out glyphtounicode if it causes issues (it's optional for ATS parsing)
    # The file might not be available in all LaTeX installations
    template = template.replace('\\input{glyphtounicode}', '% \\input{glyphtounicode}  % Commented out - optional for ATS parsing')
    
    # Extract personal info
    first_name = escape_latex(structured_data.get('first_name', ''))
    last_name = escape_latex(structured_data.get('last_name', ''))
    full_name = f"{first_name} {last_name}".strip()
    if not full_name:
        full_name = "Your Name"
    
    email = escape_latex(structured_data.get('email', ''))
    phone = escape_latex(structured_data.get('phone_number', ''))
    linkedin = structured_data.get('LinkedIn', '').strip()
    website = structured_data.get('Website', '').strip()
    
    # Build contact info line
    contact_parts = []
    if phone:
        contact_parts.append(phone)
    if email:
        contact_parts.append(f"\\href{{mailto:{email}}}{{\\underline{{{email}}}}}")
    if linkedin:
        # Clean up LinkedIn URL
        if not linkedin.startswith('http'):
            if 'linkedin.com' not in linkedin:
                linkedin = f"linkedin.com/in/{linkedin.replace('linkedin.com/in/', '')}"
            linkedin = f"https://{linkedin}"
        contact_parts.append(f"\\href{{{linkedin}}}{{\\underline{{{escape_latex(linkedin.replace('https://', '').replace('http://', ''))}}}}}")
    if website:
        if not website.startswith('http'):
            website = f"https://{website}"
        contact_parts.append(f"\\href{{{website}}}{{\\underline{{{escape_latex(website.replace('https://', '').replace('http://', ''))}}}}}")
    
    contact_line = " $|$ ".join(contact_parts) if contact_parts else ""
    
    # Replace heading
    heading_pattern = r'\\begin\{center\}.*?\\end\{center\}'
    new_heading = f"\\begin{{center}}\n    \\textbf{{\\Huge \\scshape {full_name}}}"
    if contact_line:
        new_heading += f" \\\\ \\vspace{{1pt}}\n    \\small {contact_line}"
    new_heading += "\n\\end{center}"
    # Use lambda to avoid regex interpreting backslashes in replacement
    template = re.sub(heading_pattern, lambda m: new_heading, template, flags=re.DOTALL)
    
    # Build Education section
    education_section = ""
    education_list = structured_data.get('education', [])
    if education_list:
        education_section = "%-----------EDUCATION-----------\n\\section{Education}\n  \\resumeSubHeadingListStart\n"
        for edu in education_list:
            institution = escape_latex(edu.get('institution', ''))
            degree = escape_latex(edu.get('degree', ''))
            location = escape_latex(edu.get('location', ''))
            
            # Format graduation date
            end_month = edu.get('end_month')
            end_year = edu.get('end_year')
            date_str = ""
            if end_year:
                if end_month:
                    date_str = format_date_for_latex(f"{end_year}-{end_month.zfill(2)}")
                else:
                    date_str = str(end_year)
            
            if institution:
                education_section += f"    \\resumeSubheading\n"
                education_section += f"      {{{institution}}}{{{location if location else ''}}}\n"
                education_section += f"      {{{degree}}}{{{date_str}}}\n"
        education_section += "  \\resumeSubHeadingListEnd\n\n"
    
    # Replace Education section
    education_pattern = r'%-----------EDUCATION-----------.*?\\resumeSubHeadingListEnd'
    if education_section:
        template = re.sub(education_pattern, lambda m: education_section.rstrip(), template, flags=re.DOTALL)
    else:
        # Remove entire Education section if no education entries
        template = re.sub(education_pattern + r'\s*\n\s*\n', '', template, flags=re.DOTALL)
    
    # Build Experience section
    experience_section = ""
    experience_list = structured_data.get('experience', [])
    if experience_list:
        experience_section = "%-----------EXPERIENCE-----------\n\\section{Experience}\n  \\resumeSubHeadingListStart\n\n"
        for exp in experience_list:
            company = escape_latex(exp.get('company', ''))
            role = escape_latex(exp.get('role', ''))
            location = escape_latex(exp.get('location', ''))
            start = exp.get('start', '')
            end = exp.get('end', 'Present')
            bullets = exp.get('bullets', [])
            
            date_range = format_date_range(start, end)
            
            if company and role:
                experience_section += f"    \\resumeSubheading\n"
                experience_section += f"      {{{role}}}{{{date_range}}}\n"
                experience_section += f"      {{{company}}}{{{location if location else ''}}}\n"
                
                if bullets:
                    experience_section += "      \\resumeItemListStart\n"
                    for bullet in bullets:
                        if bullet.strip():
                            bullet_text = escape_latex(bullet.strip())
                            experience_section += f"        \\resumeItem{{{bullet_text}}}\n"
                    experience_section += "      \\resumeItemListEnd\n"
        experience_section += "  \\resumeSubHeadingListEnd\n\n"
    
    # Replace Experience section
    experience_pattern = r'%-----------EXPERIENCE-----------.*?\\resumeSubHeadingListEnd'
    if experience_section:
        template = re.sub(experience_pattern, lambda m: experience_section.rstrip(), template, flags=re.DOTALL)
    else:
        # Remove entire Experience section if no experience entries
        template = re.sub(experience_pattern + r'\s*\n\s*\n', '', template, flags=re.DOTALL)
    
    # Build Projects section
    projects_section = ""
    projects_list = structured_data.get('projects', [])
    if projects_list:
        projects_section = "%-----------PROJECTS-----------\n\\section{Projects}\n    \\resumeSubHeadingListStart\n"
        for proj in projects_list:
            title = escape_latex(proj.get('title', ''))
            skills = escape_latex(proj.get('skills', ''))
            bullets = proj.get('bullets', [])
            
            if title:
                project_title = f"\\textbf{{{title}}}"
                if skills:
                    project_title += f" $|$ \\emph{{{skills}}}"
                
                projects_section += f"      \\resumeProjectHeading\n"
                projects_section += f"          {{{project_title}}}{{}}\n"
                
                if bullets:
                    projects_section += "          \\resumeItemListStart\n"
                    for bullet in bullets:
                        if bullet.strip():
                            bullet_text = escape_latex(bullet.strip())
                            projects_section += f"            \\resumeItem{{{bullet_text}}}\n"
                    projects_section += "          \\resumeItemListEnd\n"
        projects_section += "    \\resumeSubHeadingListEnd\n\n\n"
    
    # Replace Projects section
    projects_pattern = r'%-----------PROJECTS-----------.*?\\resumeSubHeadingListEnd'
    if projects_section:
        template = re.sub(projects_pattern, lambda m: projects_section.rstrip(), template, flags=re.DOTALL)
    else:
        # Remove entire Projects section if no projects
        template = re.sub(projects_pattern + r'\s*\n\s*\n', '', template, flags=re.DOTALL)
    
    # Build Skills section
    skills_section = ""
    skills_list = structured_data.get('skills', [])
    if skills_list:
        skills_section = "%-----------PROGRAMMING SKILLS-----------\n\\section{Technical Skills}\n \\begin{itemize}[leftmargin=0.15in, label={}]\n    \\small{\\item{\n"
        
        skill_lines = []
        for skill in skills_list:
            category = escape_latex(skill.get('category', ''))
            skills_str = escape_latex(skill.get('skills', ''))
            if category and skills_str:
                skill_lines.append(f"     \\textbf{{{category}}}{{: {skills_str}}}")
        
        if skill_lines:
            skills_section += " \\\\\n     ".join(skill_lines)
            skills_section += "\n    }}\n \\end{itemize}\n\n\n"
        else:
            skills_section = ""
    
    # Replace Skills section
    skills_pattern = r'%-----------PROGRAMMING SKILLS-----------.*?\\end\{itemize\}'
    if skills_section:
        template = re.sub(skills_pattern, lambda m: skills_section.rstrip(), template, flags=re.DOTALL)
    else:
        # Remove entire Skills section if no skills
        template = re.sub(skills_pattern + r'\s*\n\s*\n', '', template, flags=re.DOTALL)
    
    return template


def fill_harshibar_template(structured_data, template_path):
    """Fill the Harshibar template with structured data."""
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Extract personal info
    first_name = escape_latex(structured_data.get('first_name', ''))
    last_name = escape_latex(structured_data.get('last_name', ''))
    full_name = f"{first_name} {last_name}".strip()
    if not full_name:
        full_name = "Your Name"
    
    email = escape_latex(structured_data.get('email', ''))
    phone = escape_latex(structured_data.get('phone_number', ''))
    linkedin = structured_data.get('LinkedIn', '').strip()
    website = structured_data.get('Website', '').strip()
    
    # Build contact info line (Harshibar uses FontAwesome icons)
    contact_parts = []
    if phone:
        contact_parts.append(f"\\faPhone* \\texttt{{{phone}}}")
    if email:
        contact_parts.append(f"\\faEnvelope \\hspace{{2pt}} \\texttt{{{email}}}")
    if linkedin:
        if not linkedin.startswith('http'):
            if 'linkedin.com' not in linkedin:
                linkedin = f"linkedin.com/in/{linkedin.replace('linkedin.com/in/', '')}"
            linkedin = f"https://{linkedin}"
        linkedin_display = linkedin.replace('https://', '').replace('http://', '')
        contact_parts.append(f"\\faLinkedin \\hspace{{2pt}} \\texttt{{{escape_latex(linkedin_display)}}}")
    if website:
        if not website.startswith('http'):
            website = f"https://{website}"
        website_display = website.replace('https://', '').replace('http://', '')
        contact_parts.append(f"\\faGlobe \\hspace{{2pt}} \\texttt{{{escape_latex(website_display)}}}")
    
    contact_line = " \\hspace{1pt} $|$\n    \\hspace{1pt} ".join(contact_parts) if contact_parts else ""
    
    # Replace heading
    heading_pattern = r'\\begin\{center\}.*?\\end\{center\}'
    new_heading = f"\\begin{{center}}\n    \\textbf{{\\Huge {full_name}}}"
    if contact_line:
        new_heading += f" \\\\ \\vspace{{5pt}}\n    \\small {contact_line}"
    new_heading += "\n    \\\\ \\vspace{-3pt}\n\\end{center}"
    # Use lambda to avoid regex interpreting backslashes in replacement
    template = re.sub(heading_pattern, lambda m: new_heading, template, flags=re.DOTALL)
    
    # Build Experience section (comes first in Harshibar)
    experience_section = ""
    experience_list = structured_data.get('experience', [])
    if experience_list:
        experience_section = "%-----------EXPERIENCE-----------\n\\section{EXPERIENCE}\n  \\resumeSubHeadingListStart\n\n"
        for exp in experience_list:
            company = escape_latex(exp.get('company', ''))
            role = escape_latex(exp.get('role', ''))
            location = escape_latex(exp.get('location', ''))
            start = exp.get('start', '')
            end = exp.get('end', 'Present')
            bullets = exp.get('bullets', [])
            
            date_range = format_date_range(start, end)
            
            if company and role:
                experience_section += f"    \\resumeSubheading\n"
                experience_section += f"      {{{company}}}{{{date_range}}}\n"
                experience_section += f"      {{{role}}}{{{location if location else ''}}}\n"
                
                if bullets:
                    experience_section += "      \\resumeItemListStart\n"
                    for bullet in bullets:
                        if bullet.strip():
                            bullet_text = escape_latex(bullet.strip())
                            experience_section += f"        \\resumeItem{{{bullet_text}}}\n"
                    experience_section += "      \\resumeItemListEnd\n"
        experience_section += "  \\resumeSubHeadingListEnd\n\n\n"
    
    # Replace Experience section
    experience_pattern = r'%-----------EXPERIENCE-----------.*?\\resumeSubHeadingListEnd'
    if experience_section:
        template = re.sub(experience_pattern, lambda m: experience_section.rstrip(), template, flags=re.DOTALL)
    else:
        template = re.sub(experience_pattern + r'\s*\n\s*\n', '', template, flags=re.DOTALL)
    
    # Build Projects section
    projects_section = ""
    projects_list = structured_data.get('projects', [])
    if projects_list:
        projects_section = "%-----------PROJECTS-----------\n\n\\section{PROJECTS}\n    \\resumeSubHeadingListStart\n"
        for proj in projects_list:
            title = escape_latex(proj.get('title', ''))
            skills = escape_latex(proj.get('skills', ''))
            bullets = proj.get('bullets', [])
            
            if title:
                project_title = f"\\textbf{{{title}}}"
                
                projects_section += f"      \\resumeProjectHeading\n"
                projects_section += f"          {{{project_title}}} {{}}\n"
                
                if bullets:
                    projects_section += "          \\resumeItemListStart\n"
                    for bullet in bullets:
                        if bullet.strip():
                            bullet_text = escape_latex(bullet.strip())
                            projects_section += f"            \\resumeItem{{{bullet_text}}}\n"
                    projects_section += "          \\resumeItemListEnd\n"
        projects_section += "    \\resumeSubHeadingListEnd\n\n\n\n"
    
    # Replace Projects section
    projects_pattern = r'%-----------PROJECTS-----------.*?\\resumeSubHeadingListEnd'
    if projects_section:
        template = re.sub(projects_pattern, lambda m: projects_section.rstrip(), template, flags=re.DOTALL)
    else:
        template = re.sub(projects_pattern + r'\s*\n\s*\n', '', template, flags=re.DOTALL)
    
    # Build Education section
    education_section = ""
    education_list = structured_data.get('education', [])
    if education_list:
        education_section = "%-----------EDUCATION-----------\n\\section {EDUCATION}\n  \\resumeSubHeadingListStart\n"
        for edu in education_list:
            institution = escape_latex(edu.get('institution', ''))
            degree = escape_latex(edu.get('degree', ''))
            location = escape_latex(edu.get('location', ''))
            
            end_month = edu.get('end_month')
            end_year = edu.get('end_year')
            date_str = ""
            if end_year:
                if end_month:
                    date_str = format_date_range(None, f"{end_year}-{end_month.zfill(2)}")
                else:
                    date_str = format_date_range(None, str(end_year))
            
            if institution:
                education_section += f"    \\resumeSubheading\n"
                education_section += f"      {{{institution}}}{{{date_str}}}\n"
                education_section += f"      {{{degree}}}{{{location if location else ''}}}\n"
        education_section += "  \\resumeSubHeadingListEnd\n\n\n"
    
    # Replace Education section
    education_pattern = r'%-----------EDUCATION-----------.*?\\resumeSubHeadingListEnd'
    if education_section:
        template = re.sub(education_pattern, lambda m: education_section.rstrip(), template, flags=re.DOTALL)
    else:
        template = re.sub(education_pattern + r'\s*\n\s*\n', '', template, flags=re.DOTALL)
    
    # Build Skills section
    skills_section = ""
    skills_list = structured_data.get('skills', [])
    if skills_list:
        skills_section = "%-----------PROGRAMMING SKILLS-----------\n\\section{SKILLS}\n \\begin{itemize}[leftmargin=0in, label={}]\n    \\small{\\item{\n"
        
        skill_lines = []
        for skill in skills_list:
            category = escape_latex(skill.get('category', ''))
            skills_str = escape_latex(skill.get('skills', ''))
            if category and skills_str:
                skill_lines.append(f"     \\textbf{{{category}}} {{: {skills_str}}}")
        
        if skill_lines:
            skills_section += " \\\\\n     ".join(skill_lines)
            skills_section += "\\vspace{2pt} \\\\\n    }}\n \\end{itemize}\n\n\n"
        else:
            skills_section = ""
    
    # Replace Skills section
    skills_pattern = r'%-----------PROGRAMMING SKILLS-----------.*?\\end\{itemize\}'
    if skills_section:
        template = re.sub(skills_pattern, lambda m: skills_section.rstrip(), template, flags=re.DOTALL)
    else:
        template = re.sub(skills_pattern + r'\s*\n\s*\n', '', template, flags=re.DOTALL)
    
    return template


def fill_latex_template(structured_data, template_id, template_path):
    """Fill a LaTeX template with structured data based on template ID."""
    if template_id == 'jake':
        return fill_jake_template(structured_data, template_path)
    elif template_id == 'harshibar':
        return fill_harshibar_template(structured_data, template_path)
    else:
        raise ValueError(f"Unknown template ID: {template_id}")

