from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

class LoginSerializers(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.IntegerField(required=False)

class LoginResponseSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username']

class OTPSerializers(serializers.Serializer):
    username = serializers.CharField(required=True)
    otp = serializers.CharField(required=True)

class AuthSuccessSerializers(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id','username',"groups","permissions"]

    def get_permissions(self, obj):
        return sorted(obj.get_all_permissions())


class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField()


class AccountProfileSerializer(serializers.Serializer):
    profile_first_name = serializers.CharField(required=False)
    profile_last_name = serializers.CharField(required=False)
    profile_picture = serializers.ImageField(required=False)
    profile_picture_url = serializers.CharField(required=False)
    about_me = serializers.CharField(required=False)
    baby_gender = serializers.CharField(required=False)
    baby_age = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False, max_length=10)


class AgreementSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    agreement = serializers.CharField()
    agreement_type = serializers.CharField()
    version = serializers.CharField()
    released_date = serializers.DateTimeField()

class AcceptAgreementsSerializer(serializers.Serializer):
    agreement_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )
