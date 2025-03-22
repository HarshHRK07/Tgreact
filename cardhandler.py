import re

# Expanded regex patterns for CC validation
CC_PATTERNS = [
    r'(\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4})\|(\d{2})\|(\d{2,4})\|(\d{3,4})',
    r'(\d{16})\|(\d{2})\|(\d{2,4})\|(\d{3,4})',
    r'(\d{13,19})\|(\d{2})\|(\d{2,4})\|(\d{3,4})',
    r'(\d{4}/\d{4}/\d{4}/\d{4})/(\d{2})/(\d{2,4})/(\d{3,4})',
    r'(\d{16})/(\d{2})/(\d{2,4})/(\d{3,4})',
    r'(\d{13,19})/(\d{2})/(\d{2,4})/(\d{3,4})',
    r'(\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4})/(\d{2})/(\d{2,4})/(\d{3,4})',
    r'(\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4})\|(\d{2})[/-](\d{2,4})\|(\d{3,4})',
    r'(\d{16})\|(\d{2})[/-](\d{2,4})\|(\d{3,4})',
    r'(\d{13,19})\|(\d{2})[/-](\d{2,4})\|(\d{3,4})',
    r'(\d{4}[.]?\d{4}[.]?\d{4}[.]?\d{4})\.(\d{2})\.(\d{2,4})\.(\d{3,4})',
    r'(\d{16})\.(\d{2})\.(\d{2,4})\.(\d{3,4})',
    r'(\d{13,19})\.(\d{2})\.(\d{2,4})\.(\d{3,4})',
    r'(\d{4}\s\d{4}\s\d{4}\s\d{4})\s(\d{2})\s(\d{2,4})\s(\d{3,4})',
    r'(\d{16})\s(\d{2})\s(\d{2,4})\s(\d{3,4})',
    r'(\d{13,19})\s(\d{2})\s(\d{2,4})\s(\d{3,4})',
    r'(\d{4}[-\s.]?\d{4}[-\s.]?\d{4}[-\s.]?\d{4})\|(\d{2})[/-](\d{2,4})\|(\d{3,4})',
    r'(\d{16})\|(\d{2})[/-](\d{2,4})\|(\d{3,4})',
    r'(\d{13,19})\|(\d{2})[/-](\d{2,4})\|(\d{3,4})',
    r'(\d{13,19})[|/\s.-]?(\d{2})[|/\s.-]?(\d{2,4})[|/\s.-]?(\d{3,4})',
]

def parse_cc_input(input_text):
    for pattern in CC_PATTERNS:
        match = re.search(pattern, input_text)
        if match:
            card_number = re.sub(r'[-\s./]', '', match.group(1))
            exp_month = match.group(2)
            exp_year = match.group(3)
            cvv = match.group(4)
            
            if not (13 <= len(card_number) <= 19 and 
                   len(exp_month) == 2 and 
                   2 <= len(exp_year) <= 4 and 
                   3 <= len(cvv) <= 4):
                continue
                
            if len(exp_year) == 4:
                exp_year = exp_year[-2:]
                
            return card_number, exp_month, exp_year, cvv
    return None