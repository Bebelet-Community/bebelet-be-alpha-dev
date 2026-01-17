from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from cloudinary.models import CloudinaryField

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=10, unique=True, null=True, blank=True)
    profile_picture = CloudinaryField("profile_picture", blank=True, null=True)
    about_me = models.CharField(max_length=300, null=True, blank=True)
    pending_email = models.EmailField(null=True, blank=True, default=None)
    pending_phone = models.CharField(max_length=10, unique=True, null=True, blank=True, default=None)

    def __str__(self):
        return self.username

    @property
    def get_profile_picture_url(self):
        if not self.profile_picture:
            return ""
        return f"https://res.cloudinary.com/{CLOUDINARY_CLOUD_NAME}/{self.profile_picture}"


class OTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        EXPIRY_MINUTES = settings.OTP_EXPIRY_MINUTES

        if not self.expired_at:
            self.expired_at = timezone.now() + timezone.timedelta(minutes=EXPIRY_MINUTES)

        OTP.objects.filter(user=self.user, expired_at__lt = timezone.now()).delete()

        super().save(*args, **kwargs)

    def is_expired(self):
        if self.expired_at < timezone():
            self.delete()
            return True
        return False

    def __str__(self):
        return f"OPT for {self.user.username} - {self.otp}"


class GenderChoices(models.TextChoices):
    UNISEX = "unisex", "Unisex"
    MALE = "male", "Male"
    FEMALE = "female", "Female"


class BabyProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    baby_gender = models.CharField(max_length=10, choices=GenderChoices.choices, default=GenderChoices.UNISEX)
    baby_age = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Baby Profile of {self.user.username}"


class Agreement(models.Model):
    AGREEMENT_TYPE_CHOICES = [
        ("terms", "Terms and Conditions"),
        ("privacy", "Privacy Policy"),
        ("contract", "Contract"),
        # Add more types as needed
    ]

    agreement = models.TextField()
    agreement_type = models.CharField(max_length=20, choices=AGREEMENT_TYPE_CHOICES)
    released_date = models.DateTimeField(default=timezone.now)
    version = models.CharField(max_length=10, default="1.0")
    is_active = models.BooleanField(default=True)
    parent_agreement = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')

    def __str__(self):
        return self.agreement[:30].strip().replace("\n", " ")


class AcceptedAgreement(models.Model):
    agreement = models.ForeignKey(Agreement, on_delete=models.CASCADE, related_name="accepted_agreements")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="accepted_agreements")
    accepted_date = models.DateTimeField(default=timezone.now)
    IP_address = models.GenericIPAddressField()

    class Meta:
        unique_together = ("agreement", "user") 

    def __str__(self):
        return f"{self.user}'s agreement ->  {self.agreement}"