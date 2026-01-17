from django.contrib.auth import get_user_model
from datetime import datetime
import string
import secrets
from decouple import config

User = get_user_model()


def create_username():
    month = datetime.now().month
    year = datetime.now().year
    while True:
        username = f"{year}{secrets.token_urlsafe(10)[:10]}{month}"
        if not User.objects.filter(username=username).exists():
            return username

def generate_otp(length):
    if (config("ENVIRONMENT") == 'LOCAL' or config("ENVIRONMENT") == 'QA'):
        number = "0" * length
        return number
    else:
        number = secrets.randbelow(10 ** length)
        return f"{number:0{length}d}"
