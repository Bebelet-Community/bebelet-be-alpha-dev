from django.urls import path
from .views import LoginView, OTPView, GoogleLoginView, RefreshView, MeView, LogoutView, ProfileMeView, AgreementListView, PendingAgreementListView, AcceptAgreementsView


urlpatterns = [
    path("login/", LoginView.as_view()),
    path("otp-verify/", OTPView.as_view()),
    path("google/", GoogleLoginView.as_view()),
    path("refresh/", RefreshView.as_view()),
    path("me/", MeView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("profile/", ProfileMeView.as_view()),
    path("aggrements/", AgreementListView.as_view()),
    path("agreements/pending/", PendingAgreementListView.as_view()),
    path("agreements/accept/", AcceptAgreementsView.as_view()),
]