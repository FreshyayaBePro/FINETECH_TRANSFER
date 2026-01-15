"""
Models liés aux comptes virtuels et à la plateforme
"""
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class TimeStampMixin(models.Model):
    """Mixin pour ajouter created_at et updated_at"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    # deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Supprimé le")
    class Meta:
        abstract = True


class Platform(TimeStampMixin):
    
    # Configuration de la plateforme (compte de frais)

    name = models.CharField(max_length=100, unique=True, verbose_name="Nom")
    withdrawal_fee_rate = models.PositiveIntegerField(
        verbose_name="Taux de frais de retrait (%)",
        help_text="Pourcentage de frais sur les retraits (ex: 2 pour 2%)"
    )
    
    class Meta:
        verbose_name = "Plateforme"
        verbose_name_plural = "Plateformes"
    
    def __str__(self):
        return f"{self.name} (Frais: {self.withdrawal_fee_rate}%)"
    
    def calculate_withdrawal_fee(self, amount):
        """Calcule les frais de retrait"""
        return (amount * self.withdrawal_fee_rate) // 100


class AccountOwnerType(models.TextChoices):
    """Type de propriétaire du compte"""
    USER = "USER", "Utilisateur"
    PLATFORM = "PLATFORM", "Plateforme"


class VirtualAccount(TimeStampMixin):
    """
    Compte virtuel pouvant appartenir à un utilisateur ou à la plateforme
    """
    owner_type = models.CharField(
        max_length=10,
        choices=AccountOwnerType.choices,
        default=AccountOwnerType.USER,
        verbose_name="Type de propriétaire"
    )
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='virtual_account',
        verbose_name="Utilisateur"
    )
    
    platform = models.OneToOneField(
        'Platform',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='virtual_account',
        verbose_name="Plateforme"
    )
    
    balance = models.BigIntegerField(default=0, verbose_name="Solde")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    class Meta:
        verbose_name = "Compte virtuel"
        verbose_name_plural = "Comptes virtuels"
        indexes = [
            models.Index(fields=['owner_type', 'is_active']),
        ]
    
    def clean(self):
        """Validation : un compte doit avoir exactement un propriétaire"""
        if not self.user and not self.platform:
            raise ValidationError(
                "Le compte doit appartenir à un utilisateur ou à la plateforme."
            )
        if self.user and self.platform:
            raise ValidationError(
                "Le compte ne peut pas appartenir aux deux (utilisateur ET plateforme)."
            )
        
        # Définir automatiquement owner_type
        if self.user:
            self.owner_type = AccountOwnerType.USER
        elif self.platform:
            self.owner_type = AccountOwnerType.PLATFORM
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.user:
            return f"Compte de {self.user.email} (Solde: {self.balance})"
        elif self.platform:
            return f"Compte plateforme {self.platform.name} (Solde: {self.balance})"
        return f"Compte #{self.id}"
    
    @property
    def owner(self):
        """Retourne le propriétaire (user ou platform)"""
        return self.user if self.user else self.platform
    
    def can_withdraw(self, amount):
        """Vérifie si le retrait est possible"""
        return self.is_active and self.balance >= amount
    
    def can_receive(self):
        """Vérifie si le compte peut recevoir de l'argent"""
        return self.is_active