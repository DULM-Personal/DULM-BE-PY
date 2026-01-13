from django.shortcuts import render
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmailVerification
from .serializers import (
    SendCodeSerializer, VerifyCodeSerializer, RegisterSerializer,
    LoginSerializer, MeSerializer, ResetPasswordSerializer
)

class SendEmailCodeView(APIView):
    def post(self, request):
        s = SendCodeSerializer(data = request.data)
        s.is_valid(raise_exception=True)

        email = s.validated_data["email"]
        purpose = s.validated_data["purpose"]

        cooldown_since = timezone.now() - timedelta(minutes=1)
        recently_sent = EmailVerification.objects.filter(
            email=email,
            purpose=purpose,
            created_at__gte=cooldown_since,
        ).exists()

        if recently_sent:
            return Response(
                {"message": "인증 코드는 1분 후에 다시 요청할 수 있습니다."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        ver = EmailVerification.create_code(email=email, purpose=purpose, ttl_minutes=10)

        send_mail(
            subject = "[DULM] 이메일 인증 코드",
            message = f"인증 코드: {ver.code} (10분 내 입력)",
            from_email = None,
            recipient_list = [email],
        )

        return Response({"message": "인증 코드를 전송했습니다."})
    
class VerifyEmailCodeView(APIView):
    def post(self, request):
        s = VerifyCodeSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        email = s.validated_data["email"]
        purpose = s.validated_data["purpose"]
        code = s.validated_data["code"]

        ver = EmailVerification.objects.filter(
            email = email, purpose = purpose, code = code, is_used = False
        ).order_by("-created_at").first()

        if not ver:
            return Response({"message": "인증 코드가 올바르지 않습니다."}, status = 400)
        if ver.is_expired():
            return Response({"message": "인증 코드가 만료되었습니다."}, status = 400)
        if ver.code != code:
            return Response({"message": "인증 코드가 올바르지 않습니다."}, status = 400)
        
        ver.is_used = True
        ver.save(update_fields=["is_used"])

        return Response({"message": "이메일 인증이 완료되었습니다."})
    
class RegisterView(APIView):
    def post(self, request):
        s = RegisterSerializer(data = request.data)
        s.is_valid(raise_exception = True)
        user = s.create(s.validated_data)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )
    
class LoginView(APIView):
    def post(self, request):
        s = LoginSerializer(data = request.data)
        s.is_valid(raise_exception=True)

        user = s.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return Response({
            "accessToken": str(refresh.access_token),
            "refreshToken": str(refresh)
        })
    
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)
    
class ResetPasswordView(APIView):
    def post(self, request):
        s = ResetPasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        user = s.validated_data["user"]
        ver = s.validated_data["verification"]

        user.set_password(s.validated_data["newPassword"])
        user.save(update_fields=["password"])

        ver.is_used = True
        ver.save(update_fields=["is_used"])

        return Response({"message": "비밀번호가 재설정되었습니다."})
