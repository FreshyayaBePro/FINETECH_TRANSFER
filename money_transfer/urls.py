"""
URLs de l'application Money Transfer
"""
from django.urls import path
from money_transfer.views import (
    # Auth
    register_view,
    login_view,
    logout_view,
    verify_account_view,
    request_new_otp_view,
    profile_view,
    
    # Dashboard
    dashboard_view,
    transactions_history_view,
    transaction_detail_view,
    
    # Transactions
    deposit_view,
    withdrawal_request_view,
    withdrawal_confirm_view,
    transfer_view,
    
    # Admin
    admin_dashboard_view,
    admin_users_view,
    admin_user_detail_view,
    admin_suspend_user_view,
    admin_reactivate_user_view,
    admin_platform_config_view,
    admin_transactions_view,
)

urlpatterns = [
    # === AUTHENTIFICATION ===
    path('', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('verify-account/', verify_account_view, name='verify_account'),
    path('request-otp/', request_new_otp_view, name='request_otp'),
    path('profile/', profile_view, name='profile'),
    
    # === DASHBOARD ===
    path('dashboard/', dashboard_view, name='dashboard'),
    path('transactions/', transactions_history_view, name='transactions_history'),
    path('transaction/<uuid:reference>/', transaction_detail_view, name='transaction_detail'),
    
    # === OPÉRATIONS FINANCIÈRES ===
    path('deposit/', deposit_view, name='deposit'),
    path('withdrawal/', withdrawal_request_view, name='withdrawal_request'),
    path('withdrawal/confirm/', withdrawal_confirm_view, name='withdrawal_confirm'),
    path('transfer/', transfer_view, name='transfer'),
    
    # === ADMINISTRATION ===
    path('admin/dashboard/', admin_dashboard_view, name='admin_dashboard'),
    path('admin/users/', admin_users_view, name='admin_users'),
    path('admin/user/<int:user_id>/', admin_user_detail_view, name='admin_user_detail'),
    path('admin/user/<int:user_id>/suspend/', admin_suspend_user_view, name='admin_suspend_user'),
    path('admin/user/<int:user_id>/reactivate/', admin_reactivate_user_view, name='admin_reactivate_user'),
    path('admin/platform-config/', admin_platform_config_view, name='admin_platform_config'),
    path('admin/transactions/', admin_transactions_view, name='admin_transactions'),
]