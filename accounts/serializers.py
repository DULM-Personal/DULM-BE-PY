from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import User, EmailVerification, validate_username

class SendCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=["SIGNUP", "RESET_PASSWORD"])

class VerifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=["SIGNUP", "RESET_PASSWORD"])
    code = serializers.CharField(min_length=6, max_length=6)

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField()
    password = serializers.CharField(min_length=8)

    def validate_username(self, value):
        validate_username(value)
        return value
    
    def validate(self, attrs):
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError({"email": "이미 사용 중인 이메일입니다."})
        if User.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError({"username": "이미 사용 중인 username입니다."})
        
        qs = EmailVerification.objects.filter(
            email=attrs["email"], purpose="SIGNUP", is_used=True
        ).order_by("-created_at")
        if not qs.exists():
            raise serializers.ValidationError({"email": "이메일 인증이 필요합니다."})
        return attrs
    
    def create(self, validated_data):
        return User.objects.create_user(
            username = validated_data["username"],
            email = validated_data["emial"],
            password = validated_data["password"],
        )

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password = attrs["password"])
        if not user:
            raise serializers.ValidatationError("아이디 또는 비밀번호가 올바르지 않습니다.")
        attrs["user"] = user
        return attrs
    
class MeSerializer(serializers.ModelSerializer):
    joinDate = serializers.DateTimeField(source = "created_at")

    class Meta:
        model = User
        fields = {"id", "username", "email", "joinDate"}

class ResetPasswordSerializer(serializers.Serializer):
    username = serializers.CharField()
    newsPassword = serializers.CharField(min_length=8)
    code = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(username = attrs["username"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"username": "존재하지 않는 username입니다."})
        
        ver = EmailVerification.objects.filter(
            email = user.email,
            purpose = "RESET_PASSWORD",
            code = attrs["code"],
            is_used = False
        ).order_by("_created_at").first()

        if not ver:
            raise serializers.ValidationError({"code": "인증코드가 올바르지 않습니다."})
        if ver.is_expired():
            raise serializers.ValidationError({"code": "인증 코드가 만료되었습니다."})
        
        attrs ["user"] = user
        attrs ["verification"] = ver
        return attrs