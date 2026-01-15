# Vues des opérations financières
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from money_transfer.forms import DepositForm, WithdrawalForm, TransferForm, OTPValidationForm
from money_transfer.services import TransactionService, OTPService, AccountService
from money_transfer.models.user import OTPType
from money_transfer.models.account import Platform
from money_transfer.decorators.decorators import active_user_required


@active_user_required
def deposit_view(request):
    """Vue de dépôt d'argent"""
    user = request.user
    
    if request.method == 'POST':
        form = DepositForm(request.POST)
        
        if form.is_valid():
            amount = form.cleaned_data['amount']
            
            # Effectuer le dépôt
            success, message, transaction = TransactionService.deposit(
                user=user,
                amount=amount
            )
            
            if success:
                messages.success(request, f" {message}")
                return redirect('transaction_detail', reference=transaction.reference)
            else:
                messages.error(request, message)
        else:
            messages.error(request, " Veuillez corriger les erreurs ci-dessous.")
    else:
        form = DepositForm()
    
    balance = AccountService.get_balance(user)
    
    context = {
        'form': form,
        'user': user,
        'balance': balance,
    }
    
    return render(request, 'money_transfer/transactions/deposit.html', context)


@active_user_required
def withdrawal_request_view(request):
    """Vue de demande de retrait (Étape 1)"""
    user = request.user
    
    # Récupérer les infos de la plateforme pour afficher les frais
    platform = Platform.objects.first()
    fee_rate = platform.withdrawal_fee_rate if platform else 2
    
    if request.method == 'POST':
        form = WithdrawalForm(request.POST, user=user)
        
        if form.is_valid():
            amount = form.cleaned_data['amount']
            fee = form.get_fee_amount()
            net_amount = form.get_net_amount()
            
            # Stocker les infos en session
            request.session['withdrawal_amount'] = amount
            request.session['withdrawal_fee'] = fee
            request.session['withdrawal_net'] = net_amount
            
            # Générer et envoyer l'OTP
            success, message, otp = OTPService.request_and_send_otp(
                user=user,
                otp_type=OTPType.WITHDRAWAL
            )
            
            if success:
                messages.info(request, " Un code de confirmation a été envoyé à votre email.")
                return redirect('withdrawal_confirm')
            else:
                messages.error(request, message)
        else:
            messages.error(request, " Veuillez corriger les erreurs ci-dessous.")
    else:
        form = WithdrawalForm(user=user)
    
    balance = AccountService.get_balance(user)
    
    context = {
        'form': form,
        'user': user,
        'balance': balance,
        'fee_rate': fee_rate,
    }
    
    return render(request, 'money_transfer/transactions/withdrawal_request.html', context)


@active_user_required
def withdrawal_confirm_view(request):
    """Vue de confirmation de retrait avec OTP (Étape 2)"""
    user = request.user
    
    # Récupérer les infos de la session
    amount = request.session.get('withdrawal_amount')
    fee = request.session.get('withdrawal_fee', 0)
    net_amount = request.session.get('withdrawal_net', 0)
    
    if not amount:
        messages.error(request, " Aucune demande de retrait en cours.")
        return redirect('withdrawal_request')
    
    if request.method == 'POST':
        form = OTPValidationForm(request.POST)
        
        if form.is_valid():
            code = form.cleaned_data['code']
            
            # Valider l'OTP
            is_valid, message = OTPService.validate_otp(
                user=user,
                code=code,
                otp_type=OTPType.WITHDRAWAL
            )
            
            if is_valid:
                # Effectuer le retrait
                success, msg, transaction = TransactionService.withdraw(
                    user=user,
                    amount=amount
                )
                
                # Nettoyer la session
                del request.session['withdrawal_amount']
                del request.session['withdrawal_fee']
                del request.session['withdrawal_net']
                
                if success:
                    messages.success(request, f" {msg}")
                    return redirect('transaction_detail', reference=transaction.reference)
                else:
                    messages.error(request, msg)
                    return redirect('withdrawal_request')
            else:
                messages.error(request, message)
        else:
            messages.error(request, " Code invalide.")
    else:
        form = OTPValidationForm()
    
    context = {
        'form': form,
        'user': user,
        'amount': amount,
        'fee': fee,
        'net_amount': net_amount,
    }
    
    return render(request, 'money_transfer/transactions/withdrawal_confirm.html', context)


@active_user_required
def transfer_view(request):
    """Vue de transfert d'argent"""
    user = request.user
    
    if request.method == 'POST':
        form = TransferForm(request.POST, user=user)
        
        if form.is_valid():
            receiver_email = form.cleaned_data['receiver_email']
            amount = form.cleaned_data['amount']
            
            # Effectuer le transfert
            success, message, transaction = TransactionService.transfer(
                sender_user=user,
                receiver_email=receiver_email,
                amount=amount
            )
            
            if success:
                messages.success(request, f" {message}")
                return redirect('transaction_detail', reference=transaction.reference)
            else:
                messages.error(request, message)
        else:
            messages.error(request, " Veuillez corriger les erreurs ci-dessous.")
    else:
        form = TransferForm(user=user)
    
    balance = AccountService.get_balance(user)
    
    context = {
        'form': form,
        'user': user,
        'balance': balance,
    }
    
    return render(request, 'money_transfer/transactions/transfer.html', context)