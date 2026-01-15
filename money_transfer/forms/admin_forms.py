"""
Formulaires pour les actions administrateur
"""
from django import forms
from django.core.exceptions import ValidationError
from money_transfer.models import User, Platform
from money_transfer.models.user import UserStatus


class UserSuspendForm(forms.Form):
    """
    Formulaire de suspension d'un utilisateur
    """
    user_id = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    reason = forms.CharField(
        max_length=500,
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent',
            'rows': 4,
            'placeholder': 'Indiquez la raison de la suspension...'
        }),
        label="Raison de la suspension"
    )
    
    def clean_user_id(self):
        """Vérifie que l'utilisateur existe"""
        user_id = self.cleaned_data.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValidationError("Utilisateur introuvable.")
        
        # Vérifier qu'on ne suspend pas un admin
        if user.is_staff or user.is_superuser:
            raise ValidationError("Impossible de suspendre un administrateur.")
        
        # Vérifier que l'utilisateur n'est pas déjà suspendu
        if user.status == UserStatus.SUSPENDED:
            raise ValidationError("Cet utilisateur est déjà suspendu.")
        
        return user_id


class UserReactivateForm(forms.Form):
    """
    Formulaire de réactivation d'un utilisateur
    """
    user_id = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    def clean_user_id(self):
        """Vérifie que l'utilisateur existe et est suspendu"""
        user_id = self.cleaned_data.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValidationError("Utilisateur introuvable.")
        
        # Vérifier que l'utilisateur est bien suspendu
        if user.status != UserStatus.SUSPENDED:
            raise ValidationError("Cet utilisateur n'est pas suspendu.")
        
        return user_id


class PlatformConfigForm(forms.ModelForm):
    """
    Formulaire de configuration de la plateforme
    """
    class Meta:
        model = Platform
        fields = ['name', 'withdrawal_fee_rate']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Nom de la plateforme'
            }),
            'withdrawal_fee_rate': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'min': '0',
                'max': '100',
                'step': '1',
                'placeholder': '2'
            }),
        }
        labels = {
            'name': 'Nom de la plateforme',
            'withdrawal_fee_rate': 'Taux de frais de retrait (%)'
        }
        help_texts = {
            'withdrawal_fee_rate': 'Pourcentage de frais appliqués sur les retraits (ex: 2 pour 2%)'
        }
    
    def clean_withdrawal_fee_rate(self):
        """Valide le taux de frais"""
        rate = self.cleaned_data.get('withdrawal_fee_rate')
        
        if rate < 0:
            raise ValidationError("Le taux ne peut pas être négatif.")
        
        if rate > 100:
            raise ValidationError("Le taux ne peut pas dépasser 100%.")
        
        return rate


class UserSearchForm(forms.Form):
    """
    Formulaire de recherche d'utilisateurs (admin)
    """
    STATUS_CHOICES = [
        ('', 'Tous les statuts'),
        ('ACTIVE', 'Actifs'),
        ('PENDING', 'En attente'),
        ('SUSPENDED', 'Suspendus'),
    ]
    
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Rechercher par email, nom ou téléphone...'
        }),
        label="Recherche"
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        }),
        label="Statut"
    )
    
    is_verified = forms.NullBooleanField(
        required=False,
        widget=forms.Select(
            choices=[
                ('', 'Tous'),
                ('true', 'Vérifiés'),
                ('false', 'Non vérifiés')
            ],
            attrs={
                'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }
        ),
        label="Vérification"
    )
    
    date_joined_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        }),
        label="Inscrit depuis"
    )
    
    date_joined_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        }),
        label="Inscrit jusqu'à"
    )


class AdminDepositForm(forms.Form):
    """
    Formulaire de dépôt administratif (créditer un compte utilisateur)
    """
    user_email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'utilisateur@example.com'
        }),
        label="Email de l'utilisateur"
    )
    
    amount = forms.IntegerField(
        min_value=1,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-lg',
            'placeholder': '10000',
            'min': '1'
        }),
        label="Montant à créditer"
    )
    
    reason = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Ex: Correction suite à erreur technique'
        }),
        label="Motif du crédit"
    )
    
    def clean_user_email(self):
        """Vérifie que l'utilisateur existe"""
        email = self.cleaned_data.get('user_email').lower()
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError("Aucun utilisateur trouvé avec cet email.")
        
        return email
    
    def clean_amount(self):
        """Valide le montant"""
        amount = self.cleaned_data.get('amount')
        
        if amount <= 0:
            raise ValidationError("Le montant doit être positif.")
        
        # Limite de sécurité
        MAX_ADMIN_DEPOSIT = 50_000_000  # 50 millions
        if amount > MAX_ADMIN_DEPOSIT:
            raise ValidationError(
                f"Le montant maximum par opération admin est de {MAX_ADMIN_DEPOSIT:,} FCFA."
            )
        
        return amount


class StatisticsFilterForm(forms.Form):
    """
    Formulaire de filtrage des statistiques
    """
    PERIOD_CHOICES = [
        ('today', "Aujourd'hui"),
        ('week', 'Cette semaine'),
        ('month', 'Ce mois'),
        ('year', 'Cette année'),
        ('custom', 'Période personnalisée'),
    ]
    
    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        required=False,
        initial='month',
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        }),
        label="Période"
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
    
    def clean(self):
        """Validation des dates pour période personnalisée"""
        cleaned_data = super().clean()
        period = cleaned_data.get('period')
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if period == 'custom':
            if not date_from or not date_to:
                raise ValidationError(
                    "Veuillez spécifier les dates de début et de fin pour une période personnalisée."
                )
            
            if date_from > date_to:
                raise ValidationError("La date de début doit être antérieure à la date de fin.")
        
        return cleaned_data