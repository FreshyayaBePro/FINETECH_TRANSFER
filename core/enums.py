from django.db import models


class UserStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    SUSPENDED = 'SUSPENDED', 'Suspended'
    PENDING = 'PENDING', 'Pending'


class TransactionStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    SUCCESS = 'SUCCESS', 'Success'
    FAILED = 'FAILED', 'Failed'


class TypeTransaction(models.TextChoices):
    DEPOSIT = 'DEPOSIT', 'Deposit'
    TRANSFER = 'TRANSFER', 'Transfer'
    WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'
    FEE = 'FEE', 'Fee'
