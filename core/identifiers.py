import string
import secrets
import random

from datetime import datetime
from decouple import config

from django.contrib.auth import get_user_model

from apps.salepost.models import SalePost

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


def generate_unique_post_id():
    while True:
        new_id = random.randint(100000, 999999)  # 6-digit number
        if not SalePost.objects.filter(post_id=new_id).exists():
            return new_id