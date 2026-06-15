from django import forms
from .models import Laboratory
from accounts.models import User


class LabRegistrationForm(forms.Form):
    lab_name = forms.CharField(max_length=200, label='Laboratory Name')
    username = forms.CharField(max_length=150, label='Username')
    city = forms.CharField(max_length=100, label='City')
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Address')
    phone = forms.CharField(max_length=20, label='Phone Number')
    password = forms.CharField(widget=forms.PasswordInput, label='Password')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        username = cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already taken.")
        return cleaned_data


class LaboratoryUpdateForm(forms.ModelForm):
    class Meta:
        model = Laboratory
        fields = ['name', 'city', 'address', 'phone']
