"""
Service de gestion des transactions
Dépôt, Retrait, Transfert - Logique atomique et sécurisée
"""
import logging
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from money_transfer.models import Transaction, VirtualAccount, User, Platform
from money_transfer.models.transaction import TypeTransaction, TransactionStatus
from .account_service import AccountService

logger = logging.getLogger('money_transfer')


class TransactionService:
    # Service centralisé pour toutes les opérations financières
    
    @staticmethod
    @transaction.atomic
    def deposit(user, amount):
   
        # Validations
        if amount <= 0:
            return False, "Le montant doit être positif.", None
        
        can_transact, error_msg = AccountService.can_perform_transaction(user)
        if not can_transact:
            return False, error_msg, None
        
        try:
            account = user.virtual_account
            
            # Créer la transaction
            txn = Transaction.objects.create(
                type=TypeTransaction.DEPOSIT,
                status=TransactionStatus.PENDING,
                amount=amount,
                fee=0,  # Pas de frais sur dépôt
                net_amount=amount,
                sender_account=account,
                receiver_account=account,
                description=f"Dépôt de {amount} sur le compte"
            )
            
            # Mettre à jour le solde
            VirtualAccount.objects.filter(id=account.id).update(
                balance=F('balance') + amount
            )
            
            # Marquer la transaction comme réussie
            txn.status = TransactionStatus.SUCCESS
            txn.save(update_fields=['status'])
            
            # Recharger le compte pour avoir le solde à jour
            account.refresh_from_db()
            
            logger.info(
                f"Dépôt réussi - User: {user.email} - Montant: {amount} - "
                f"Nouveau solde: {account.balance} - Ref: {txn.reference}"
            )
            
            return True, f" Dépôt de {amount} effectué avec succès !", txn
            
        except Exception as e:
            logger.error(f"Erreur lors du dépôt pour {user.email}: {str(e)}")
            if 'txn' in locals():
                txn.status = TransactionStatus.FAILED
                txn.save(update_fields=['status'])
            return False, " Une erreur est survenue lors du dépôt.", None
    
    @staticmethod
    @transaction.atomic
    def withdraw(user, amount):
       
        # Validations
        if amount <= 0:
            return False, " Le montant doit être positif.", None
        
        can_transact, error_msg = AccountService.can_perform_transaction(user)
        if not can_transact:
            return False, error_msg, None
        
        try:
            account = user.virtual_account
            platform_account = AccountService.get_or_create_platform_account()
            platform = platform_account.platform
            
            # Calculer les frais
            fee = platform.calculate_withdrawal_fee(amount)
            net_amount = amount - fee
            total_to_deduct = amount  
            
            # Vérifier le solde
            has_balance, balance_msg = AccountService.check_sufficient_balance(
                account, total_to_deduct
            )
            if not has_balance:
                return False, balance_msg, None
            
            # Créer la transaction de retrait
            withdrawal_txn = Transaction.objects.create(
                type=TypeTransaction.WITHDRAWAL,
                status=TransactionStatus.PENDING,
                amount=amount,
                fee=fee,
                net_amount=net_amount,
                sender_account=account,
                receiver_account=None,  # Retrait = sortie du système
                description=f"Retrait de {amount} (Frais: {fee}, Net: {net_amount})"
            )
            
            # Déduire le montant du compte utilisateur
            VirtualAccount.objects.filter(id=account.id).update(
                balance=F('balance') - total_to_deduct
            )
            
            # Créer une transaction de frais vers la plateforme
            if fee > 0:
                fee_txn = Transaction.objects.create(
                    type=TypeTransaction.FEE,
                    status=TransactionStatus.SUCCESS,
                    amount=fee,
                    fee=0,
                    net_amount=fee,
                    sender_account=account,
                    receiver_account=platform_account,
                    description=f"Frais de retrait ({platform.withdrawal_fee_rate}%)"
                )
                
                # Créditer le compte plateforme
                VirtualAccount.objects.filter(id=platform_account.id).update(
                    balance=F('balance') + fee
                )
            
            # Marquer la transaction comme réussie
            withdrawal_txn.status = TransactionStatus.SUCCESS
            withdrawal_txn.save(update_fields=['status'])
            
            # Recharger les comptes
            account.refresh_from_db()
            platform_account.refresh_from_db()
            
            logger.info(
                f"Retrait réussi - User: {user.email} - Montant: {amount} - "
                f"Frais: {fee} - Net: {net_amount} - Nouveau solde: {account.balance} - "
                f"Ref: {withdrawal_txn.reference}"
            )
            
            return True, (
                f" Retrait de {amount} effectué avec succès !\n"
                f"Frais: {fee} ({platform.withdrawal_fee_rate}%)\n"
                f"Montant net retiré: {net_amount}"
            ), withdrawal_txn
            
        except Exception as e:
            logger.error(f"Erreur lors du retrait pour {user.email}: {str(e)}")
            if 'withdrawal_txn' in locals():
                withdrawal_txn.status = TransactionStatus.FAILED
                withdrawal_txn.save(update_fields=['status'])
            return False, " Une erreur est survenue lors du retrait.", None
    
    @staticmethod
    @transaction.atomic
    def transfer(sender_user, receiver_email, amount):
      
   
        # Validations
        if amount <= 0:
            return False, "Le montant doit être positif.", None
        
        can_transact, error_msg = AccountService.can_perform_transaction(sender_user)
        if not can_transact:
            return False, error_msg, None
        
        # Vérifier que le destinataire existe
        try:
            receiver_user = User.objects.get(email=receiver_email)
        except User.DoesNotExist:
            return False, f" Aucun utilisateur trouvé avec l'email : {receiver_email}", None
        
        # Vérifier qu'on ne transfère pas à soi-même
        if sender_user.id == receiver_user.id:
            return False, " Vous ne pouvez pas transférer à vous-même.", None
        
        # Vérifier que le destinataire peut recevoir
        can_receive, receive_error = AccountService.can_perform_transaction(receiver_user)
        if not can_receive:
            return False, f" Le destinataire ne peut pas recevoir : {receive_error}", None
        
        try:
            sender_account = sender_user.virtual_account
            receiver_account = receiver_user.virtual_account
            
            # Vérifier le solde
            has_balance, balance_msg = AccountService.check_sufficient_balance(
                sender_account, amount
            )
            if not has_balance:
                return False, balance_msg, None
            
            # Créer la transaction
            transfer_txn = Transaction.objects.create(
                type=TypeTransaction.TRANSFER,
                status=TransactionStatus.PENDING,
                amount=amount,
                fee=0,  # Pas de frais sur transfert
                net_amount=amount,
                sender_account=sender_account,
                receiver_account=receiver_account,
                description=f"Transfert de {sender_user.email} vers {receiver_user.email}"
            )
            
            # Déduire du compte envoyeur
            VirtualAccount.objects.filter(id=sender_account.id).update(
                balance=F('balance') - amount
            )
            
            # Créditer le compte destinataire
            VirtualAccount.objects.filter(id=receiver_account.id).update(
                balance=F('balance') + amount
            )
            
            # Marquer la transaction comme réussie
            transfer_txn.status = TransactionStatus.SUCCESS
            transfer_txn.save(update_fields=['status'])
            
            # Recharger les comptes
            sender_account.refresh_from_db()
            receiver_account.refresh_from_db()
            
            logger.info(
                f"Transfert réussi - De: {sender_user.email} - Vers: {receiver_user.email} - "
                f"Montant: {amount} - Nouveau solde envoyeur: {sender_account.balance} - "
                f"Ref: {transfer_txn.reference}"
            )
            
            return True, (
                f" Transfert de {amount} effectué avec succès vers {receiver_user.email}!"
            ), transfer_txn
            
        except Exception as e:
            logger.error(
                f"Erreur lors du transfert de {sender_user.email} vers {receiver_email}: {str(e)}"
            )
            if 'transfer_txn' in locals():
                transfer_txn.status = TransactionStatus.FAILED
                transfer_txn.save(update_fields=['status'])
            return False, " Une erreur est survenue lors du transfert.", None
    
    @staticmethod
    def get_user_transactions(user, limit=50):
       
        if not hasattr(user, 'virtual_account') or not user.virtual_account:
            return Transaction.objects.none()
        
        account = user.virtual_account
        
        # Récupérer toutes les transactions où l'utilisateur est impliqué
        transactions = Transaction.objects.filter(
            sender_account=account
        ) | Transaction.objects.filter(
            receiver_account=account
        )
        
        transactions = transactions.distinct().order_by('-created_at')
        
        # Appliquer la limite si spécifiée
        if limit is not None:
            transactions = transactions[:limit]
        
        return transactions
    
    @staticmethod
    def get_transaction_by_reference(reference):
      
        try:
            return Transaction.objects.get(reference=reference)
        except Transaction.DoesNotExist:
            return None