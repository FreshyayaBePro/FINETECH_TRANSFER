# Models liés aux utilisateurs et à l'authentification

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class UserStatus(models.TextChoices):
    # Statuts possibles d'un utilisateur
    PENDING = 'PENDING', 'En attente'
    ACTIVE = 'ACTIVE', 'Actif'
    SUSPENDED = 'SUSPENDED', 'Suspendu'


class UserManager(BaseUserManager):
    # Manager personnalisé pour User sans username
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('status', UserStatus.ACTIVE)
        extra_fields.setdefault('is_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser doit avoir is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    
    # Utilisateur de la plateforme avec authentification par email

    username = None 
    
    email = models.EmailField(unique=True, verbose_name="Email")
    phone = models.CharField(max_length=20, unique=True, verbose_name="Téléphone")
    gender = models.CharField(
        max_length=10,
        choices=[('M', 'Masculin'), ('F', 'Féminin')],
        verbose_name="Genre"
    )
    
    status = models.CharField(
        max_length=10,
        choices=UserStatus.choices,
        default=UserStatus.PENDING,
        verbose_name="Statut"
    )
    
    is_verified = models.BooleanField(default=False, verbose_name="Compte vérifié")
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone", "first_name", "last_name"]
    
    objects = UserManager()
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def is_active_user(self):
        # Vérifie si l'utilisateur peut effectuer des opérations
        return self.status == UserStatus.ACTIVE and self.is_verified
    
    def can_perform_operations(self):
        # Alias pour is_active_user
        return self.is_active_user()


class OTPType(models.TextChoices):
    # Types d'OTP possibles
    ACCOUNT_VALIDATION = "ACCOUNT_VALIDATION", "Validation de compte"
    WITHDRAWAL = "WITHDRAWAL", "Retrait d'argent"


class OTP(models.Model):
    # Code à usage unique pour sécuriser les opérations critiques

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="otps",
        verbose_name="Utilisateur"
    )
    
    code = models.CharField(max_length=6, verbose_name="Code")
    otp_type = models.CharField(
        max_length=30,
        choices=OTPType.choices,
        verbose_name="Type"
    )
    
    is_used = models.BooleanField(default=False, verbose_name="Utilisé")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    expires_at = models.DateTimeField(verbose_name="Expire le")
    
    class Meta:
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'otp_type', 'is_used']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Par défaut, OTP valide 2 minutes
            self.expires_at = timezone.now() + timedelta(minutes=2)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        # Vérifie si l'OTP est encore valide
        return not self.is_used and timezone.now() <= self.expires_at
    
    def mark_as_used(self):
        # Marque l'OTP comme utilisé
        self.is_used = True
        self.save(update_fields=['is_used'])
    
    def __str__(self):
        return f"{self.user.email} - {self.get_otp_type_display()} - {self.code}"