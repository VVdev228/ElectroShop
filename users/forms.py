"""
Форми додатку 'users'.
Реєстрація та авторизація з Bootstrap-стилізацією.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Форма реєстрації нового користувача."""

    first_name = forms.CharField(
        max_length=30,
        label="Ім'я",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Введіть ім'я",
        }),
    )
    last_name = forms.CharField(
        max_length=30,
        label='Прізвище',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введіть прізвище',
        }),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.ua',
        }),
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label='Телефон',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+380 (99) 123-45-67',
        }),
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'phone',
                  'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Придумайте логін',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Придумайте пароль',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Повторіть пароль',
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.CLIENT
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
        return user


class ProfileEditForm(forms.ModelForm):
    """Форма редагування профілю користувача."""

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone', 'address')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'phone':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+380 (99) 123-45-67'}),
            'address':    forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    """Форма зміни пароля з Bootstrap-стилізацією."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введіть поточний пароль',
        })
        self.fields['old_password'].label = 'Поточний пароль'
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введіть новий пароль',
        })
        self.fields['new_password1'].label = 'Новий пароль'
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Повторіть новий пароль',
        })
        self.fields['new_password2'].label = 'Підтвердження нового пароля'


class CustomUserLoginForm(AuthenticationForm):
    """Форма входу до системи."""

    username = forms.CharField(
        label='Логін',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введіть логін',
        }),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введіть пароль',
        }),
    )
