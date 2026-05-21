"""
Форми додатку 'orders'.
Форма додавання до кошика та форма оформлення замовлення.
"""

from django import forms
from .models import Order


class CartAddProductForm(forms.Form):
    """Форма додавання товару до кошика."""

    quantity = forms.IntegerField(
        min_value=1,
        max_value=99,
        initial=1,
        label='Кількість',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'width: 80px;',
        }),
    )
    override = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput,
    )


class OrderCreateForm(forms.ModelForm):
    """Форма оформлення замовлення."""

    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'notes']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Введіть ім'я",
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введіть прізвище',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@mail.ua',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+380 (99) 123-45-67',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Місто, вулиця, будинок, квартира',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Коментар до замовлення (необов\'язково)',
            }),
        }
