import re
import uuid
import random
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import (AbstractBaseUser, PermissionsMixin, BaseUserManager)
from django.core.exceptions import ValidationError

USERNAME_REGEX = re.compile(r"^[A-Za-z0-9_]{3,15}$")

def validate_username(value: str):
    if not USERNAME_REGEX.match(value):
        raise ValidationError("username은 3~15자, 영문/숫자/언더바(_)만 가능합니다.")
    
class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError("username은 필수입니다.")
        if not email:
            raise ValueError("email은 필수입니다.")

        username = username.strip()
        email = self.normalize_email(email)

        validate_username(username)

        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(username, email, password, **extra_fields)
    
class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    username = models.CharField(max_length=15, unique=True, validators=[validate_username])
    email = models.EmailField(unique=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username
    
class EmailVerification(models.Model):
    PURPOSE_CHOICES = (
        ("SIGNUP", "SIGNUP"),
        ("RESET_PASSWORD", "RESET_PASSWORD")
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)

    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)

    create_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    @staticmethod
    def generate_code():
        return f"{random.randint(0, 999999):06d}"
    
    @classmethod
    def create_code(cls, email: str, purpose: str, ttl_minutes: int=10):
        now = timezone.now()
        return cls.objects.create(
            email=email,
            purpose=purpose,
            code=cls.generate_code(),
            expires_at=now + timedelta(minutes=ttl_minutes),
        )
    
    def is_expired(self):
        return timezone.now() > self.expires_at