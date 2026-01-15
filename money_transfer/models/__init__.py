"""
Consolidation de tous les models dans une seule app
"""
from .user import User, OTP
from .account import Platform, VirtualAccount
from .transaction import Transaction

__all__ = [
    'User',
    'OTP',
    'Platform',
    'VirtualAccount',
    'Transaction',
]