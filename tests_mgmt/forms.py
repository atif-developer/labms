from django import forms
from .models import TestCategory, Test, Customer, TestOrder, OrderTest
from accounts.models import User
from lab.models import Laboratory


class TestCategoryForm(forms.ModelForm):
    class Meta:
        model = TestCategory
        fields = ['name', 'description']


class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['name', 'category', 'laboratory', 'price']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_lab_manager:
            try:
                lab = user.laboratory
                self.fields['laboratory'].queryset = Laboratory.objects.filter(pk=lab.pk)
                self.fields['laboratory'].initial = lab
                self.fields['laboratory'].widget.attrs['disabled'] = True
            except Exception:
                self.fields['laboratory'].queryset = Laboratory.objects.none()
        else:
            self.fields['laboratory'].queryset = Laboratory.objects.filter(status='approved')

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Test name is required.")
        return name

    def clean_category(self):
        category = self.cleaned_data.get('category')
        if not category:
            raise forms.ValidationError("Category is required.")
        return category

    def clean_laboratory(self):
        laboratory = self.cleaned_data.get('laboratory')
        if not laboratory:
            raise forms.ValidationError("Laboratory is required.")
        return laboratory

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is None:
            raise forms.ValidationError("Price is required.")
        if price <= 0:
            raise forms.ValidationError("Price must be greater than 0.")
        return price


class CustomerForm(forms.ModelForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=False)
    phone = forms.CharField(required=False)
    whatsapp_number = forms.CharField(required=False)
    gender = forms.ChoiceField(
        choices=[('', '-- Select --'), ('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        required=False
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3})
    )
    blood_group = forms.ChoiceField(
        choices=[
            ('', '-- Select Blood Group --'),
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-'),
        ],
        required=False
    )

    class Meta:
        model = Customer
        fields = ['blood_group']

    def __init__(self, *args, **kwargs):
        kwargs.pop('user_instance', None)  # accept but ignore legacy kwarg
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            user = self.instance.user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            self.fields['phone'].initial = user.phone
            self.fields['whatsapp_number'].initial = user.whatsapp_number
            self.fields['gender'].initial = user.gender
            self.fields['date_of_birth'].initial = user.date_of_birth
            self.fields['address'].initial = user.address
            self.fields['blood_group'].initial = self.instance.blood_group

    def save(self, commit=True):
        customer = super().save(commit=False)
        if customer.pk:
            user = customer.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data.get('email', '')
            user.phone = self.cleaned_data.get('phone', '')
            user.whatsapp_number = self.cleaned_data.get('whatsapp_number', '')
            user.gender = self.cleaned_data.get('gender', '')
            user.date_of_birth = self.cleaned_data.get('date_of_birth')
            user.address = self.cleaned_data.get('address', '')
            if commit:
                user.save()
            customer.blood_group = self.cleaned_data.get('blood_group', '')
            if commit:
                customer.save()
        return customer


class TestOrderForm(forms.ModelForm):
    class Meta:
        model = TestOrder
        fields = ['customer', 'laboratory', 'tests', 'notes', 'is_paid']
        widgets = {'tests': forms.CheckboxSelectMultiple()}

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.role == User.ROLE_LAB_MANAGER:
            try:
                lab = user.laboratory
                self.fields['laboratory'].queryset = Laboratory.objects.filter(id=lab.id)
                self.fields['laboratory'].initial = lab
                self.fields['tests'].queryset = Test.objects.filter(laboratory=lab, is_active=True)
            except Exception:
                pass
        else:
            self.fields['tests'].queryset = Test.objects.filter(is_active=True)


class UploadResultForm(forms.ModelForm):
    class Meta:
        model = OrderTest
        fields = ['result_file']

    def clean_result_file(self):
        file = self.cleaned_data.get('result_file')
        if not file:
            raise forms.ValidationError("Please upload a PDF file.")
        if hasattr(file, 'name') and not file.name.endswith('.pdf'):
            raise forms.ValidationError("Only PDF files are allowed.")
        return file
