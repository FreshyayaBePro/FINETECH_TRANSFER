import os
import sys
import django
import random
from datetime import timedelta
from django.utils import timezone


# ===============================
# CONFIG DJANGO (config/settings.py)
# ===============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ajouter la racine du projet au PYTHONPATH
sys.path.insert(0, BASE_DIR)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()

# ===============================
# IMPORTS DJANGO
# ===============================

from accounts.models import User, OTP
from wallets.models import VirtualAccount
from transactions.models import Transaction
from core.enums import UserStatus


def main():
    print(" Initialisation des données de test...")

    users = []

    # =========================
    # 1️⃣ UTILISATEURS (10)
    # =========================
    for i in range(1, 11):
        user, created = User.objects.get_or_create(
            email=f"user{i}@fintech.com",
            defaults={
                "first_name": f"User{i}",
                "last_name": "Test",
                "phone": f"+228900000{i}",
                "gender": "M",
                "status": UserStatus.ACTIVE,
                "is_verified": True,
            }
        )

        if created:
            user.set_password("password123")
            user.save()

        users.append(user)

    print(" 10 utilisateurs créés")

    # =========================
    # 2️ WALLET / COMPTE VIRTUEL
    # =========================

    # for user in users:
    #     VirtualAccount.objects.get_or_create(
    #         user=user,
    #         defaults={
    #             "balance": random.randint(10_000, 100_000),
    #             "is_active": True,
    #         }
    #     )

    # print(" Comptes virtuels créés")


    # =========================
    # 3️ OTP
    # =========================
    # for user in users:
    #     OTP.objects.create(
    #         user=user,
    #         code=str(random.randint(100000, 999999)),
    #         otp_type="ACCOUNT_VALIDATION",
    #         expires_at=timezone.now() + timedelta(minutes=10),
    #     )

    #     OTP.objects.create(
    #         user=user,
    #         code=str(random.randint(100000, 999999)),
    #         otp_type="WITHDRAWAL",
    #         expires_at=timezone.now() + timedelta(minutes=5),
    #     )

    # print(" OTP créés")

    # =========================
    # 4️ TRANSACTIONS
    # =========================
    from transactions.models import Transaction
    from wallets.models import VirtualAccount
    from core.enums import TypeTransaction, TransactionStatus

    for user in users:
        account = user.virtual_account

        # 1️ DÉPÔT
        Transaction.objects.create(
            type=TypeTransaction.DEPOSIT,
            status=TransactionStatus.SUCCESS,
            amount=20_000,
            fee=0,
            net_amount=20_000,
            sender_account=account,
            receiver_account=account,
        )

        # 2️ RETRAIT
        fee = 500
        amount = 10_000

        Transaction.objects.create(
            type=TypeTransaction.WITHDRAWAL,
            status=TransactionStatus.SUCCESS,
            amount=amount,
            fee=fee,
            net_amount=amount - fee,
            sender_account=account,
            receiver_account=None,
        )

    print(" Transactions créées")



if __name__ == "__main__":
    main()
