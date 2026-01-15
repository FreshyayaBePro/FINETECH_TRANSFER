"""
Vues administrateur
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg
from datetime import datetime, timedelta

from money_transfer.models import User, Transaction, VirtualAccount, Platform
from money_transfer.models.transaction import TypeTransaction, TransactionStatus
from money_transfer.models.user import UserStatus
from money_transfer.forms import (
    UserSuspendForm,
    UserReactivateForm,
    PlatformConfigForm,
    UserSearchForm
)
from money_transfer.services import AccountService
from money_transfer.decorators.decorators import admin_required


@admin_required
def admin_dashboard_view(request):
    """Dashboard administrateur avec statistiques"""
    
    # Statistiques globales
    total_users = User.objects.count()
    active_users = User.objects.filter(status=UserStatus.ACTIVE).count()
    pending_users = User.objects.filter(status=UserStatus.PENDING).count()
    suspended_users = User.objects.filter(status=UserStatus.SUSPENDED).count()
    
    # Statistiques des transactions
    total_transactions = Transaction.objects.count()
    successful_transactions = Transaction.objects.filter(status=TransactionStatus.SUCCESS).count()
    
    # Volume total des transactions
    total_volume = Transaction.objects.filter(
        status=TransactionStatus.SUCCESS
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Frais collectés
    total_fees = Transaction.objects.filter(
        type=TypeTransaction.FEE,
        status=TransactionStatus.SUCCESS
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Transactions du jour
    today = datetime.now().date()
    transactions_today = Transaction.objects.filter(
        created_at__date=today
    ).count()
    
    # Dernières transactions
    recent_transactions = Transaction.objects.select_related(
        'sender_account__user',
        'receiver_account__user'
    ).order_by('-created_at')[:10]
    
    # Utilisateurs récents
    recent_users = User.objects.order_by('-date_joined')[:10]
    
    # Plateforme
    platform = Platform.objects.first()
    platform_account = None
    if platform and hasattr(platform, 'virtual_account'):
        platform_account = platform.virtual_account
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'pending_users': pending_users,
        'suspended_users': suspended_users,
        'total_transactions': total_transactions,
        'successful_transactions': successful_transactions,
        'total_volume': total_volume,
        'total_fees': total_fees,
        'transactions_today': transactions_today,
        'recent_transactions': recent_transactions,
        'recent_users': recent_users,
        'platform': platform,
        'platform_account': platform_account,
    }
    
    return render(request, 'money_transfer/admin/dashboard.html', context)


@admin_required
def admin_users_view(request):
    """Liste et recherche des utilisateurs"""
    
    users = User.objects.all().order_by('-date_joined')
    
    # Filtrage
    if request.method == 'GET':
        form = UserSearchForm(request.GET)
        
        if form.is_valid():
            search = form.cleaned_data.get('search')
            status = form.cleaned_data.get('status')
            is_verified = form.cleaned_data.get('is_verified')
            
            if search:
                users = users.filter(
                    Q(email__icontains=search) |
                    Q(first_name__icontains=search) |
                    Q(last_name__icontains=search) |
                    Q(phone__icontains=search)
                )
            
            if status:
                users = users.filter(status=status)
            
            if is_verified is not None:
                users = users.filter(is_verified=is_verified)
    else:
        form = UserSearchForm()
    
    context = {
        'users': users,
        'form': form,
    }
    
    return render(request, 'money_transfer/admin/users.html', context)


@admin_required
def admin_user_detail_view(request, user_id):
    """Détails d'un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    
    # Solde
    balance = AccountService.get_balance(user)
    
    # Transactions de l'utilisateur
    from money_transfer.services import TransactionService
    transactions = TransactionService.get_user_transactions(user, limit=20)
    
    # Statistiques
    account = user.virtual_account if hasattr(user, 'virtual_account') else None
    
    if account:
        deposits = Transaction.objects.filter(
            sender_account=account,
            type=TypeTransaction.DEPOSIT,
            status=TransactionStatus.SUCCESS
        ).aggregate(total=Sum('amount'), count=Count('id'))
        
        withdrawals = Transaction.objects.filter(
            sender_account=account,
            type=TypeTransaction.WITHDRAWAL,
            status=TransactionStatus.SUCCESS
        ).aggregate(total=Sum('amount'), count=Count('id'))
        
        transfers_sent = Transaction.objects.filter(
            sender_account=account,
            type=TypeTransaction.TRANSFER,
            status=TransactionStatus.SUCCESS
        ).aggregate(total=Sum('amount'), count=Count('id'))
        
        transfers_received = Transaction.objects.filter(
            receiver_account=account,
            type=TypeTransaction.TRANSFER,
            status=TransactionStatus.SUCCESS
        ).aggregate(total=Sum('amount'), count=Count('id'))
    else:
        deposits = {'total': 0, 'count': 0}
        withdrawals = {'total': 0, 'count': 0}
        transfers_sent = {'total': 0, 'count': 0}
        transfers_received = {'total': 0, 'count': 0}
    
    context = {
        'user_detail': user,
        'balance': balance,
        'transactions': transactions,
        'deposits': deposits,
        'withdrawals': withdrawals,
        'transfers_sent': transfers_sent,
        'transfers_received': transfers_received,
    }
    
    return render(request, 'money_transfer/admin/user_detail.html', context)


@admin_required
def admin_suspend_user_view(request, user_id):
    """Suspendre un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserSuspendForm(request.POST)
        
        if form.is_valid():
            reason = form.cleaned_data['reason']
            
            success, message = AccountService.suspend_account(user, reason)
            
            if success:
                messages.success(request, f" Utilisateur {user.email} suspendu.")
                return redirect('admin_user_detail', user_id=user_id)
            else:
                messages.error(request, message)
        else:
            messages.error(request, " Veuillez corriger les erreurs.")
    else:
        form = UserSuspendForm(initial={'user_id': user_id})
    
    context = {
        'form': form,
        'user_detail': user,
    }
    
    return render(request, 'money_transfer/admin/suspend_user.html', context)


@admin_required
def admin_reactivate_user_view(request, user_id):
    # Réactiver un utilisateur suspendu
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        success, message = AccountService.reactivate_account(user)
        
        if success:
            messages.success(request, f" Utilisateur {user.email} réactivé.")
        else:
            messages.error(request, message)
        
        return redirect('admin_user_detail', user_id=user_id)
    
    return render(request, 'money_transfer/admin/reactivate_user.html', {
        'user_detail': user
    })


@admin_required
def admin_platform_config_view(request):
    """Configuration de la plateforme"""
    platform = Platform.objects.first()
    
    if not platform:
        platform = Platform.objects.create(
            name="Money Transfer Platform",
            withdrawal_fee_rate=2
        )
    
    if request.method == 'POST':
        form = PlatformConfigForm(request.POST, instance=platform)
        
        if form.is_valid():
            form.save()
            messages.success(request, " Configuration mise à jour !")
            return redirect('admin_dashboard')
        else:
            messages.error(request, " Veuillez corriger les erreurs.")
    else:
        form = PlatformConfigForm(instance=platform)
    
    context = {
        'form': form,
        'platform': platform,
    }
    
    return render(request, 'money_transfer/admin/platform_config.html', context)


@admin_required
def admin_transactions_view(request):
    # Liste de toutes les transactions
    
    transactions = Transaction.objects.select_related(
        'sender_account__user',
        'receiver_account__user'
    ).order_by('-created_at')[:100]
    
    # Filtrage par type
    transaction_type = request.GET.get('type')
    if transaction_type:
        transactions = transactions.filter(type=transaction_type)
    
    # Filtrage par statut
    status = request.GET.get('status')
    if status:
        transactions = transactions.filter(status=status)
    
    context = {
        'transactions': transactions,
        'selected_type': transaction_type,
        'selected_status': status,
    }
    
    return render(request, 'money_transfer/admin/transactions.html', context)