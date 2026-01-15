# Vues du dashboard utilisateur
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta

from money_transfer.services import AccountService, TransactionService
from money_transfer.models import Transaction
from money_transfer.models.transaction import TypeTransaction, TransactionStatus
from money_transfer.decorators.decorators import active_user_required


@login_required
def dashboard_view(request):
    # Dashboard principal de l'utilisateur
    user = request.user
    
    # Récupérer le solde
    balance = AccountService.get_balance(user)
    
    # Debug: afficher le solde dans la console
    print(f"DEBUG - Solde de {user.email}: {balance}")
    
    # Vérifier si l'utilisateur peut effectuer des transactions
    can_transact, error_message = AccountService.can_perform_transaction(user)
    
    # Récupérer les dernières transactions
    recent_transactions = TransactionService.get_user_transactions(user, limit=5)
    
    # Statistiques du mois en cours
    now = datetime.now()
    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    account = user.virtual_account if hasattr(user, 'virtual_account') else None
    
    if account:
        # Dépôts du mois
        deposits_this_month = Transaction.objects.filter(
            sender_account=account,
            type=TypeTransaction.DEPOSIT,
            status=TransactionStatus.SUCCESS,
            created_at__gte=first_day_of_month
        ).aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        # Retraits du mois
        withdrawals_this_month = Transaction.objects.filter(
            sender_account=account,
            type=TypeTransaction.WITHDRAWAL,
            status=TransactionStatus.SUCCESS,
            created_at__gte=first_day_of_month
        ).aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        # Transferts envoyés du mois
        transfers_sent_this_month = Transaction.objects.filter(
            sender_account=account,
            type=TypeTransaction.TRANSFER,
            status=TransactionStatus.SUCCESS,
            created_at__gte=first_day_of_month
        ).aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        # Transferts reçus du mois
        transfers_received_this_month = Transaction.objects.filter(
            receiver_account=account,
            type=TypeTransaction.TRANSFER,
            status=TransactionStatus.SUCCESS,
            created_at__gte=first_day_of_month
        ).aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
    else:
        deposits_this_month = {'total': 0, 'count': 0}
        withdrawals_this_month = {'total': 0, 'count': 0}
        transfers_sent_this_month = {'total': 0, 'count': 0}
        transfers_received_this_month = {'total': 0, 'count': 0}
    
    context = {
        'user': user,
        'balance': balance,
        'can_transact': can_transact,
        'error_message': error_message,
        'recent_transactions': recent_transactions,
        'deposits_this_month': deposits_this_month,
        'withdrawals_this_month': withdrawals_this_month,
        'transfers_sent_this_month': transfers_sent_this_month,
        'transfers_received_this_month': transfers_received_this_month,
    }
    
    return render(request, 'money_transfer/dashboard/home.html', context)


@active_user_required
def transactions_history_view(request):
    """Vue de l'historique complet des transactions"""
    user = request.user
    
    # Récupérer toutes les transactions (SANS limite d'abord)
    transactions = TransactionService.get_user_transactions(user, limit=None)
    
    # Filtrage par type si demandé
    transaction_type = request.GET.get('type')
    if transaction_type:
        transactions = transactions.filter(type=transaction_type)
    
    # Filtrage par statut si demandé
    status = request.GET.get('status')
    if status:
        transactions = transactions.filter(status=status)
    
    # Appliquer la limite APRÈS les filtres
    transactions = transactions[:100]
    
    context = {
        'user': user,
        'transactions': transactions,
        'selected_type': transaction_type,
        'selected_status': status,
    }
    
    return render(request, 'money_transfer/dashboard/transactions_history.html', context)


@active_user_required
def transaction_detail_view(request, reference):
    """Vue de détail d'une transaction"""
    user = request.user
    
    # Récupérer la transaction
    transaction = TransactionService.get_transaction_by_reference(reference)
    
    if not transaction:
        messages.error(request, " Transaction introuvable.")
        return redirect('transactions_history')
    
    # Vérifier que l'utilisateur est impliqué dans cette transaction
    account = user.virtual_account if hasattr(user, 'virtual_account') else None
    
    if account:
        is_involved = (
            transaction.sender_account == account or 
            transaction.receiver_account == account
        )
    else:
        is_involved = False
    
    if not is_involved and not user.is_staff:
        messages.error(request, " Vous n'avez pas accès à cette transaction.")
        return redirect('transactions_history')
    
    # Déterminer le rôle de l'utilisateur dans la transaction
    user_role = None
    if account:
        if transaction.sender_account == account:
            user_role = 'sender'
        elif transaction.receiver_account == account:
            user_role = 'receiver'
    
    context = {
        'user': user,
        'transaction': transaction,
        'user_role': user_role,
    }
    
    return render(request, 'money_transfer/dashboard/transaction_detail.html', context)