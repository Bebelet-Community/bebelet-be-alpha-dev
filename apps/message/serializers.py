from rest_framework import serializers
from .models import Conversation, ConversationMember, Message, MessageRelUser
from accounts.models import CustomUser
from django.db.models import Q


class ConversationSerializer(serializers.ModelSerializer):
    unread_messages_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['unique_id', 'title', 'conversation_type', 'created_at', "salepost", 'unread_messages_count']

    def get_unread_messages_count(self, obj):
        request = self.context.get("request")
        user = request.user
        messagereuser_objs = Message.objects.filter(conversation=obj).exclude(Q(messagereluser__is_deleted=False) | Q(messagereluser__is_read=True))
        return messagereuser_objs.count()

class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()
    class Meta:
        model = Conversation
        fields = ['unique_id', 'title', 'conversation_type', 'created_at', "salepost", 'messages']

    def get_messages(self, obj):
        messages = Message.objects.filter(conversation=obj).exclude(messagereluser__is_deleted=True).order_by('created_at')
        if messages.exists():
            return MessageSerializer(messages, many=True).data
        else:
            return None

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.SerializerMethodField()
    class Meta:
        model = Message
        fields = ['id', 'sender_username', 'content', 'created_at']


    def get_sender_username(self, obj):
        return obj.sender.username