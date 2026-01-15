# Models liés aux transactions financières

import uuid
from django.db import models
from .account import TimeStampMixin


class TypeTransaction(models.TextChoices):
    """Types de transactions possibles"""
    DEPOSIT = "DEPOSIT", "Dépôt"
    TRANSFER = "TRANSFER", "Transfert"
    WITHDRAWAL = "WITHDRAWAL", "Retrait"
    FEE = "FEE", "Frais"


class TransactionStatus(models.TextChoices):
    """Statuts de transaction"""
    PENDING = "PENDING", "En attente"
    SUCCESS = "SUCCESS", "Réussie"
    FAILED = "FAILED", "Échouée"


class Transaction(TimeStampMixin):
    """
    Transaction financière immuable et traçable
    """
    reference = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="Référence"
    )
    
    type = models.CharField(
        max_length=20,
        choices=TypeTransaction.choices,
        verbose_name="Type"
    )
    
    status = models.CharField(
        max_length=10,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        verbose_name="Statut"
    )
    
    amount = models.PositiveBigIntegerField(
        verbose_name="Montant brut",
        help_text="Montant initial de la transaction"
    )
    
    fee = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Frais",
        help_text="Frais appliqués (uniquement pour retrait)"
    )
    
    net_amount = models.PositiveBigIntegerField(
        verbose_name="Montant net",
        help_text="Montant réellement transféré (amount - fee)"
    )
    
    sender_account = models.ForeignKey(
        'VirtualAccount',
        on_delete=models.PROTECT,
        related_name='sent_transactions',
        verbose_name="Compte émetteur"
    )
    
    receiver_account = models.ForeignKey(
        'VirtualAccount',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='received_transactions',
        verbose_name="Compte récepteur"
    )
    
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Description"
    )
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['sender_account', 'status']),
            models.Index(fields=['receiver_account', 'status']),
            models.Index(fields=['-created_at']),
        ]
    
    def delete(self, *args, **kwargs):
        #--- Les transactions ne peuvent pas être supprimées (immuabilité)
        raise Exception(" Une transaction ne peut pas être supprimée.")
    
    def save(self, *args, **kwargs):
        #--- Les transactions ne peuvent pas être modifiées après création
        # Permettre la première sauvegarde (création)
        is_new = self.pk is None
        
        # Si c'est une modification (pas une création), interdire
        if not is_new and self._state.adding is False:
            # Vérifier si c'est juste un changement de statut (autorisé)
            if self.pk:
                old_instance = Transaction.objects.get(pk=self.pk)
                # Autoriser uniquement le changement de statut
                if (self.amount != old_instance.amount or 
                    self.fee != old_instance.fee or 
                    self.sender_account != old_instance.sender_account or
                    self.receiver_account != old_instance.receiver_account):
                    raise Exception(" Une transaction ne peut pas être modifiée.")
        
        # Calcul automatique du net_amount si non fourni
        if not self.net_amount:
            self.net_amount = self.amount - self.fee
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_type_display()} | {self.amount} | {self.reference}"
    
    @property
    def is_successful(self):
        #--- Vérifie si la transaction a réussi
        return self.status == TransactionStatus.SUCCESS
    
    @property
    def is_pending(self):
        #--- Vérifie si la transaction est en attente
        return self.status == TransactionStatus.PENDING
    
    @property
    def is_failed(self):
        #--- Vérifie si la transaction a échoué
        return self.status == TransactionStatus.FAILED