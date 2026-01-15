"""
Commande Django pour créer un administrateur avec compte virtuel
Usage: python manage.py create_admin
"""

from django.core.management.base import BaseCommand
from money_transfer.models import User
from money_transfer.services import AccountService, TransactionService
from money_transfer.models.user import UserStatus
from money_transfer.models import VirtualAccount

class Command(BaseCommand):
    help = 'Crée un administrateur avec un compte virtuel activé'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email de l\'administrateur',
            default='yaya@example.com'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Mot de passe',
            default='yaya123456'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            help='Prénom',
            default='Yaya'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            help='Nom',
            default='System'
        )
        parser.add_argument(
            '--phone',
            type=str,
            help='Téléphone',
            default='+22890000010'
        )
        parser.add_argument(
            '--balance',
            type=int,
            help='Solde initial',
            default=100000
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        phone = options['phone']
        initial_balance = options['balance']

        self.stdout.write(self.style.HTTP_INFO('🔧 Création de l\'administrateur...'))

        # 1. Créer ou récupérer l'admin
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'  Utilisateur {email} existe déjà'))
            user = User.objects.get(email=email)
        else:
            user = User.objects.create_superuser(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                gender='M'
            )
            self.stdout.write(self.style.SUCCESS(f' Superuser créé : {email}'))

        # 2. Créer le compte virtuel
        if not hasattr(user, 'virtual_account') or not user.virtual_account:
            account = VirtualAccount.objects.create(
            user=user,
            balance=0,
            is_active=True  
        )
            self.stdout.write(self.style.SUCCESS(f' Compte virtuel créé : ID={account.id}'))
        else:
            account = user.virtual_account
            self.stdout.write(self.style.HTTP_INFO(f'ℹ  Compte existe : ID={account.id}'))

        # 3. Activer le compte
        if user.status != UserStatus.ACTIVE or not user.is_verified:
            success, message = AccountService.activate_account(user)
            if success:
                self.stdout.write(self.style.SUCCESS(f' Compte activé'))
            else:
                self.stdout.write(self.style.ERROR(f' {message}'))

        # 4. Dépôt initial
        if account.balance == 0 and initial_balance > 0:
            success, msg, txn = TransactionService.deposit(user, initial_balance)
            if success:
                self.stdout.write(self.style.SUCCESS(f' Dépôt de {initial_balance:,} FCFA effectué'))
            else:
                self.stdout.write(self.style.ERROR(f' {msg}'))

        # 5. Résumé
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.HTTP_INFO(' RÉSUMÉ DU COMPTE'))
        self.stdout.write('='*60)
        self.stdout.write(f' Email       : {user.email}')
        self.stdout.write(f' Nom         : {user.first_name} {user.last_name}')
        self.stdout.write(f' Téléphone   : {user.phone}')
        self.stdout.write(f' Admin       : {" Oui" if user.is_staff else " Non"}')
        self.stdout.write(f'✓  Vérifié     : {" Oui" if user.is_verified else " Non"}')
        self.stdout.write(f' Solde       : {account.balance:,} FCFA')
        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('\n Admin prêt à l\'emploi !'))
        self.stdout.write(f'\n Connectez-vous :')
        self.stdout.write(f'   URL      : http://localhost:8000/')
        self.stdout.write(f'   Email    : {email}')
        self.stdout.write(f'   Password : {password}')
        self.stdout.write('='*60 + '\n')