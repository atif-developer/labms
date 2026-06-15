from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))


class CustomerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)
    whatsapp_number = forms.CharField(max_length=20, required=False, help_text='With country code e.g. +923001234567')
    gender = forms.ChoiceField(choices=[('', '-- Select --'), ('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'whatsapp_number',
                  'gender', 'date_of_birth', 'address', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.ROLE_CUSTOMER
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'whatsapp_number',
                  'gender', 'date_of_birth', 'address', 'profile_picture']
        widgets = {'date_of_birth': forms.DateInput(attrs={'type': 'date'})}


class AdminCreateUserForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20)
    whatsapp_number = forms.CharField(max_length=20, required=False)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone',
                  'whatsapp_number', 'role', 'password1', 'password2']
