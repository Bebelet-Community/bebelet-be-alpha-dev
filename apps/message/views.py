from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.permissions import HasPerm
from core.responses import build_response, swagger_response


class MessageView(ModelViewSet):
    authentication_classes = [IsAuthenticated]

    def get_new_messages_count(self):
        user = self.request.user

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Conversation.objects.filter(
                Q(conversationmember__user=user, conversationmember__is_deleted=False) | 
                Q(conversation_type="announcement",) | 
                Q(conversation_type="support")).distinct().order_by('-updated_at')
        else:
            return Conversation.objects.filter(Q(conversationmember__user=user, conversationmember__is_deleted=False) | Q(conversation_type="announcement")).distinct().order_by('-updated_at')
    
    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return response_success("Conversations retrieved successfully", data=serializer.data)

    def retrieve(self, request, pk=None):
        try:
            conversation_instance=Conversation.objects.get(unique_id=pk)
            if conversation_instance.conversation_type != "announcement":
                if request.user.is_superuser and conversation_instance.conversation_type == "support":
                    serializer = ConversationDetailSerializer(conversation_instance)
                    return response_success("Conversation details retrieved successfully", data=serializer.data)
                else:
                    if not ConversationMember.objects.filter(conversation=conversation_instance, user=request.user, is_deleted=False).exists():
                        return response_error("You are not a member of this conversation", status_code=status.HTTP_403_FORBIDDEN)
                    message_list = Message.objects.filter(conversation=conversation_instance).exclude(messagereluser__is_deleted=True)
                    for message in message_list:
                        MessageRelUser.objects.get_or_create(message=message, user=request.user)
                        MessageRelUser.objects.filter(message=message, user=request.user, is_read=False).update(is_read=True)
                    serializer = ConversationDetailSerializer(conversation_instance)
                    return response_success("Conversation details retrieved successfully", data=serializer.data)
            else:
                serializer = ConversationDetailSerializer(conversation_instance)
                message_list = Message.objects.filter(conversation=conversation_instance).exclude(messagereluser__is_deleted=True)
                for message in message_list:
                    MessageRelUser.objects.get_or_create(message=message, user=request.user)
                    MessageRelUser.objects.filter(message=message, user=request.user, is_read=False).update(is_read=True)
                return response_success("Conversation details retrieved successfully", data=serializer.data)
        except Conversation.DoesNotExist:
            return response_error("Conversation not found", status_code=status.HTTP_404_NOT_FOUND)

    
    def create(self, request):
        user = request.user
        data = request.data

        conversation_type = data.get("conversation_type")
        salepost_id = data.get("salepost_id")
        title = (data.get("title") or "").strip()
        content = (data.get("content") or "").strip()
        conversation_uid = data.get("conversation_id")
        receiver_id = data.get("receiver_id")

        if conversation_type not in ["private", "support", "announcement"]:
            return response_error(message="Invalid conversation_type")
        if not content:
            return response_error(message="content is required")
        if conversation_uid:
            if conversation_type:
                return response_error(message="conversation_type should not be provided when conversation_id is given")
            if salepost_id:
                return response_error(message="salepost_id should not be provided when conversation_id is given")
            if title:
                return response_error(message="title should not be provided when conversation_id is given")
            if receiver_id:
                return response_error(message="receiver_id should not be provided when conversation_id is given")

            try:
                conversation_instance=Conversation.objects.get(unique_id=conversation_uid)
                if conversation_instance.conversation_type == "private":
                    if not ConversationMember.objects.filter(conversation=conversation_instance, user=user, is_deleted=False).exists():
                        return response_error(message="You are not a member of this conversation", status_code=status.HTTP_403_FORBIDDEN)
                else:
                    if not user.is_superuser and not ConversationMember.objects.filter(conversation=conversation_instance, user=user, is_deleted=False).exists():
                        return response_error(message="You are not authorized to access this conversation", status_code=status.HTTP_403_FORBIDDEN)
            except Conversation.DoesNotExist:
                return response_error(message="Conversation not found", status_code=status.HTTP_404_NOT_FOUND)

            message_instance = Message.objects.create(conversation=conversation_instance, sender=user, content=content)
            conversationmember_instance = ConversationMember.objects.filter(conversation=conversation_instance, is_deleted=True)
            for member in conversationmember_instance:
                member.is_deleted = False
                member.save()
            conversation_instance.updated_at = message_instance.created_at
            conversation_instance.save()
            return response_success(message="Message sent successfully", data={"conversation_id": conversation_instance.unique_id, "message_id": message_instance.id})
        else:
            if conversation_type == "private":
                if not salepost_id:
                    return response_error(message="salepost_id is required")
                if title:
                    return response_error(message="title should not be provided")

                try:
                    salepost_instance = SalePost.objects.get(id=salepost_id)
                except SalePost.DoesNotExist:
                    return response_error(message="SalePost not found", status_code=status.HTTP_404_NOT_FOUND)

                try:
                    conversation_instance = Conversation.objects.get(salepost_id=salepost_instance, conversationmember__user=user)
                    conversationmembers = ConversationMember.objects.filter(conversation=conversation_instance, is_deleted=True)
                    if conversationmembers.exists():
                        for member in conversationmembers:
                            if member.is_deleted:
                                member.is_deleted = False
                                member.save()
                except Conversation.DoesNotExist:
                    conversation_instance = Conversation.objects.create(
                        unique_id=generate_conversation_unique_id(),
                        salepost=salepost_instance,
                        title=f"{user.id}{salepost_instance.id} - {salepost_instance.post_title}",
                        conversation_type="private"
                    )
                    ConversationMember.objects.create(conversation=conversation_instance, user=user)
                    ConversationMember.objects.create(conversation=conversation_instance, user=salepost_instance.seller)

                message_instance = Message.objects.create(conversation=conversation_instance, sender=user, content=content)
                conversation_instance.updated_at = message_instance.created_at
                conversation_instance.save()

            elif conversation_type == "support":
                if not user.is_superuser:
                    return response_error(message="Only superusers can create support conversations", status_code=status.HTTP_403_FORBIDDEN)
                if salepost_id:
                    return response_error(message="salepost_id should not be provided for support conversations")
                if not title:
                    return response_error(message="title is required for support conversations")
                if not receiver_id:
                    return response_error(message="receiver_id is required for support conversations")
                if receiver_id == user.id:
                    return response_error(message="You cannot create a support conversation with yourself", status_code=status.HTTP_400_BAD_REQUEST)

                try:
                    receiver = CustomUser.objects.get(id=receiver_id)
                except CustomUser.DoesNotExist:
                    return response_error(message="User not found", status_code=status.HTTP_404_NOT_FOUND)

                conversation_instance=Conversation.objects.create(
                    unique_id=generate_conversation_unique_id(),
                    title=title,
                    conversation_type="support"
                )
                ConversationMember.objects.create(conversation=conversation_instance, user=receiver)
                message_instance = Message.objects.create(conversation=conversation_instance, sender=user, content=content)
                conversation_instance.updated_at = message_instance.created_at
                conversation_instance.save()

            else:
                if not user.is_superuser:
                    return response_error(message="Only superusers can create announcement conversations", status_code=status.HTTP_403_FORBIDDEN)
                if salepost_id:
                    return response_error(message="salepost_id should not be provided for announcement conversations")
                if not title:
                    return response_error(message="title is required for announcement conversations")
                if receiver_id:
                    return response_error(message="receiver_id should not be provided for announcement conversations")

                conversation_instance=Conversation.objects.create(
                    unique_id=generate_conversation_unique_id(),
                    title=title,
                    conversation_type="announcement"
                )
                message_instance = Message.objects.create(conversation=conversation_instance, sender=user, content=content)
                conversation_instance.updated_at = message_instance.created_at
                conversation_instance.save()
            return response_success(message="Message sent successfully", data={"conversation_id": conversation_instance.unique_id, "message_id": message_instance.id})
                

    def update(self, request, pk=None):
        return response_error(message="Method not allowed", status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, pk=None):
        return response_error(message="Method not allowed", status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, pk=None):
        try:
            conversation_instance = Conversation.objects.get(unique_id=pk)
            if conversation_instance.conversation_type == "private":
                try:
                    conversationmember_instance = ConversationMember.objects.get(conversation=conversation_instance, user=request.user)
                    conversationmember_instance.is_deleted = True
                    conversationmember_instance.save()
                    message_list = Message.objects.filter(conversation=conversation_instance)
                    for message in message_list:
                        messagereluser_instance = MessageRelUser.objects.filter(message=message, user=request.user).first()
                        if messagereluser_instance:
                            messagereluser_instance.is_deleted = True
                            messagereluser_instance.save()
                    return response_success(message="You have left the conversation successfully")
                except ConversationMember.DoesNotExist:
                    return response_error(message="You are not a member of this conversation", status_code=status.HTTP_403_FORBIDDEN)
            else:
                return response_error(message="You cannot leave this conversation", status_code=status.HTTP_403_FORBIDDEN)
        except Conversation.DoesNotExist:
            return response_error(message="Conversation not found", status_code=status.HTTP_404_NOT_FOUND)
            