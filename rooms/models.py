from django.db import models
from django.conf import settings
from django.utils import timezone
import secrets
import string

def generate_room_code(length = 8):
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

class Room(models.Model):
    name = models.CharField(max_length=60, blank = True)
    code = models.CharField(max_length=12, unique = True, db_index=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name = "owned_rooms")
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def create_with_unique_code(cls, owner, name=""):
        for _ in range(10):
            code = generate_room_code()
            if not cls.objects.filter(code=code).exists():
                return cls.objects.create(owner=owner, name=name, code=code)
        raise RuntimeError("Failed to generate unique room code")
    
class RoomMember(models.Model):
    class Role(models.TextChoices):
        OWNER  = "OWNER", "OWNER"
        MEMBER = "MEMBER", "MEMBER"

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='room_memberships')
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["room", "user"], name="uniq_room_user"),
        ]

    def leave(self):
        if self.left_at is None:
            self.left_at = timezone.now()
            self.save(update_fields=["left_at"])