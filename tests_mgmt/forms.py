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
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)
    whatsapp_number = forms.CharField(max_length=20, required=False, 
                                      help_text='With country code e.g. +923001234567')
    gender = forms.ChoiceField(choices=[('', '-- Select --'), ('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)

    class Meta:
        model = Customer
        fields = ['blood_group']

    def __init__(self, *args, **kwargs):
        self.instance_user = kwargs.pop('user_instance', None)
        super().__init__(*args, **kwargs)
        if self.instance_user:
            self.fields['first_name'].initial = self.instance_user.first_name
            self.fields['last_name'].initial = self.instance_user.last_name
            self.fields['email'].initial = self.instance_user.email
            self.fields['phone'].initial = self.instance_user.phone
            self.fields['whatsapp_number'].initial = self.instance_user.whatsapp_number
            self.fields['gender'].initial = self.instance_user.gender
            self.fields['date_of_birth'].initial = self.instance_user.date_of_birth
            self.fields['address'].initial = self.instance_user.address


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
