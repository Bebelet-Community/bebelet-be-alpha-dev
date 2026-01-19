import uuid
from apps.message.models import Conversation
from django.utils import timezone

def generate_conversation_unique_id():
    # Create a unique identifier using UUID4 for 8 characters
    month = timezone.now().strftime("%m")
    year = timezone.now().strftime("%Y")[2:]
    unique_code = str(uuid.uuid4().hex[:16])
    code = f"{year}{month}{unique_code}"
    # Check if the unique code is already used
    while Conversation.objects.filter(unique_id=code).exists():
        unique_code = str(uuid.uuid4().hex[:16])
        code = f"{year}{month}{unique_code}"
    return code  