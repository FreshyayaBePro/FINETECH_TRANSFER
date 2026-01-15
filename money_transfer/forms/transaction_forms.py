"""
Formulaires pour les opérations financières
"""
from django import forms
from django.core.exceptions import ValidationError
from money_transfer.models import User, Platform
from money_transfer.services import AccountService


class DepositForm(forms.Form):
    """
    Formulaire de dépôt d'argent
    """
    amount = forms.IntegerField(
        min_value=1,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-lg',
            'placeholder': '10000',
            'min': '1',
            'step': '1'
        }),
        label="Montant à déposer",
        help_text="Entrez le montant en francs CFA"
    )
    
    def clean_amount(self):
        """Valide que le montant est positif"""
        amount = self.cleaned_data.get('amount')
        
        if amount <= 0:
            raise ValidationError("Le montant doit être positif.")
        
        # Limite maximale de dépôt (optionnel)
        MAX_DEPOSIT = 10_000_000  # 10 millions
        if amount > MAX_DEPOSIT:
            raise ValidationError(f"Le montant maximum par dépôt est de {MAX_DEPOSIT:,} FCFA.")
        
        return amount


class WithdrawalForm(forms.Form):
    """
    Formulaire de retrait d'argent
    """
    amount = forms.IntegerField(
        min_value=1,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent text-lg',
            'placeholder': '5000',
            'min': '1',
            'step': '1'
        }),
        label="Montant à retirer",
        help_text="Entrez le montant en francs CFA (des frais seront appliqués)"
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        # Récupérer les frais de la plateforme
        try:
            platform = Platform.objects.first()
            if platform:
                self.fee_rate = platform.withdrawal_fee_rate
                self.fields['amount'].help_text = (
                    f"Des frais de {self.fee_rate}% seront appliqués sur le retrait"
                )
        except:
            self.fee_rate = 0
    
    def clean_amount(self):
        """Valide le montant et vérifie le solde"""
        amount = self.cleaned_data.get('amount')
        
        if amount <= 0:
            raise ValidationError("Le montant doit être positif.")
        
        # Vérifier le solde si l'utilisateur est fourni
        if self.user:
            balance = AccountService.get_balance(self.user)
            
            if balance < amount:
                raise ValidationError(
                    f"Solde insuffisant. Votre solde actuel est de {balance:,} FCFA."
                )
            
            # Montant minimum de retrait
            MIN_WITHDRAWAL = 500
            if amount < MIN_WITHDRAWAL:
                raise ValidationError(f"Le montant minimum de retrait est de {MIN_WITHDRAWAL} FCFA.")
        
        return amount
    
    def get_fee_amount(self):
        """Calcule le montant des frais"""
        amount = self.cleaned_data.get('amount', 0)
        return (amount * self.fee_rate) // 100 if hasattr(self, 'fee_rate') else 0
    
    def get_net_amount(self):
        """Calcule le montant net après frais"""
        amount = self.cleaned_data.get('amount', 0)
        fee = self.get_fee_amount()
        return amount - fee


class TransferForm(forms.Form):
    """
    Formulaire de transfert d'argent
    """
    receiver_email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'destinataire@example.com'
        }),
        label="Email du destinataire"
    )
    
    amount = forms.IntegerField(
        min_value=1,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg',
            'placeholder': '2000',
            'min': '1',
            'step': '1'
        }),
        label="Montant à transférer",
        help_text="Entrez le montant en francs CFA (aucun frais sur les transferts)"
    )
    
    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Description (optionnel)'
        }),
        label="Description"
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
    
    def clean_receiver_email(self):
        """Valide l'email du destinataire"""
        receiver_email = self.cleaned_data.get('receiver_email').lower()
        
        # Vérifier que le destinataire existe
        try:
            receiver = User.objects.get(email=receiver_email)
        except User.DoesNotExist:
            raise ValidationError("Aucun utilisateur trouvé avec cet email.")
        
        # Vérifier qu'on ne transfère pas à soi-même
        if self.user and receiver.id == self.user.id:
            raise ValidationError("Vous ne pouvez pas effectuer un transfert vers vous-même.")
        
        # Vérifier que le destinataire peut recevoir
        can_receive, error_msg = AccountService.can_perform_transaction(receiver)
        if not can_receive:
            raise ValidationError(f"Le destinataire ne peut pas recevoir de transferts : {error_msg}")
        
        return receiver_email
    
    def clean_amount(self):
        """Valide le montant et vérifie le solde"""
        amount = self.cleaned_data.get('amount')
        
        if amount <= 0:
            raise ValidationError("Le montant doit être positif.")
        
        # Vérifier le solde si l'utilisateur est fourni
        if self.user:
            balance = AccountService.get_balance(self.user)
            
            if balance < amount:
                raise ValidationError(
                    f"Solde insuffisant. Votre solde actuel est de {balance:,} FCFA."
                )
            
            # Montant minimum de transfert
            MIN_TRANSFER = 100
            if amount < MIN_TRANSFER:
                raise ValidationError(f"Le montant minimum de transfert est de {MIN_TRANSFER} FCFA.")
            
            # Montant maximum de transfert par transaction
            MAX_TRANSFER = 5_000_000  # 5 millions
            if amount > MAX_TRANSFER:
                raise ValidationError(f"Le montant maximum par transfert est de {MAX_TRANSFER:,} FCFA.")
        
        return amount


class TransactionSearchForm(forms.Form):
    """
    Formulaire de recherche de transactions
    """
    TRANSACTION_TYPE_CHOICES = [
        ('', 'Tous les types'),
        ('DEPOSIT', 'Dépôts'),
        ('WITHDRAWAL', 'Retraits'),
        ('TRANSFER', 'Transferts'),
        ('FEE', 'Frais'),
    ]
    
    TRANSACTION_STATUS_CHOICES = [
        ('', 'Tous les statuts'),
        ('SUCCESS', 'Réussies'),
        ('PENDING', 'En attente'),
        ('FAILED', 'Échouées'),
    ]
    
    transaction_type = forms.ChoiceField(
        choices=TRANSACTION_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        }),
        label="Type"
    )
    
    status = forms.ChoiceField(
        choices=TRANSACTION_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        }),
        label="Statut"
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        }),
        label="Du"
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        }),
        label="Au"
    )
    
    min_amount = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Montant min'
        }),
        label="Montant minimum"
    )
    
    max_amount = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Montant max'
        }),
        label="Montant maximum"
    )
    
    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        min_amount = cleaned_data.get('min_amount')
        max_amount = cleaned_data.get('max_amount')
        
        # Vérifier la cohérence des dates
        if date_from and date_to and date_from > date_to:
            raise ValidationError("La date de début doit être antérieure à la date de fin.")
        
        # Vérifier la cohérence des montants
        if min_amount and max_amount and min_amount > max_amount:
            raise ValidationError("Le montant minimum doit être inférieur au montant maximum.")
        
        return cleaned_data