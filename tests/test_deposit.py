import pytest
from django.contrib.auth import get_user_model
from wallets.models import VirtualAccount
from transactions.services import deposit_money

User = get_user_model()


def test_deposit_money():
    user = User.objects.create_user(
        email="deposit@test.com",
        phone="91000000",
        password="pass1234",
        is_verified=True
    )

    account = VirtualAccount.objects.create(
        user=user,
        balance=0,
        is_active=True
    )

    deposit_money(account, 10000)

    account.refresh_from_db()
    assert account.balance == 10000
