import re

def verify_email_address(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if(re.fullmatch(regex, email)):
        return True
    else:
        return False

def verify_phone_number(phone):
    operators = {"50","53","54","55","56"}

    if phone is None:
        return False

    digits = str(phone).strip()
    digits = "".join(ch for ch in digits if ch.isdigit())
    if len(digits) != 10:
        return False

    return digits[:2] in operators

