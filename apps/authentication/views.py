from django.utils import timezone

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse


from google.oauth2 import id_token as google_id_token

from core.responses import build_response, swagger_response
from core.validators import verify_email_address, verify_phone_number
from core.identifiers import create_username, generate_otp
from core.communication import sending_email, sending_sms
from core.cookies import set_access_cookie, set_refresh_cookie, clear_auth_cookies
from core.groups import add_user_to_group, remove_user_to_group, clear_user_groups
from core.network import get_client_ip


from .serializers import LoginSerializers, LoginResponseSerializers, OTPSerializers, AuthSuccessSerializers, GoogleLoginSerializer, AccountProfileSerializer, AgreementSerializer, AcceptAgreementsSerializer

from .models import OTP, BabyProfile, Agreement, AcceptedAgreement

User = get_user_model()


class OTPLoginThrottle(AnonRateThrottle):
    rate = "3/min"

class LoginView(APIView):
    permission_classes = []
    throttle_classes = [OTPLoginThrottle]

    @extend_schema(
        summary = "Login with phone or email",
        description = "Login with email or phone. Sends OTP to the given email or phone",
        request = LoginSerializers,
        tags = ["Auth"],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = LoginResponseSerializers,
                description = "Login successful",
                examples = [
                    swagger_response(
                        name = "Login success with email",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "OTP has been send to your email",
                        data={
                            "username":"bebelet_user"
                        }
                    ),
                    swagger_response(
                        name = "Login success with phone",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "OTP has been send to your phone",
                        data = {
                            "username":"bebelet_user"
                        }
                    ),
                ]
            ),
            status.HTTP_400_BAD_REQUEST : OpenApiResponse(
                response = LoginResponseSerializers,
                description = "Login Error",
                examples = [
                    swagger_response(
                        name="email and phone both exist",
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="You need to use only one(email or phone)",
                        data = {}
                    ),
                    swagger_response(
                        name="email is not valid",
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="You need to enter a valid email",
                        data = {}
                    ),
                    swagger_response(
                        name="phone is not valid",
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="You need to enter a valid phone number",
                        data = {}
                    ),
                    swagger_response(
                        name="email and phone are missing",
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="email or phone is required",
                        data = {},
                    )
                ]
            ),
            status.HTTP_403_FORBIDDEN : OpenApiResponse(
                response = LoginResponseSerializers,
                description = "Permission Error",
                examples = [
                    swagger_response(
                        name="User not active",
                        success = False,
                        code = status.HTTP_403_FORBIDDEN,
                        message = "User is not active",
                        data = {}
                    )
                ]
            ),
            status.HTTP_429_TOO_MANY_REQUESTS : OpenApiResponse(
                response = True,
                description = "Too many attempts",
                examples = [
                    swagger_response(
                        name="There is an active OTP",
                        success=False,
                        code=status.HTTP_429_TOO_MANY_REQUESTS,
                        message="OTP has already been send",
                        data = {
                            "username": "2026cARG1-kvJP1"
                        },
                    ),
                    swagger_response(
                        name="Many request",
                        success=False,
                        code=status.HTTP_429_TOO_MANY_REQUESTS,
                        message="Too many requests. Try again in 59 seconds.",
                        data = {},
                    )
                ]
            )
        }
    )
    def post(self, request):
        serializer = LoginSerializers(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data.get("email")
        phone = serializer.validated_data.get("phone")
        user = None
        OTP_LENGTH = settings.OTP_LENGTH

        if email or phone:
            if email and phone:
                payload = build_response(
                    success = False,
                    code = status.HTTP_400_BAD_REQUEST,
                    message = "You need to use only one(email or phone)",
                )
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)
            
            if email:
                email = email.strip().lower()
                if verify_email_address(email):
                    user, created = User.objects.get_or_create(email=email, defaults={'username': create_username()})
                else:
                    payload = build_response(
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="You need to enter a valid email"
                    )
                    return Response(payload, status=status.HTTP_400_BAD_REQUEST)

            if phone:
                if verify_phone_number(phone):
                    user, created = User.objects.get_or_create(phone=phone, defaults={"username" : create_username()})
                else:
                    payload = build_response(
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="You need to enter a valid phone number"
                    )
                    return Response(payload, status=status.HTTP_400_BAD_REQUEST)

            data = LoginResponseSerializers(user).data

            if not user.is_active:
                payload = build_response(
                    success = False,
                    code = status.HTTP_403_FORBIDDEN,
                    message = "User is not active",
                )
                return Response(payload, status=status.HTTP_403_FORBIDDEN)

            new_otp_list = OTP.objects.filter(user=user, expired_at__gte=timezone.now())

            if new_otp_list.exists():
                payload = build_response(
                    success = False,
                    code=status.HTTP_429_TOO_MANY_REQUESTS,
                    message="OTP has already been send",
                    data=data
                )
                return Response(payload, status=status.HTTP_429_TOO_MANY_REQUESTS)

            else:
                otp  = generate_otp(OTP_LENGTH)
                otp_data = OTP.objects.create(user=user, otp=otp)
                otp_data.save()


            if email:
                sending_email(subject="OTP Verification", message=f"Your OTP code is {otp}", email=email)
                payload = build_response(
                    success=True,
                    code=status.HTTP_200_OK,
                    message="OTP has been send to your email",
                    data=data
                )

                return Response(payload, status=status.HTTP_200_OK)

            if phone:
                sending_sms(message=f"Your OTP code is {otp}", phone=phone)
                payload = build_response(
                    success=True,
                    code=status.HTTP_200_OK,
                    message="OTP has been send to your phone",
                    data=data
                )

                return Response(payload, status=status.HTTP_200_OK)   
 
        else:
            payload = build_response(
                success=False,
                code=status.HTTP_400_BAD_REQUEST,
                message="email or phone is required"
            )
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)


class OTPView(APIView):
    permission_classes = []
    throttle_classes = [OTPLoginThrottle]

    @extend_schema(
            summary = "OTP verification",
            description = "Confirming auth with OTP code",
            request = OTPSerializers,
            tags = ["Auth"],
            responses = {
                status.HTTP_200_OK : OpenApiResponse(
                    response = AuthSuccessSerializers,
                    description = "OTP Verification Success",
                    examples = [
                        swagger_response(
                            name = "Login confirmation with OTP",
                            success = True,
                            code = status.HTTP_200_OK,
                            message = "OTP verified successfully",
                            data = {
                                "id": 1,
                                "username": "bebelet_user",
                                "groups": [
                                    2
                                ],
                                "permissions": []
                            }
                        ),

                    ]
                ),
                status.HTTP_400_BAD_REQUEST : OpenApiResponse(
                    response = AuthSuccessSerializers,
                    description = "OTP Verification Error",
                    examples = [
                        swagger_response(
                            name = "username is missing",
                            success = False,
                            code = status.HTTP_400_BAD_REQUEST,
                            message = "username is required",
                            data = {}
                        ),
                        swagger_response(
                            name = "otp is missing",
                            success = False,
                            code = status.HTTP_400_BAD_REQUEST,
                            message = "otp is required",
                            data = {},
                        ),
                        swagger_response(
                            name = "otp is not string",
                            success = False,
                            code = status.HTTP_400_BAD_REQUEST,
                            message = "otp must be an string",
                            data = {},
                        ),
                        swagger_response(
                            name = "username is not valid",
                            success = False,
                            code = status.HTTP_400_BAD_REQUEST,
                            message = "username is not valid",
                            data = {}
                        ),
                        swagger_response(
                            name = "Invalid OTP",
                            success = False,
                            code = status.HTTP_400_BAD_REQUEST,
                            message = "Invalid or expired OTP",
                            data = {}
                        )
                    ]
                ),
                status.HTTP_429_TOO_MANY_REQUESTS : OpenApiResponse(
                    response = AuthSuccessSerializers,
                    description = "Too many attempts",
                    examples = [
                        swagger_response(
                            name="Many request",
                            success=False,
                            code=status.HTTP_429_TOO_MANY_REQUESTS,
                            message="Too many requests. Try again in 59 seconds.",
                            data = {}
                            )
                    ]
                )

            }
        )
    def post(self, request):
        serializer = OTPSerializers(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        username = serializer.validated_data.get("username")
        otp = serializer.validated_data.get("otp")

        if not username:
            payload = build_response(
                success=False,
                code=status.HTTP_400_BAD_REQUEST,
                message="username is required"
            )
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)
        
        if not otp:
            payload = build_response(
                success = False,
                code = status.HTTP_400_BAD_REQUEST,
                message="otp is required"
            )
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(otp, str):
            payload = build_response(
                success = False,
                code = status.HTTP_400_BAD_REQUEST,
                message = "otp must be an string"
            )
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_instance = User.objects.get(username=username)
        
        except User.DoesNotExist:
            payload = build_response(
                success = False,
                code = status.HTTP_400_BAD_REQUEST,
                message = "username is not valid"
            )

        print("User:", user_instance)
        

        try:
            otp_instance = OTP.objects.get(user=user_instance, otp=otp, expired_at__gte=timezone.now())

            refresh = RefreshToken.for_user(user_instance)
            access = str(refresh.access_token)

            add_user_to_group(user_instance, 'verified_user')

            payload = build_response(
                success = True,
                code = status.HTTP_200_OK,
                message = "OTP verified successfully",
                data = AuthSuccessSerializers(user_instance).data
            )

            response = Response(payload, status.HTTP_200_OK)
            set_access_cookie(response, access)
            set_refresh_cookie(response, str(refresh))
            #otp_instance.delete()
            return response
            
        except OTP.DoesNotExist:
            payload = build_response(
                success = False,
                code = status.HTTP_400_BAD_REQUEST,
                message = "Invalid or expired OTP"
            )

            return Response(payload, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginView(APIView):
    permission_classes = []
    throttle_classes = [OTPLoginThrottle]

    @extend_schema(
            summary = "Google Login",
            description = "Logging in with googleAuth",
            request = GoogleLoginSerializer,
            tags = ["Auth"],
            responses = {
                status.HTTP_200_OK : OpenApiResponse(
                    response = True,
                    description = "OTP Verification Success",
                    examples = [
                        swagger_response(
                            name = "Login with Google Auth",
                            success = True,
                            code = status.HTTP_200_OK,
                            message = "The login with google was successful",
                            data = {
                                "id": 1,
                                "username": "bebelet_user",
                                "groups": [
                                    2
                                ],
                                "permissions": []
                            }
                        ),
                    ]
                ),
                status.HTTP_400_BAD_REQUEST : OpenApiResponse(
                    response = True,
                    description = "OTP Verification Error",
                    examples = [
                        swagger_response(
                            name = "iss is missing",
                            success = False,
                            code = status.HTTP_400_BAD_REQUEST,
                            message = "Invalid iss",
                            data = {}
                        ),
                        swagger_response(
                            name = "email is not verified",
                            success = False,
                            code = status.HTTP_400_BAD_REQUEST,
                            message = "Google email not verified",
                            data = {}
                        ),
                        swagger_response(
                            name = "email is not found",
                            success = False,
                            code = status.HTTP_400_BAD_REQUEST,
                            message = "Email not found",
                            data = {}
                        ),
                    ]
                ),
                status.HTTP_429_TOO_MANY_REQUESTS : OpenApiResponse(
                    response = True,
                    description = "Too many attempts",
                    examples = [
                        swagger_response(
                            name="Many request",
                            success=False,
                            code=status.HTTP_429_TOO_MANY_REQUESTS,
                            message="Too many requests. Try again in 59 seconds.",
                            data = {}
                            )
                    ]
                )
            }
        )
    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializers.errors, status=status.HTTP_400_BAD_REQUEST)

        id_token_raw = serializers.validated_data.get("id_token")

        try:
            idinfo = google_id_token.verify_oauth2_token(
                id_token_raw,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )

            if idinfo.get("iss") not in ["https://accounts.google.com", "accounts.google.com"]:
                payload = build_response(
                    success=False, 
                    code=status.HTTP_400_BAD_REQUEST, 
                    message="Invalid iss"
                )
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)

            if not idinfo.get("email_verified"):
                payload = build_response(
                    success=False, 
                    code=status.HTTP_400_BAD_REQUEST, 
                    message="Google email not verified"
                )
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)

            email = idinfo.get("email")
            given_name = idinfo.get("given_name") or ""
            family_name = idinfo.get("family_name") or ""


            if not email:
                payload = build_response(
                    success=False, 
                    code=status.HTTP_400_BAD_REQUEST, 
                    message="Email not found"
                )
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)

            user, _ = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    "username": create_username(),
                    "first_name": given_name,
                    "last_name": family_name,
                },
            )

            refresh = RefreshToken.for_user(user)
            access = str(refresh.access_token)
            payload = build_response(
                success=True, 
                code=status.HTTP_200_OK, 
                message="The login with google was successful",
                data = {
                    "id" : user_instance.id,
                    "username" : user_instance.username,
                }
            )
            response = Response(payload, status=status.HTTP_200_OK)
            set_access_cookie(response, access)
            set_refresh_cookie(response, str(refresh))
            return response
        
        except Exception:
            payload = api_response(success=False, code=status.HTTP_400_BAD_REQUEST, message="Google token verification failed", data=None)
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)


class RefreshView(APIView):
    permission_classes = []

    @extend_schema(
            summary = "Refresh",
            description = "Refresh Access Token",
            tags = ["Auth"],
            responses = {
                status.HTTP_200_OK : OpenApiResponse(
                    response = True,
                    description = "Token Refresh Success",
                    examples = [
                        swagger_response(
                            name = "Token Refreshed",
                            success = True,
                            code = status.HTTP_200_OK,
                            message = "Token refreshed successfully.",
                            data = {}
                        ),
                    ]
                ),
                status.HTTP_401_UNAUTHORIZED : OpenApiResponse(
                    response = True,
                    description = "OTP Verification Error",
                    examples = [
                        swagger_response(
                            name = "Refresh token is missing",
                            success = False,
                            code = status.HTTP_401_UNAUTHORIZED,
                            message = "Authentication credentials were not provided.",
                            data = {}
                        ),
                        swagger_response(
                            name = "Invalid Refresh Token",
                            success= False,
                            code = status.HTTP_401_UNAUTHORIZED,
                            message = "Invalid refresh token.",
                            data = {}
                        )
                    ]
                )
            }
        )
    def post(self, request):
        refresh = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)

        if not refresh:
            payload = build_response(
                success = False,
                code = status.HTTP_401_UNAUTHORIZED,
                message="Authentication credentials were not provided."
            )
            return Response(payload, status=status.HTTP_401_AUTHORIZED)

        try:
            refresh_token = RefreshToken(refresh)
            new_access = str(refresh_token.access_token)


        except Exception:
            payload = build_response(
                success = False,
                code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid refresh token."
            )
            return Response(payload, status=status.HTTP_401_AUTHORIZED)


        payload = build_response(
            success=True,
            code=status.HTTP_200_OK,
            message="Token refreshed successfully.",
        )
        response = Response(payload, status.HTTP_200_OK)
        set_access_cookie(response, new_access)
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
            summary = "User Info",
            description = "Gettings authenticated user information",
            tags = ["Auth"],
            responses = {
                status.HTTP_200_OK : OpenApiResponse(
                    response = True,
                    description = "Me Success",
                    examples = [
                        swagger_response(
                            name = "Getting user info",
                            success = True,
                            code = status.HTTP_200_OK,
                            message = "User info retrieved successfully",
                            data = {
                                "id" : 1,
                                "username": "bebelet_user"
                            }
                        ),
                    ]
                ),
                status.HTTP_403_FORBIDDEN : OpenApiResponse(
                    response = True,
                    description = "Me Error",
                    examples = [
                        swagger_response(
                            name = "Unauthenticated User",
                            success = False,
                            code = status.HTTP_403_FORBIDDEN,
                            message = "Authentication credentials were not provided.",
                            data = {
                                "detail": "Authentication credentials were not provided."
                            }
                        )
                    ]
                )
            }
        )
    def get(self, request):
        user = request.user
        

        payload = build_response(
            success=True,
            code = status.HTTP_200_OK,
            message = "User info retrieved successfully",
            data = {
                "id" : user.id,
                "username" : user.username,
            }
        )

        return Response(payload, status.HTTP_200_OK)

class ProfileMeView(APIView):
    permission_classes = [IsAuthenticated]
     
    @extend_schema(
        summary = "Profile",
        description = "Gettings profile",
        tags = ["Auth"],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = True,
                description = "Get profile success",
                examples = [
                    swagger_response(
                        name = "Getting user info",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Profile retrieved successfully",
                        data = {
                            "profile_first_name": "John",
                            "profile_last_name": "Doe",
                            "profile_picture_url": "http://example.com/profile.jpg",
                            "about_me": "I am a new parent.",
                        }
                    ),
                ]
            ),
            status.HTTP_404_NOT_FOUND : OpenApiResponse(
                response = True,
                description = "Get profile error response",
                examples = [
                    swagger_response(
                        name = "User not found",
                        success = False,
                        code = status.HTTP_404_NOT_FOUND,
                        message = "User not found",
                        data = {}
                    )
                ]
            )
        }
    )
    def get(self, request):
        user = request.user
        try:
            user_profile_pic = User.objects.get(id=user.id).get_profile_picture_url
        except User.DoesNotExist:
            payload = build_response(
                success = False,
                code = status.HTTP_404_NOT_FOUND,
                message = "User not found"
            )
            return Response(payload, status.HTTP_404_NOT_FOUND)

        baby_profile, _ = BabyProfile.objects.get_or_create(user=user)

        data = {
            "profile_first_name": user.first_name or "",
            "profile_last_name": user.last_name or "",
            "profile_picture_url": user_profile_pic or "",
            "about_me": user.about_me or "",
            "baby_gender": baby_profile.baby_gender or "",
            "baby_age": baby_profile.baby_age or "",
            "email": user.email or "",
            "phone": user.phone or "",
        }

        serializer = AccountProfileSerializer(instance=data)
        payload = build_response(
            success=True,
            code=status.HTTP_200_OK,
            message="Profile retrieved successfully",
            data=serializer.data,
        )
        return Response(payload, status=status.HTTP_200_OK)


    @extend_schema(
        summary = "Profile",
        request = AccountProfileSerializer,
        description = "Updating profile",
        tags = ["Auth"],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = True,
                description = "Update profile success",
                examples = [
                    swagger_response(
                        name = "Update profile success",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Profile updated successfully",
                        data = {}
                    ),
                ]
            ),
            status.HTTP_400_BAD_REQUEST : OpenApiResponse(
                response = True,
                description = "Update profile error response",
                examples = [
                    swagger_response(
                        name = "Invalid baby_gender",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Invalid baby_gender",
                        data = {}
                    ),
                    swagger_response(
                        name = "Invalid email format",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Invalid email format",
                        data = {}
                    ),
                    swagger_response(
                        name = "Invalid phone number",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Invalid phone number",
                        data = {}
                    ),
                ]
            ),
            status.HTTP_409_CONFLICT : OpenApiResponse(
                response = True,
                description = "Update profile conflict response",
                examples = [
                    swagger_response(
                        name = "Email already in use",
                        success = False,
                        code = status.HTTP_409_CONFLICT,
                        message = "Email already in use",
                        data = {}
                    ),
                    swagger_response(
                        name = "Phone number already in use",
                        success = False,
                        code = status.HTTP_409_CONFLICT,
                        message = "Phone number already in use",
                        data = {}
                    ),
                ]
            ),
        }
    )
    def put(self, request):
        user = request.user
        serializer = AccountProfileSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data

            # Update basic profile info
            if "profile_picture" in data:
                user.profile_picture = data["profile_picture"]

            if "about_me" in data:
                user.about_me = data["about_me"]

            if "profile_first_name" in data:
                user.first_name = data["profile_first_name"]

            if "profile_last_name" in data:
                user.last_name = data["profile_last_name"]

            user.save()

            # Update baby profile info
            if "baby_gender" in data or "baby_age" in data:
                baby_profile, _ = BabyProfile.objects.get_or_create(user=user)

                if "baby_gender" in data:
                    if data["baby_gender"] not in GenderChoices.values:
                        payload = api_response(
                            success=False,
                            code=status.HTTP_400_BAD_REQUEST,
                            message="Invalid baby_gender",
                        )

                        return Response(
                            payload,
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    baby_profile.baby_gender = data["baby_gender"]

                if "baby_age" in data:
                    baby_profile.baby_age = data["baby_age"]

                baby_profile.save()

            # cannot receive otp to both phone and email at the same time
            if "email" in data and "phone" in data:
                new_email = data["email"]
                new_phone = data["phone"]
                if new_email != user.email and new_phone != user.phone:
                    payload = api_response(
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="You cannot change both email and phone at the same time",
                    )
                    return Response(payload, status=status.HTTP_400_BAD_REQUEST)

            # Validate email
            if "email" in data:
                new_email = data["email"]

                if new_email != user.email:
                    if not verify_email_address(new_email):
                        payload = api_response(
                            success=False,
                            code=status.HTTP_400_BAD_REQUEST,
                            message="Invalid email format",
                        )
                        return Response(payload,status=status.HTTP_400_BAD_REQUEST)

                    if CustomUser.objects.filter(email=new_email).exclude(
                        id=user.id
                    ).exists():
                        payload = api_response(
                            success=False,
                            code=status.HTTP_409_CONFLICT,
                            message="Email already in use",
                        )
                        return Response(payload, status=status.HTTP_409_CONFLICT)
                        

                    # check if the user has already active OTP code
                    if OTP.objects.filter(
                        user=user, expired_at__gte=timezone.now()
                    ).exists():
                        payload = api_response(
                            success=False,
                            code=status.HTTP_429_TOO_MANY_REQUESTS,
                            message="User has already an active OTP",
                        )
                        return Response(payload, status=status.HTTP_429_TOO_MANY_REQUESTS)

                    # save the new email to pending_email
                    user.pending_email = new_email
                    user.save()
                    # create an OTP and return it
                    OTP_LENGTH = int(get_setting("OTP_LENGTH"))
                    otp = generate_otp(OTP_LENGTH)
                    # in case it generates duplicated otp...
                    while OTP.objects.filter(user=user, otp=otp).exists():
                        otp = generate_otp(OTP_LENGTH)
                    otp_instance = OTP.objects.create(user=user, otp=otp)
                    otp_instance.save()

                    # ########################### IMPORTANT  ###########
                    # below line will be uncommented in server
                    # EmailMessage('OTP Verification', f'Your OTP code is {otp}', to=[new_email]).send()
                    payload = api_response(
                        success=True,
                        code=status.HTTP_200_OK,
                        message="OTP has been send to your email",
                        data={"username": user.username},
                    )
                    return Response(payload, status=status.HTTP_200_OK)


            # Validate phone
            if "phone" in data:
                new_phone = request.data.get("phone")
                if new_phone != user.phone:
                    if not verify_phone_number(new_phone):
                        payload = api_response(
                            success=False,
                            code=status.HTTP_400_BAD_REQUEST,
                            message="Invalid phone number",
                        )
                        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

                    if CustomUser.objects.filter(phone=new_phone).exclude(
                        id=user.id
                    ).exists():
                        payload = api_response(
                            success=False,
                            code=status.HTTP_409_CONFLICT,
                            message="Phone number already in use",
                        )
                        return Response(payload, status=status.HTTP_409_CONFLICT)

                    # check if the user has already active OTP code
                    if OTP.objects.filter(
                        user=user, expired_at__gte=timezone.now()
                    ).exists():
                        payload = api_response(
                            success=False,
                            code=status.HTTP_429_TOO_MANY_REQUESTS,
                            message="User has already an active OTP",
                        )
                        return Response(payload, status=status.HTTP_429_TOO_MANY_REQUESTS)
                    # save the new phone to pending_phone
                    user.pending_phone = new_phone
                    user.save()
                    OTP_LENGTH = int(get_setting("OTP_LENGTH"))
                    otp = generate_otp(OTP_LENGTH)
                    # in case it generates duplicate otp
                    while OTP.objects.filter(user=user, otp=otp).exists():
                        otp = generate_otp(OTP_LENGTH)
                    otp_instance = OTP.objects.create(user=user, otp=otp)
                    otp_instance.save()

                    payload = api_response(
                        success=True,
                        code=status.HTTP_200_OK,
                        message="OTP has been send to your phone",
                        data={"username": user.username},
                    )
                    return Response(payload, status=status.HTTP_200_OK)
                    # OTP will be sent to pending_phone here ..

            payload = api_response(
                success=True,
                code=status.HTTP_200_OK,
                message="Profile updated",
            )
            return Response(payload, status=status.HTTP_200_OK)

        payload = api_response(
            success=False,
            code=status.HTTP_400_BAD_REQUEST,
            message="Invalid data",
        )
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)


class AgreementListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary = "Agreement List",
        description = "List all active agreements. Optional: filter by type (terms, privacy, contract).",
        tags = ["Auth"],
        parameters = [
            OpenApiParameter(
                name="type",
                required=False,
                type=OpenApiTypes.STR,
                description="Filter agreements by type (e.g. 'terms', 'privacy', 'contract').",
            )
        ],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = True,
                description = "Agreements list success response",
                examples = [
                    swagger_response(
                        name = "Agreements list success",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Agreements retrieved successfully",
                        data = [
                            {
                                "id": 1,
                                "title": "Terms of Service",
                                "version": "1.0",
                                "is_active": True,
                                "agreement_type": "terms",
                            },
                            {
                                "id": 2,
                                "title": "Privacy Policy",
                                "version": "1.0",
                                "is_active": True,
                                "agreement_type": "privacy",
                            },
                        ],
                    ),
                ]
            )
        }
    )
    def get(self, request):
        agreement_type = request.query_params.get("type")

        agreements = Agreement.objects.filter(is_active=True)
        if agreement_type:
            agreements = agreements.filter(agreement_type=agreement_type)

        serializer = AgreementSerializer(agreements, many=True)
        payload = build_response(
            success=True,
            code=status.HTTP_200_OK,
            message="Agreements retrieved successfully",
            data=serializer.data,
        )
        return Response(payload, status=status.HTTP_200_OK)

class PendingAgreementListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary = "Pending Agreement List",
        description = "List all active agreements the current user has NOT yet accepted.",
        tags = ["Auth"],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = True,
                description = "Pending Agreements List success response",
                examples = [
                    swagger_response(
                        name = "Pending Agreements list success",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Agreements retrieved successfully",
                        data = [
                            {
                                "id": 1,
                                "title": "Terms of Service",
                                "version": "1.0",
                                "is_active": True,
                                "agreement_type": "terms",
                            },
                            {
                                "id": 2,
                                "title": "Privacy Policy",
                                "version": "1.0",
                                "is_active": True,
                                "agreement_type": "privacy",
                            },
                        ],
                    ),
                ]
            )
        }
    )
    def get(self, request):
        user = request.user
        all_active = Agreement.objects.filter(is_active=True)
        accepted_ids = AcceptedAgreement.objects.filter(user=user).values_list(
            "agreement_id", flat=True
        )

        unaccepted = all_active.exclude(id__in=accepted_ids)

        serializer = AgreementSerializer(unaccepted, many=True)

        payload = build_response(
            success=True,
            code=status.HTTP_200_OK,
            message="Pending agreements retrieved successfully",
            data=serializer.data,
        )

        return Response(payload, status=status.HTTP_200_OK)


class AcceptAgreementsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary = "Accept Agreements",
        description = "Accept one or more agreements by ID",
        tags = ["Auth"],
        request= AcceptAgreementsSerializer,
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = True,
                description = "Accept aggrements by ID",
                examples = [
                    swagger_response(
                        name = "Agreements accepted successfully",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Agreements accepted successfully",
                        data = {
                            "accepted": [1,2,3]
                        },
                    ),
                ]
            ),
            status.HTTP_404_NOT_FOUND : OpenApiResponse(
                response = True,
                description = "No new agreements",
                examples = [
                    swagger_response(
                        name = "No new agreements to accept",
                        success = True,
                        code = status.HTTP_404_NOT_FOUND,
                        message = "No new agreements to accept",
                        data = {
                            "accepted": [1,2,3]
                        },
                    ),
                ]
            )
        }
    )
    def post(self, request):
        serializer = AcceptAgreementsSerializer(data=request.data)
        if not serializer.is_valid():
            payload = api_response(
                success=False,
                code=status.HTTP_400_BAD_REQUEST,
                message="Invalid data",
                data=serializer.errors,
            )
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        agreement_ids = serializer.validated_data["agreement_ids"]
        ip_address = get_client_ip(request)

        accepted_ids = AcceptedAgreement.objects.filter(user=user).values_list(
            "agreement_id", flat=True
        )

        to_accept = Agreement.objects.filter(
            id__in=agreement_ids, is_active=True
        ).exclude(id__in=accepted_ids)

        if len(to_accept) == 0:
            payload = build_response(
                success=False,
                code=status.HTTP_404_NOT_FOUND,
                message="No new agreements to accept",
            )
            return Response(
                payload,
                status=status.HTTP_404_NOT_FOUND,
            )

        accepted = []
        for agreement in to_accept:
            AcceptedAgreement.objects.create(
                user=user,
                agreement=agreement,
                IP_address=ip_address,
                accepted_date=timezone.now(),
            )
            accepted.append(agreement.id)

        payload = build_response(
            success=True,
            code=status.HTTP_200_OK,
            message="Agreements accepted successfully",
            data={
                "accepted": accepted
            },
        )
        return Response(
            payload,
            status=status.HTTP_200_OK,
        )

class LogoutView(APIView):
    permission_classes = []
    throttle_classes = [OTPLoginThrottle]


    @extend_schema(
        summary = "User Info",
        description = "Gettings authenticated user information",
        tags = ["Auth"],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = True,
                description = "Me Success",
                examples = [
                    swagger_response(
                        name = "Logout Success",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Logged out successfully",
                        data = {}
                    ),
                ]
            ),
            status.HTTP_406_NOT_ACCEPTABLE : OpenApiResponse(
                response = True,
                description = "Already Logged Out",
                examples = [
                    swagger_response(
                        name = "Unauthenticated User",
                        success = False,
                        code = status.HTTP_406_NOT_ACCEPTABLE,
                        message = "Already logged out",
                        data = {}
                    )
                ]
            )
        }
    )
    def post(self, request):
        if not request.COOKIES.get(settings.AUTH_COOKIE_ACCESS) and not request.COOKIES.get(settings.AUTH_COOKIE_REFRESH):
            payload = build_response(
                success = False,
                code = status.HTTP_406_NOT_ACCEPTABLE,
                message = "Already logged out"
            )
            return Response(payload, status.HTTP_406_NOT_ACCEPTABLE)

        payload = build_response(
            success = True,
            code = status.HTTP_200_OK,
            message = "Logged out successfully"
        )
        response = Response(payload, status= status.HTTP_200_OK)
        clear_auth_cookies(response)
        return response