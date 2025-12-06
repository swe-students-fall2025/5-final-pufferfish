
import re
from typing import Dict, Any, List
from pypdf import PdfReader

def parse_resume_pdf(file_stream) -> Dict[str, Any]:
    """
    Parses a PDF resume and extracts contact info and structured sections.
    """
    try:
        reader = PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return {}

    extracted_data = {
        'first_name': '',
        'last_name': '',
        'email': '',
        'phone': '',
        'education': [],
        'experience': [],
        'skills': [],
        'projects': []
    }

    # --- Basic Contact Info ---
    extract_contact_info(text, extracted_data)

    # --- Section Extraction ---
    sections = extract_sections(text)

    # --- Structured Parsing ---
    if 'education' in sections:
        extracted_data['education'] = parse_education(sections['education'])

    if 'experience' in sections:
        extracted_data['experience'] = parse_experience(sections['experience'])

    if 'skills' in sections:
        extracted_data['skills'] = parse_skills(sections['skills'])

    if 'projects' in sections:
        extracted_data['projects'] = parse_projects(sections['projects'])

    return extracted_data

def extract_contact_info(text: str, data: Dict[str, Any]):
    """
    Helper function to extract contact info
    
    :param text: text to extract from
    :type text: str
    :param data: extracted data dict
    :type data: Dict[str, Any]
    """
    # Email
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if email_match:
        data['email'] = email_match.group(0)

    # Phone
    phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        data['phone'] = phone_match.group(0).strip()
        
    # First line for name
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        name_parts = lines[0].split()
        if len(name_parts) >= 1:
            data['first_name'] = name_parts[0]
        if len(name_parts) >= 2:
            data['last_name'] = " ".join(name_parts[1:])

def extract_sections(text: str) -> Dict[str, str]:
    """
    Helper function to identify sections and extract info
    
    :param text: text to extract from 
    :type text: str
    :return: dictionary containing extract info
    :rtype: Dict[str, str]
    """
    lower_text = text.lower()
    section_map = {
        'education': ['education', 'university', 'college', 'academic background'],
        'experience': ['experience', 'work experience', 'employment', 'work history'],
        'skills': ['skills', 'technologies', 'technical skills'],
        'projects': ['projects', 'personal projects', 'portfolio']
    }

    found_headers = []
    for name, keywords in section_map.items():
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            for match in re.finditer(pattern, lower_text):
                found_headers.append({'start': match.start(), 'name': name})

    found_headers.sort(key=lambda x: x['start'])

    # Filter unique sections
    unique_headers = []
    seen = set()
    for h in found_headers:
        if h['name'] not in seen:
            unique_headers.append(h)
            seen.add(h['name'])
    unique_headers.sort(key=lambda x: x['start'])

    sections = {}
    for i, header in enumerate(unique_headers):
        start = header['start']
        end = unique_headers[i+1]['start'] if i < len(unique_headers) - 1 else len(text)
        content = text[start:end]
        # Remove first line - header
        parts = content.split('\n', 1)
        if len(parts) > 1:
            sections[header['name']] = parts[1].strip()
        else:
            sections[header['name']] = content.strip()

    return sections

def parse_education(text: str) -> List[Dict[str, Any]]:
    """
    Helper to parse education info
    
    :param text: text to extract from
    :type text: str
    :return: dict containing extracted info
    :rtype: List[Dict[str, Any]]
    """
    entries = []
    # Heuristic: split by lines
    # Assume groups of lines represent an entry
    # Look for date patterns to identify new entries?
    # Or just lines that look like school names?
    
    # Simple approach based on sample: School \n Degree \n Date
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    # We'll group by detecting "University" or "College" or just chunks of 2-3 lines
    
    # Pattern for date range: "Aug. 2018 – May 2021"
    date_pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z.]*\s+\d{4})\s*–\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z.]*\s+\d{4}|Present)'
    
    current_entry = {}
    buffer = []
    
    for line in lines:
        date_match = re.search(date_pattern, line, re.IGNORECASE)
        if date_match:
            if buffer:
                current_entry['school'] = buffer[0]
                if len(buffer) > 1:
                    current_entry['degree'] = " ".join(buffer[1:])
                else:
                    # Maybe degree is on the same line as date?
                    # "Bachelor of Arts... Aug 2018..."
                    pre_date = line[:date_match.start()].strip()
                    if pre_date:
                        current_entry['degree'] = pre_date
            
            # Parse dates
            start_str, end_str = date_match.groups()
            s_m, s_y = parse_date_str(start_str)
            e_m, e_y = parse_date_str(end_str)
            
            current_entry['start_month'] = s_m
            current_entry['start_year'] = s_y
            current_entry['end_month'] = e_m
            current_entry['end_year'] = e_y
            
            entries.append(current_entry)
            current_entry = {}
            buffer = []
        else:
            buffer.append(line)
            
    # Fallback if no dates found, just dump first line as school
    if not entries and buffer:
        entries.append({'school': buffer[0]})
        
    return entries

def parse_experience(text: str) -> List[Dict[str, Any]]:
    """
    Helper to parse exp.
    
    :param text: text to extract from
    :type text: str
    :return: dict containing extracted info
    :rtype: List[Dict[str, Any]]
    """
    entries = []
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    # Date pattern again
    date_pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z.]*\s+\d{4})\s*–\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z.]*\s+\d{4}|Present)'

    current_entry = None
    
    for line in lines:
        date_match = re.search(date_pattern, line, re.IGNORECASE)
        if date_match:
            # Start of a new entry
            if current_entry:
                entries.append(current_entry)
            
            current_entry = {'bullets': []}
            
            # Parse dates
            start_str, end_str = date_match.groups()
            s_m, s_y = parse_date_str(start_str)
            e_m, e_y = parse_date_str(end_str)
            current_entry['start_month'] = s_m
            current_entry['start_year'] = s_y
            current_entry['end_month'] = e_m
            current_entry['end_year'] = e_y
            
            # Title/Company usually on this line or previous lines?
            # Sample: "Undergraduate Research Assistant June 2020 – Present"
            pre_date = line[:date_match.start()].strip()
            if pre_date:
                current_entry['title'] = pre_date
            
        elif current_entry is not None:
            # Check for bullet points
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                current_entry['bullets'].append(line.lstrip('•-* ').strip())
            elif 'company' not in current_entry and 'location' not in current_entry:
                 # Assume line after title is Company/Location
                 # Sample: "Texas A&M University College Station, TX"
                 current_entry['company'] = line
            else:
                 pass
                 
    if current_entry:
        entries.append(current_entry)
        
    return entries

def parse_projects(text: str) -> List[Dict[str, Any]]:
    # Similar to experience but Title might be Project Name
    # TODO: create logic for parsing projects
    return parse_experience(text) # Reuse logic for now

def parse_skills(text: str) -> List[Dict[str, Any]]:
    entries = []
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    for line in lines:
        if ':' in line:
            cat, skills = line.split(':', 1)
            entries.append({'category': cat.strip(), 'skills': skills.strip()})
        else:
            # Treat whole line as skills with generic category?
            entries.append({'category': 'General', 'skills': line})
            
    return entries

def parse_date_str(date_str: str):
    if not date_str or date_str.lower() == 'present':
        return '', ''
    try:
        parts = date_str.split()
        if len(parts) == 2:
            month_str = parts[0][:3].lower() # jan, feb...
            year = parts[1]
            
            months = {
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
                'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
            }
            return months.get(month_str, ''), year
    except:
        pass
    return '', ''
