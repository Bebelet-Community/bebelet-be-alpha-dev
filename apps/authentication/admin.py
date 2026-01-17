from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, OTP, BabyProfile, Agreement, AcceptedAgreement

class BabyProfileInline(admin.StackedInline):
    model = BabyProfile
    can_delete = False
    extra = 0


class AcceptedAgreementInline(admin.TabularInline):
    model = AcceptedAgreement
    extra = 0
    readonly_fields = ("accepted_date",)

class OTPInline(admin.TabularInline):
    model = OTP
    extra = 0

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    inlines = [
        BabyProfileInline,
        AcceptedAgreementInline,
        OTPInline
    ]


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("user", "otp", "created_at", "expired_at")
    list_filter = ("expired_at",)
    search_fields = ("expired_at",)

@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display = ("agreement", "is_active")
    list_filter = ("is_active",)
    search_fields = ("agreement",)
