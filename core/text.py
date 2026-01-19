# this will be used to avoid the errors due to Turkish characters in regions

def turkish_lower(text: str) -> str:
    mapping = {
        'I': 'ı',
        'İ': 'i',
        'Ş': 'ş',
        'Ç': 'ç',
        'Ü': 'ü',
        'Ö': 'ö',
        'Ğ': 'ğ',
    }
    return ''.join(mapping.get(char, char.lower()) for char in text)