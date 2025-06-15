import re

UNIVERSITY_EMAIL_DOMAINS = {
    'unsw.edu.au': 'University of New South Wales',
    'student.unsw.edu.au': 'University of New South Wales',
    'student.uwa.edu.au': 'University of Western Australia',
    'uwa.edu.au': 'University of Western Australia',
    'student.unimelb.edu.au': 'University of Melbourne',
    'unimelb.edu.au': 'University of Melbourne',
    'uni.sydney.edu.au': 'University of Sydney',
    'sydney.edu.au': 'University of Sydney',
    'students.curtin.edu.au': 'Curtin University',
    'curtin.edu.au': 'Curtin University',
    'student.qut.edu.au': 'Queensland University of Technology',
    'qut.edu.au': 'Queensland University of Technology',
    'student.adelaide.edu.au': 'University of Adelaide',
    'adelaide.edu.au': 'University of Adelaide',
    'students.cdu.edu.au': 'Charles Darwin University',
    'cdu.edu.au': 'Charles Darwin University',
    'students.mq.edu.au': 'Macquarie University',
    'mq.edu.au': 'Macquarie University',
    'students.deakin.edu.au': 'Deakin University',
    'deakin.edu.au': 'Deakin University',
    'student.csu.edu.au': 'Charles Sturt University',
    'csu.edu.au': 'Charles Sturt University',
    'student.rmit.edu.au': 'RMIT University',
    'rmit.edu.au': 'RMIT University',
    'student.swin.edu.au': 'Swinburne University of Technology',
    'swin.edu.au': 'Swinburne University of Technology',
    'student.uq.edu.au': 'University of Queensland',
    'uq.edu.au': 'University of Queensland',
    'student.canberra.edu.au': 'University of Canberra',
    'canberra.edu.au': 'University of Canberra',
    'students.flinders.edu.au': 'Flinders University',
    'flinders.edu.au': 'Flinders University',
    'student.latrobe.edu.au': 'La Trobe University',
    'latrobe.edu.au': 'La Trobe University',
    'students.acu.edu.au': 'Australian Catholic University',
    'acu.edu.au': 'Australian Catholic University',
    'students.bond.edu.au': 'Bond University',
    'bond.edu.au': 'Bond University',
    'students.jcu.edu.au': 'James Cook University',
    'jcu.edu.au': 'James Cook University',
    'students.anu.edu.au': 'Australian National University',
    'anu.edu.au': 'Australian National University',
    'students.usc.edu.au': 'University of the Sunshine Coast',
    'usc.edu.au': 'University of the Sunshine Coast',
    'students.scu.edu.au': 'Southern Cross University',
    'scu.edu.au': 'Southern Cross University',
    'students.vu.edu.au': 'Victoria University',
    'vu.edu.au': 'Victoria University',

    # 🔹 Added universities
    'murdoch.edu.au': 'Murdoch University',
    'student.murdoch.edu.au': 'Murdoch University',
    'newcastle.edu.au': 'University of Newcastle',
    'uon.edu.au': 'University of Newcastle',
    'students.uon.edu.au': 'University of Newcastle',
    'une.edu.au': 'University of New England',
    'students.une.edu.au': 'University of New England',
    'federation.edu.au': 'Federation University Australia',
    'students.federation.edu.au': 'Federation University Australia',
    'utas.edu.au': 'University of Tasmania',
    'students.utas.edu.au': 'University of Tasmania',
    'nd.edu.au': 'University of Notre Dame Australia',
    'my.nd.edu.au': 'University of Notre Dame Australia',
    'torrens.edu.au': 'Torrens University Australia',
    'students.torrens.edu.au': 'Torrens University Australia',
    'cqu.edu.au': 'Central Queensland University',
    'my.cqu.edu.au': 'Central Queensland University',
    'ecu.edu.au': 'Edith Cowan University',
    'our.ecu.edu.au': 'Edith Cowan University',
    'students.ecu.edu.au': 'Edith Cowan University',
}
def sanitize_domain(email):
    domain = email.split('@')[-1].lower()

    # Try exact match
    if domain in UNIVERSITY_EMAIL_DOMAINS:
        return UNIVERSITY_EMAIL_DOMAINS[domain]

    # Strip known prefixes like student., mail., etc.
    stripped = re.sub(r'^(student|students|alumni|mail|staff|info|admin|uni|my|our)\.', '', domain)
    if stripped in UNIVERSITY_EMAIL_DOMAINS:
        return UNIVERSITY_EMAIL_DOMAINS[stripped]

    # Try matching using base domain components
    base_domain = re.sub(r'\.(edu|ac|com|org|net)(\.[a-z]{2})?$', '', domain)
    for key in UNIVERSITY_EMAIL_DOMAINS:
        if base_domain in key:
            return UNIVERSITY_EMAIL_DOMAINS[key]

    # Fallback to last meaningful part
    fallback = base_domain.split('.')[-1].upper()
    return fallback


# 🔁 Generate mapping from slug → full university name
UNIVERSITY_SLUG_TO_NAME = {}

for domain, full_name in UNIVERSITY_EMAIL_DOMAINS.items():
    # Try to extract slug from domain using regex
    match = re.search(r'([a-z]+)\.(edu|ac)\.au$', domain)
    if match:
        slug = match.group(1).lower()
    else:
        # Fallback for unusual domains
        slug = domain.split('.')[0].lower()

    # Store slug mapping if not already present
    if slug not in UNIVERSITY_SLUG_TO_NAME:
        UNIVERSITY_SLUG_TO_NAME[slug] = full_name.title()