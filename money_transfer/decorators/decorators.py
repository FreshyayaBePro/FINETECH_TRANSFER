"""
Décorateurs pour gérer les permissions et la sécurité
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models.user import UserStatus


def admin_required(view_func):
    """
    Décorateur pour restreindre l'accès aux administrateurs uniquement
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "⛔ Accès réservé aux administrateurs.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def active_user_required(view_func):
    """
    Décorateur pour s'assurer que l'utilisateur est actif et vérifié
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        
        if user.status == UserStatus.SUSPENDED:
            messages.error(request, "⛔ Votre compte est suspendu. Contactez l'administrateur.")
            return redirect('dashboard')
        
        if user.status == UserStatus.PENDING:
            messages.warning(request, "⚠️ Votre compte est en attente de validation.")
            return redirect('dashboard')
        
        if not user.is_verified:
            messages.warning(request, "⚠️ Veuillez vérifier votre compte pour continuer.")
            return redirect('verify_account')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def verified_account_required(view_func):
    """
    Décorateur pour s'assurer que le compte est vérifié
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_verified:
            messages.warning(request, "⚠️ Veuillez vérifier votre compte d'abord.")
            return redirect('verify_account')
        return view_func(request, *args, **kwargs)
    return wrapper


def otp_required(otp_type):
    """
    Décorateur pour exiger un OTP valide avant d'accéder à une vue
    Usage: @otp_required('WITHDRAWAL')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Vérifier si l'OTP a été validé dans la session
            session_key = f'otp_validated_{otp_type}'
            if not request.session.get(session_key, False):
                messages.warning(request, "⚠️ Veuillez valider l'OTP d'abord.")
                return redirect('request_otp', otp_type=otp_type)
            
            # Supprimer le flag après utilisation (usage unique)
            del request.session[session_key]
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator