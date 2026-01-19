from django.db import models
from django.contrib.auth import get_user_model
from apps.salepost.models import SalePost

User = get_user_model()

class ConversationType(models.TextChoices):
    private = 'private', 'Private'
    support = 'support', 'Support'
    announcement = 'announcement', 'Announcement'

class Conversation(models.Model):
    unique_id = models.CharField(max_length=20, unique=True)
    salepost = models.ForeignKey(SalePost, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=120)
    conversation_type = models.CharField(max_length=12, choices=ConversationType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.conversation_type})"


class ConversationMember(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('conversation', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.conversation.title}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} in {self.conversation.title}"

class MessageRelUser(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user')

    def __str__(self):
        return f"Message {self.message.id} for {self.user.username}"