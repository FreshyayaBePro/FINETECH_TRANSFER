"""
Vues Django pour Money Transfer
"""
# Auth views
from .auth import (
    register_view,
    login_view,
    logout_view,
    verify_account_view,
    request_new_otp_view,
    profile_view,
)

# Dashboard views
from .dashboard import (
    dashboard_view,
    transactions_history_view,
    transaction_detail_view,
)

# Transaction views
from .transactions import (
    deposit_view,
    withdrawal_request_view,
    withdrawal_confirm_view,
    transfer_view,
)

# Admin views
from .admin import (
    admin_dashboard_view,
    admin_users_view,
    admin_user_detail_view,
    admin_suspend_user_view,
    admin_reactivate_user_view,
    admin_platform_config_view,
    admin_transactions_view,
)

__all__ = [
    # Auth
    'register_view',
    'login_view',
    'logout_view',
    'verify_account_view',
    'request_new_otp_view',
    'profile_view',
    
    # Dashboard
    'dashboard_view',
    'transactions_history_view',
    'transaction_detail_view',
    
    # Transactions
    'deposit_view',
    'withdrawal_request_view',
    'withdrawal_confirm_view',
    'transfer_view',
    
    # Admin
    'admin_dashboard_view',
    'admin_users_view',
    'admin_user_detail_view',
    'admin_suspend_user_view',
    'admin_reactivate_user_view',
    'admin_platform_config_view',
    'admin_transactions_view',
]