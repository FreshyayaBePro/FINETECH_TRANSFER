# Formulaires d'authentification et de gestion de compte

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from money_transfer.models.user import User , OTPType


class UserRegistrationForm(UserCreationForm):
    # Formulaire d'inscription utilisateur
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'votre.email@example.com'
        }),
        label="Email"
    )
    
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Prénom'
        }),
        label="Prénom"
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Nom'
        }),
        label="Nom"
    )
    
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '+228 90 00 00 00'
        }),
        label="Téléphone"
    )
    
    gender = forms.ChoiceField(
        choices=[
            ('M', 'Masculin'),
            ('F', 'Féminin')        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        }),
        label="Genre"
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Mot de passe (min. 8 caractères)'
        }),
        label="Mot de passe"
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Confirmez le mot de passe'
        }),
        label="Confirmation"
    )
    
    accept_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
        }),
        label="J'accepte les conditions générales d'utilisation"
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'gender', 'password1', 'password2']
    
    def clean_email(self):
        # Vérifie que l'email est unique
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Cette adresse email est déjà utilisée.")
        return email.lower()
    
    def clean_phone(self):
        # Vérifie que le numéro de téléphone est unique
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exists():
            raise ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return phone
    
    def clean_password2(self):
        # Vérifie que les deux mots de passe correspondent
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        
        if password1 and password2 and password1 != password2:
            raise ValidationError("Les mots de passe ne correspondent pas.")
        
        return password2


class UserLoginForm(AuthenticationForm):
    # Formulaire de connexion
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'votre.email@example.com',
            'autofocus': True
        }),
        label="Email"
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Mot de passe'
        }),
        label="Mot de passe"
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
        }),
        label="Se souvenir de moi"
    )


class OTPValidationForm(forms.Form):
  
    # Formulaire de validation OTP
  
    code = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 text-center text-2xl font-mono tracking-widest border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': '000000',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric',
            'autocomplete': 'off'
        }),
        label="Code de validation"
    )
    
    def clean_code(self):
        # Valide que le code ne contient que des chiffres
        code = self.cleaned_data.get('code')
        
        if not code.isdigit():
            raise ValidationError("Le code doit contenir uniquement des chiffres.")
        
        if len(code) != 6:
            raise ValidationError("Le code doit contenir exactement 6 chiffres.")
        
        return code


class RequestOTPForm(forms.Form):
    # Formulaire pour demander un nouveau code OTP
    otp_type = forms.ChoiceField(
        choices=OTPType.choices,
        widget=forms.HiddenInput(),
        required=True
    )


class PasswordResetRequestForm(forms.Form):
    # Formulaire de demande de réinitialisation de mot de passe
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'votre.email@example.com'
        }),
        label="Email"
    )
    
    def clean_email(self):
        # Vérifie que l'email existe
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise ValidationError("Aucun compte associé à cet email.")
        return email.lower()


class PasswordResetConfirmForm(forms.Form):
    # Formulaire de confirmation de réinitialisation de mot de passe
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Nouveau mot de passe'
        }),
        label="Nouveau mot de passe"
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Confirmez le mot de passe'
        }),
        label="Confirmation"
    )
    
    def clean_password2(self):
        # Vérifie que les deux mots de passe correspondent
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        
        if password1 and password2 and password1 != password2:
            raise ValidationError("Les mots de passe ne correspondent pas.")
        
        # Validation de la force du mot de passe
        if len(password1) < 8:
            raise ValidationError("Le mot de passe doit contenir au moins 8 caractères.")
        
        return password2


class ProfileUpdateForm(forms.ModelForm):
    # Formulaire de mise à jour du profil utilisateur
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'gender']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'gender': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
        }
    
    def clean_phone(self):
        # Vérifie que le téléphone n'est pas déjà utilisé par un autre utilisateur
        phone = self.cleaned_data.get('phone')
        user_id = self.instance.id
        
        if User.objects.filter(phone=phone).exclude(id=user_id).exists():
            raise ValidationError("Ce numéro de téléphone est déjà utilisé.")
        
        return phone