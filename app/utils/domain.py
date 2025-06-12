import re

def sanitize_domain(email):
    domain = email.split('@')[-1].lower()

    # Remove common prefixes like student., mail., alumni., etc.
    domain = re.sub(r'^(student|alumni|mail|staff|cs|it|info|admin)\.', '', domain)

    # Remove common TLD suffixes
    domain = re.sub(r'\.(edu|ac|com|org|net)(\.[a-z]{2})?$', '', domain)

    # Keep only last portion (e.g., curtin.edu.au → curtin)
    return domain.split('.')[-1]
