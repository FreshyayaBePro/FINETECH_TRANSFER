"""
Formulaires Django pour Money Transfer
"""
# Formulaires d'authentification
from .auth_forms import (
    UserRegistrationForm,
    UserLoginForm,
    OTPValidationForm,
    RequestOTPForm,
    PasswordResetRequestForm,
    PasswordResetConfirmForm,
    ProfileUpdateForm,
)

# Formulaires de transactions
from .transaction_forms import (
    DepositForm,
    WithdrawalForm,
    TransferForm,
    TransactionSearchForm,
)

# Formulaires administrateur
from .admin_forms import (
    UserSuspendForm,
    UserReactivateForm,
    PlatformConfigForm,
    UserSearchForm,
    AdminDepositForm,
    StatisticsFilterForm,
)

__all__ = [
    # Auth forms
    'UserRegistrationForm',
    'UserLoginForm',
    'OTPValidationForm',
    'RequestOTPForm',
    'PasswordResetRequestForm',
    'PasswordResetConfirmForm',
    'ProfileUpdateForm',
    
    # Transaction forms
    'DepositForm',
    'WithdrawalForm',
    'TransferForm',                                                                                                                                                                                                                                                                                                                                                                                                                                     
    'TransactionSearchForm',
    
    # Admin forms
    'UserSuspendForm',
    'UserReactivateForm',
    'PlatformConfigForm',
    'UserSearchForm',
    'AdminDepositForm',
    'StatisticsFilterForm',
]