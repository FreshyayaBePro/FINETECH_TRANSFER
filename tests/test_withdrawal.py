import pytest
from django.contrib.auth import get_user_model
from wallets.models import VirtualAccount
from transactions.services import withdraw_money

User = get_user_model()


@pytest.mark.django_db
def test_withdraw_money():
    user = User.objects.create_user(
        email="withdraw@test.com",
        phone="92000000",
        password="pass1234",
        is_verified=True
    )

    account = VirtualAccount.objects.create(
        user=user,
        balance=20000,
        is_active=True
    )

    withdraw_money(account, amount=5000, fee=500)

    account.refresh_from_db()
    assert account.balance == 14500
