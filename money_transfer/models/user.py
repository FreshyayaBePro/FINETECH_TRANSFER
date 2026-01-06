from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone
from core.enums import UserStatus
from .managers import UserManager


class User(AbstractUser):
    """
    Utilisateur de la plateforme
    """

    username = None  # 🔥 suppression du username
    email = models.EmailField(unique=True)

    phone = models.CharField(max_length=20, unique=True)
    gender = models.CharField(max_length=10)

    status = models.CharField(
        max_length=10,
        choices=UserStatus.choices,
        default=UserStatus.PENDING
    )

    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone", "first_name", "last_name"]

    objects = UserManager() 
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class OTP(models.Model):
    OTP_TYPE_CHOICES = (
        ("ACCOUNT_VALIDATION", "Validation de compte"),
        ("WITHDRAWAL", "Retrait d'argent"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="otps"
    )

    code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=30, choices=OTP_TYPE_CHOICES)

    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at

    def __str__(self):
        return f"{self.user} - {self.otp_type} - {self.code}"
