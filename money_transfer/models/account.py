from django.conf import settings
from django.db import models
from core.mixins import TimeStampMixin


class Platform(TimeStampMixin):
    name = models.CharField(max_length=100)
    withdrawal_fee_rate = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class VirtualAccount(TimeStampMixin):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='virtual_account'
    )

    platform = models.OneToOneField(
        'wallets.Platform',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='virtual_account'
    )

    balance = models.BigIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def clean(self):
        if not self.user and not self.platform:
            raise ValueError("Le compte doit appartenir à un utilisateur ou à la plateforme.")
        if self.user and self.platform:
            raise ValueError("Le compte ne peut pas appartenir aux deux.")

    def __str__(self):
        return f"VirtualAccount #{self.id}"
