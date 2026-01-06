
# Create your models here.

import uuid
from django.db import models
from core.mixins import TimeStampMixin
from core.enums import TypeTransaction, TransactionStatus
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


class Transaction(TimeStampMixin):
    """
    Représente une opération financière immuable
    """

    reference = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    type = models.CharField(
        max_length=20,
        choices=TypeTransaction.choices
    )

    status = models.CharField(
        max_length=10,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING
    )

    amount = models.PositiveBigIntegerField(
        help_text="Montant brut de la transaction"
    )

    fee = models.PositiveBigIntegerField(
        default=0,
        help_text="Frais appliqués (uniquement pour retrait)"
    )

    net_amount = models.PositiveBigIntegerField(
        help_text="Montant réellement transféré"
    )

    sender_account = models.ForeignKey(
        'wallets.VirtualAccount',
        on_delete=models.PROTECT,
        related_name='sent_transactions'
    )

    receiver_account = models.ForeignKey(
        'wallets.VirtualAccount',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='received_transactions'
    )

    class Meta:
        ordering = ['-created_at']

    def delete(self, *args, **kwargs):
        raise Exception("Une transaction ne peut pas être supprimée.")

    def save(self, *args, **kwargs):
        if self.pk:
            raise Exception("Une transaction ne peut pas être modifiée.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.type} | {self.amount} | {self.reference}"

