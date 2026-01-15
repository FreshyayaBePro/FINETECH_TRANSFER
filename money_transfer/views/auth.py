"""
Vues d'authentification et gestion de compte
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from money_transfer.forms import (
    UserRegistrationForm,
    UserLoginForm,
    OTPValidationForm,
    ProfileUpdateForm
)
from money_transfer.services import OTPService, AccountService
from money_transfer.models.user import OTPType


def register_view(request):
    # Vue d'inscription
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Créer l'utilisateur
                    user = form.save(commit=False)
                    user.set_password(form.cleaned_data['password1'])
                    user.save()
                    
                    # Créer le compte virtuel
                    AccountService.create_user_account(user)
                    
                    # Générer et envoyer l'OTP
                    success, message, otp = OTPService.request_and_send_otp(
                        user=user,
                        otp_type=OTPType.ACCOUNT_VALIDATION
                    )
                    
                    if success:
                        # Connecter l'utilisateur automatiquement
                        login(request, user)
                        messages.success(
                            request,
                            f" Bienvenue {user.first_name} ! Un code de validation a été envoyé à {user.email}"
                        )
                        return redirect('verify_account')
                    else:
                        messages.error(request, f"⚠️ {message}")
                        return redirect('register')
                        
            except Exception as e:
                messages.error(request, f" Une erreur est survenue lors de l'inscription : {str(e)}")
    else:
        form = UserRegistrationForm()
    
    return render(request, 'money_transfer/auth/register.html', {'form': form})


def login_view(request):
    """Vue de connexion"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                login(request, user)
                
                # Gestion "Se souvenir de moi"
                if not form.cleaned_data.get('remember_me'):
                    request.session.set_expiry(0)
                
                messages.success(request, f" Bienvenue {user.first_name} !")
                
                # Rediriger vers la page demandée ou dashboard
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, " Email ou mot de passe incorrect.")
        else:
            messages.error(request, " Veuillez corriger les erreurs ci-dessous.")
    else:
        form = UserLoginForm()
    
    return render(request, 'money_transfer/auth/login.html', {'form': form})


@login_required
def logout_view(request):
    """Vue de déconnexion"""
    user_name = request.user.first_name
    logout(request)
    messages.info(request, f" À bientôt {user_name} !")
    return redirect('login')


@login_required
def verify_account_view(request):
    """Vue de vérification du compte avec OTP"""
    user = request.user
    
    # Si déjà vérifié, rediriger
    if user.is_verified:
        messages.info(request, " Votre compte est déjà vérifié !")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = OTPValidationForm(request.POST)
        
        if form.is_valid():
            code = form.cleaned_data['code']
            
            # Valider l'OTP
            is_valid, message = OTPService.validate_otp(
                user=user,
                code=code,
                otp_type=OTPType.ACCOUNT_VALIDATION
            )
            
            if is_valid:
                # Activer le compte
                success, activation_message = AccountService.activate_account(user)
                
                if success:
                    messages.success(request, f" {activation_message}")
                    return redirect('dashboard')
                else:
                    messages.error(request, activation_message)
            else:
                messages.error(request, message)
    else:
        form = OTPValidationForm()
    
    return render(request, 'money_transfer/auth/verify_account.html', {
        'form': form,
        'user': user
    })


@login_required
def request_new_otp_view(request):
    """Vue pour demander un nouveau code OTP"""
    user = request.user
    otp_type = request.GET.get('type', OTPType.ACCOUNT_VALIDATION)
    
    # Générer et envoyer un nouveau code
    success, message, otp = OTPService.request_and_send_otp(
        user=user,
        otp_type=otp_type
    )
    
    if success:
        messages.success(request, f" {message}")
    else:
        messages.error(request, f" {message}")
    
    # Rediriger selon le type d'OTP
    if otp_type == OTPType.WITHDRAWAL:
        return redirect('withdrawal_confirm')
    else:
        return redirect('verify_account')


@login_required
def profile_view(request):
    """Vue du profil utilisateur"""
    user = request.user
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=user)
        
        if form.is_valid():
            form.save()
            messages.success(request, " Profil mis à jour avec succès !")
            return redirect('profile')
        else:
            messages.error(request, " Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ProfileUpdateForm(instance=user)
    
    # Récupérer le solde
    balance = AccountService.get_balance(user)
    
    context = {
        'form': form,
        'user': user,
        'balance': balance
    }
    
    return render(request, 'money_transfer/auth/profile.html', context)