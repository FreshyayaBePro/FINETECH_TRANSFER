# Service de gestion des comptes virtuels
# Création, activation, suspension, vérification de solde

import logging
from django.db import transaction
from money_transfer.models import VirtualAccount, Platform, User
from money_transfer.models.user import UserStatus

logger = logging.getLogger('money_transfer')


class AccountService:
    # Service centralisé pour la gestion des comptes virtuels
    
    @staticmethod
    @transaction.atomic
    def create_user_account(user):
    
        # Vérifier si l'utilisateur a déjà un compte
        if hasattr(user, 'virtual_account') and user.virtual_account:
            logger.warning(f"Tentative de création de compte existant pour {user.email}")
            raise ValueError(f"L'utilisateur {user.email} a déjà un compte virtuel.")
        
        # Créer le compte
        account = VirtualAccount.objects.create(
            user=user,
            balance=0,
            is_active=False  # Reste inactif jusqu'à la validation de l'OTP
        )
        
        logger.info(f"Compte virtuel créé pour {user.email} - ID: {account.id}")
        return account
    
    @staticmethod
    @transaction.atomic
    def create_platform_account(platform):
    
        if hasattr(platform, 'virtual_account') and platform.virtual_account:
            logger.warning(f"Tentative de création de compte plateforme existant pour {platform.name}")
            raise ValueError(f"La plateforme {platform.name} a déjà un compte virtuel.")
        
        account = VirtualAccount.objects.create(
            platform=platform,
            balance=0,
            is_active=True  # La plateform reste tjr actif
        )
        
        logger.info(f"Compte plateforme créé pour {platform.name} - ID: {account.id}")
        return account
    
    @staticmethod
    def get_or_create_platform_account():
       
        try:
            platform = Platform.objects.first()
            
            if not platform:
                # Créer la plateforme par défaut si elle n'existe pas
                platform = Platform.objects.create(
                    name="Money Transfer Platform",
                    withdrawal_fee_rate=2  # 2% par défaut
                )
                logger.info("Plateforme par défaut créée")
            
            # Récupérer ou créer le compte
            if hasattr(platform, 'virtual_account') and platform.virtual_account:
                return platform.virtual_account
            else:
                return AccountService.create_platform_account(platform)
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du compte plateforme: {str(e)}")
            raise
    
    @staticmethod
    @transaction.atomic
    def activate_account(user):
      
        try:
            # Vérifier que l'utilisateur a un compte
            if not hasattr(user, 'virtual_account') or not user.virtual_account:
                return False, " Aucun compte trouvé pour cet utilisateur."
            
            account = user.virtual_account
            
            # Activer le compte
            account.is_active = True
            account.save(update_fields=['is_active'])
            
            # Mettre à jour le statut de l'utilisateur
            user.status = UserStatus.ACTIVE
            user.is_verified = True
            user.save(update_fields=['status', 'is_verified'])
            
            logger.info(f"Compte activé pour {user.email}")
            return True, " Votre compte a été activé avec succès !"
            
        except Exception as e:
            logger.error(f"Erreur lors de l'activation du compte pour {user.email}: {str(e)}")
            return False, " Une erreur est survenue lors de l'activation."
    
    @staticmethod
    @transaction.atomic
    def suspend_account(user, reason=""):
        
        try:
            if not hasattr(user, 'virtual_account') or not user.virtual_account:
                return False, " Aucun compte trouvé."
            
            account = user.virtual_account
            account.is_active = False
            account.save(update_fields=['is_active'])
            
            # Mettre à jour le statut utilisateur
            user.status = UserStatus.SUSPENDED
            user.save(update_fields=['status'])
            
            logger.warning(f"Compte suspendu pour {user.email} - Raison: {reason}")
            return True, "⚠️ Le compte a été suspendu."
            
        except Exception as e:
            logger.error(f"Erreur lors de la suspension du compte pour {user.email}: {str(e)}")
            return False, " Erreur lors de la suspension."
    
    @staticmethod
    @transaction.atomic
    def reactivate_account(user):
     
        try:
            if not hasattr(user, 'virtual_account') or not user.virtual_account:
                return False, " Aucun compte trouvé."
            
            account = user.virtual_account
            account.is_active = True
            account.save(update_fields=['is_active'])
            
            user.status = UserStatus.ACTIVE
            user.save(update_fields=['status'])
            
            logger.info(f"Compte réactivé pour {user.email}")
            return True, " Le compte a été réactivé."
            
        except Exception as e:
            logger.error(f"Erreur lors de la réactivation du compte pour {user.email}: {str(e)}")
            return False, " Erreur lors de la réactivation."
    
    @staticmethod
    def get_balance(user):
   
        try:
            if hasattr(user, 'virtual_account') and user.virtual_account:
                return user.virtual_account.balance
            return 0
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du solde pour {user.email}: {str(e)}")
            return 0
    
    @staticmethod
    def can_perform_transaction(user):
    
        # Vérifier le statut de l'utilisateur
        if user.status == UserStatus.SUSPENDED:
            return False, " Votre compte est suspendu. Contactez l'administrateur."
        
        if user.status == UserStatus.PENDING:
            return False, "⚠️ Votre compte est en attente de validation."
        
        if not user.is_verified:
            return False, "⚠️ Veuillez vérifier votre compte pour effectuer des transactions."
        
        # Vérifier l'existence et l'état du compte virtuel
        if not hasattr(user, 'virtual_account') or not user.virtual_account:
            return False, " Aucun compte virtuel trouvé."
        
        if not user.virtual_account.is_active:
            return False, " Votre compte virtuel est inactif."
        
        return True, ""
    
    @staticmethod
    def check_sufficient_balance(account, amount):
   
        if account.balance < amount:
            return False, f" Solde insuffisant. Solde actuel : {account.balance}"
        return True, ""