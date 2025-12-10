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
        "first_name": "",
        "last_name": "",
        "email": "",
        "phone": "",
        "education": [],
        "experience": [],
        "skills": [],
        "projects": [],
    }

    # --- Basic Contact Info ---
    extract_contact_info(text, extracted_data)

    # --- Section Extraction ---
    sections = extract_sections(text)

    # --- Structured Parsing ---
    if "education" in sections:
        extracted_data["education"] = parse_education(sections["education"])

    if "experience" in sections:
        extracted_data["experience"] = parse_experience(sections["experience"])

    if "skills" in sections:
        extracted_data["skills"] = parse_skills(sections["skills"])

    if "projects" in sections:
        extracted_data["projects"] = parse_projects(sections["projects"])

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
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        data["email"] = email_match.group(0)

    # LinkedIn
    linkedin_match = re.search(r'(linkedin\.com/in/[a-zA-Z0-9_-]+)', text, re.IGNORECASE)
    if linkedin_match:
        data['linkedin'] = linkedin_match.group(0)

    # GitHub or Website
    github_match = re.search(r'(github\.com/[a-zA-Z0-9_-]+)', text, re.IGNORECASE)
    if github_match:
        data['website'] = github_match.group(0)
    else:
        pass

    # Phone
    phone_pattern = r"(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        data["phone"] = phone_match.group(0).strip()

    # First line for name
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        name_parts = lines[0].split()
        if len(name_parts) >= 1:
            data["first_name"] = name_parts[0]
        if len(name_parts) >= 2:
            data["last_name"] = " ".join(name_parts[1:])


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
        "education": ["education", "university", "college", "academic background"],
        "experience": ["experience", "work experience", "employment", "work history"],
        "skills": ["skills", "technologies", "technical skills"],
        "projects": ["projects", "personal projects", "portfolio"],
    }

    found_headers = []
    for name, keywords in section_map.items():
        for keyword in keywords:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            for match in re.finditer(pattern, lower_text):
                found_headers.append({"start": match.start(), "name": name})

    found_headers.sort(key=lambda x: x["start"])

    # Filter unique sections
    unique_headers = []
    seen = set()
    for h in found_headers:
        if h["name"] not in seen:
            unique_headers.append(h)
            seen.add(h["name"])
    unique_headers.sort(key=lambda x: x["start"])

    sections = {}
    for i, header in enumerate(unique_headers):
        start = header["start"]
        end = (
            unique_headers[i + 1]["start"] if i < len(unique_headers) - 1 else len(text)
        )
        content = text[start:end]
        # Remove first line - header
        parts = content.split("\n", 1)
        if len(parts) > 1:
            sections[header["name"]] = parts[1].strip()
        else:
            sections[header["name"]] = content.strip()

    return sections


def parse_education(text: str) -> List[Dict[str, Any]]:
    entries = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Pattern for date range: "Aug. 2018 – May 2021"
    date_pattern = r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z.]*\s+\d{4})\s*–\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z.]*\s+\d{4}|Present)"

    current_entry = {}
    buffer = []

    for line in lines:
        date_match = re.search(date_pattern, line, re.IGNORECASE)
        if date_match:
            if buffer:
                # First line in buffer is School + Location
                school_line = buffer[0]
                # Heuristic: split by last comma for location? "University Name, City, ST"
                if ',' in school_line:
                    parts = school_line.rsplit(',', 2)
                    if len(parts) >= 2:
                        location_part = school_line[len(parts[0]):].strip(', ')
                        school_part = parts[0].strip()
                        
                        split_match = re.search(r'(.*? (?:University|College|Institute|School|Academy))\s+([A-Z][a-zA-Z\s]+)$', school_part)
                        if split_match:
                            real_school = split_match.group(1).strip()
                            city = split_match.group(2).strip()
                            current_entry['school'] = real_school
                            current_entry['location'] = f"{city}, {location_part}"
                        else:
                            current_entry['school'] = school_part
                            current_entry['location'] = location_part
                    else:
                        current_entry["school"] = school_line
                else:
                    current_entry["school"] = school_line

                if len(buffer) > 1:
                    full_degree = " ".join(buffer[1:])
                else:
                    pre_date = line[: date_match.start()].strip()
                    full_degree = pre_date

                if ' in ' in full_degree:
                    d, f = full_degree.split(' in ', 1)
                    current_entry['degree'] = d.strip()
                    current_entry['field'] = f.split(',')[0].strip()
                else:
                    current_entry["degree"] = full_degree

            # Parse dates
            start_str, end_str = date_match.groups()
            s_m, s_y = parse_date_str(start_str)
            e_m, e_y = parse_date_str(end_str)

            current_entry["start_month"] = s_m
            current_entry["start_year"] = s_y
            current_entry["end_month"] = e_m
            current_entry["end_year"] = e_y

            entries.append(current_entry)
            current_entry = {}
            buffer = []
        else:
            buffer.append(line)

    if not entries and buffer:
        entries.append({"school": buffer[0]})

    return entries


def parse_experience(text: str) -> List[Dict[str, Any]]:
    entries = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    date_pattern = r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z.]*\s+\d{4})\s*–\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z.]*\s+\d{4}|Present)"

    current_entry = None

    for line in lines:
        date_match = re.search(date_pattern, line, re.IGNORECASE)
        if date_match:
            if current_entry:
                entries.append(current_entry)

            current_entry = {"bullets": []}

            start_str, end_str = date_match.groups()
            s_m, s_y = parse_date_str(start_str)
            e_m, e_y = parse_date_str(end_str)
            current_entry["start_month"] = s_m
            current_entry["start_year"] = s_y
            current_entry["end_month"] = e_m
            current_entry["end_year"] = e_y

            pre_date = line[: date_match.start()].strip()
            if pre_date:
                current_entry["title"] = pre_date

        elif current_entry is not None:
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                current_entry['bullets'].append(line.lstrip('•-* ').strip())
            elif 'company' not in current_entry and 'location' not in current_entry:
                 if ',' in line:
                     parts = line.rsplit(',', 1) # City, ST
                     possible_loc = parts[1].strip()
                     if len(possible_loc) < 5: 
                         current_entry['company'] = parts[0].strip()
                         current_entry['location'] = line[len(current_entry['company']):].strip(', ')
                         
                         school_match = re.search(r'(.*? (?:University|College|Institute|School|Academy))\s+([A-Z][a-zA-Z\s]+)$', current_entry['company'])
                         if school_match:
                             current_entry['company'] = school_match.group(1).strip()
                             city = school_match.group(2).strip()
                             current_entry['location'] = f"{city}, {current_entry['location']}"
                     else:
                        current_entry['company'] = line
                 else:
                    current_entry['company'] = line
            else:
                pass

    if current_entry:
        entries.append(current_entry)

    return entries


def parse_projects(text: str) -> List[Dict[str, Any]]:
    entries = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Date pattern
    date_pattern = r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z.]*\s+\d{4})\s*–\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z.]*\s+\d{4}|Present)"

    current_entry = None

    for line in lines:
        # Check for date line, usually indicates start of project entry if in projects section
        date_match = re.search(date_pattern, line, re.IGNORECASE)

        if date_match:
            if current_entry:
                entries.append(current_entry)
            
            current_entry = {'bullets': []}
            
            pre_date = line[:date_match.start()].strip()
            if '|' in pre_date:
                parts = pre_date.split('|', 1)
                current_entry['name'] = parts[0].strip()
                candidate_title = parts[1].strip()
                
                tech_keywords = ['python', 'java', 'c++', 'react', 'sql', 'docker', 'flask', 'node', 'aws', 'git', 'html', 'css', 'javascript', 'typescript']
                is_tech = False
                if ',' in candidate_title:
                    is_tech = True
                else:
                    lower_title = candidate_title.lower()
                    if any(k in lower_title for k in tech_keywords):
                        is_tech = True
                
                if is_tech:
                    current_entry['skills'] = candidate_title
                    current_entry['title'] = current_entry['name'] 
                else:
                    current_entry['title'] = current_entry['name']
                    if candidate_title:
                         current_entry['skills'] = candidate_title
            else:
                current_entry['title'] = pre_date

        elif current_entry is not None:
             if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                 current_entry['bullets'].append(line.lstrip('•-* ').strip())
             else:
                 if 'skills' not in current_entry and (',' in line or any(k in line.lower() for k in ['java', 'python', 'c++', 'react'])):
                      current_entry['skills'] = line.strip()
                 else:
                      current_entry['bullets'].append(line.strip())
                 
    if current_entry:
        entries.append(current_entry)

    return entries


def parse_skills(text: str) -> List[Dict[str, Any]]:
    entries = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    for line in lines:
        if ":" in line:
            cat, skills = line.split(":", 1)
            entries.append({"category": cat.strip(), "skills": skills.strip()})
        else:
            entries.append({'category': 'General', 'skills': line})
            
    return entries


def parse_date_str(date_str: str):
    if not date_str or date_str.lower() == "present":
        return "", ""
    try:
        parts = date_str.split()
        if len(parts) == 2:
            month_str = parts[0][:3].lower()  # jan, feb...
            year = parts[1]

            months = {
                "jan": "01",
                "feb": "02",
                "mar": "03",
                "apr": "04",
                "may": "05",
                "jun": "06",
                "jul": "07",
                "aug": "08",
                "sep": "09",
                "oct": "10",
                "nov": "11",
                "dec": "12",
            }
            return months.get(month_str, ""), year
    except:
        pass
    return "", ""
