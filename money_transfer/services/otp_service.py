# Service de gestion des OTP (One-Time Password)
# Génération, validation, envoi par email

import random
import logging
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from money_transfer.models.user import OTP, User, OTPType

logger = logging.getLogger('money_transfer')


class OTPService:
    # Service centralisé pour la gestion des OTP
    
    @staticmethod
    def generate_code(length=6):
     
        return ''.join([str(random.randint(0, 9)) for _ in range(length)])
    
    @staticmethod
    def create_otp(user, otp_type, expiry_minutes=2):
        
        if otp_type not in [OTPType.ACCOUNT_VALIDATION, OTPType.WITHDRAWAL]:
            raise ValueError(f"Type d'OTP invalide : {otp_type}")
        
        # Invalider tous les anciens OTP non utilisés du même type
        OTP.objects.filter(
            user=user,
            otp_type=otp_type,
            is_used=False
        ).update(is_used=True)
        
        # Générer le code
        code = OTPService.generate_code()
        
        # Créer le nouvel OTP
        otp = OTP.objects.create(
            user=user,
            code=code,
            otp_type=otp_type,
            expires_at=timezone.now() + timedelta(minutes=expiry_minutes)
        )
        
        logger.info(f"OTP créé pour {user.email} - Type: {otp_type} - Code: {code}")
        
        return otp
    
    @staticmethod
    def send_otp_email(otp):
        
        user = otp.user
        
        # Déterminer le sujet et le message selon le type
        if otp.otp_type == OTPType.ACCOUNT_VALIDATION:
            subject = " Code de validation de votre compte"
            template_name = "money_transfer/emails/otp_account_validation.html"
        else:  # WITHDRAWAL
            subject = " Code de confirmation de retrait"
            template_name = "money_transfer/emails/otp_withdrawal.html"
        
        # Contexte pour le template
        context = {
            'user': user,
            'code': otp.code,
            'expires_at': otp.expires_at,
            'otp_type': otp.get_otp_type_display(),
        }
        
        try:
            # Rendu HTML
            html_message = render_to_string(template_name, context)
            plain_message = strip_tags(html_message)
            
            # Envoi de l'email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Email OTP envoyé à {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email OTP à {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def validate_otp(user, code, otp_type):
       
        try:
            # Rechercher l'OTP
            otp = OTP.objects.get(
                user=user,
                code=code,
                otp_type=otp_type,
                is_used=False
            )
            
            # Vérifier la validité
            if not otp.is_valid():
                logger.warning(f"OTP expiré pour {user.email} - Code: {code}")
                return False, " Ce code a expiré. Demandez un nouveau code."
            
            # Marquer comme utilisé
            otp.mark_as_used()
            
            logger.info(f"OTP validé avec succès pour {user.email} - Type: {otp_type}")
            return True, " Code validé avec succès !"
            
        except OTP.DoesNotExist:
            logger.warning(f"OTP invalide pour {user.email} - Code: {code}")
            return False, " Code invalide. Vérifiez et réessayez."
        
        except Exception as e:
            logger.error(f"Erreur lors de la validation OTP pour {user.email}: {str(e)}")
            return False, " Une erreur est survenue. Réessayez."
    
    @staticmethod
    def request_and_send_otp(user, otp_type):
      
        try:
            # Créer l'OTP
            otp = OTPService.create_otp(user, otp_type)
            
            # Envoyer par email
            email_sent = OTPService.send_otp_email(otp)
            
            if email_sent:
                return True, f" Un code de validation a été envoyé à {user.email}", otp
            else:
                return False, " Erreur lors de l'envoi de l'email. Réessayez.", None
                
        except Exception as e:
            logger.error(f"Erreur lors de la création/envoi OTP pour {user.email}: {str(e)}")
            return False, " Une erreur est survenue. Contactez le support.", None
    
    @staticmethod
    def cleanup_expired_otps():
      
        expired_otps = OTP.objects.filter(
            expires_at__lt=timezone.now(),
            is_used=False
        )
        
        count = expired_otps.count()
        expired_otps.update(is_used=True)  # Marquer comme utilisés plutôt que supprimer
        
        logger.info(f"Nettoyage OTP : {count} OTP expirés marqués comme utilisés")
        return count