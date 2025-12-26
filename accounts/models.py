from django.contrib.auth.models import AbstractUser
from django.db import models
from core.enums import UserStatus


class User(AbstractUser):
    """
    Utilisateur de la plateforme
    """

    username = None
    email = models.EmailField(unique=True)

    phone = models.CharField(max_length=20, unique=True)
    gender = models.CharField(max_length=10)

    status = models.CharField(
        max_length=10,
        choices=UserStatus.choices,
        default=UserStatus.PENDING
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
