"""Accounts forms."""

from django import forms
from django.contrib.auth.forms import UserCreationForm

from apps.accounts.models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True,
        help_text='You must be 18 or older to register.',
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'date_of_birth', 'password1', 'password2']

    def clean_date_of_birth(self):
        from datetime import date
        dob = self.cleaned_data['date_of_birth']
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise forms.ValidationError('You must be 18 years or older to register.')
        return dob


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'avatar', 'odds_format', 'receive_promotions', 'receive_bet_updates',
        ]
        widgets = {
            'avatar': forms.FileInput(),
        }
