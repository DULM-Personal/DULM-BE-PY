from django.urls import path
from .views import (
    SendEmailCodeView, VerifyEmailCodeView,
    RegisterView, LoginView, MeView, ResetPasswordView
)

urlpatterns = [
    path("send-code", SendEmailCodeView.as_view()),
    path("verify-code", VerifyEmailCodeView.as_view()),
    path("register", RegisterView.as_view()),
    path("login", LoginView.as_view()),
    path("me", MeView.as_view()),
    path("reset-password", ResetPasswordView.as_view()),
]
