from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_CUSTOMER = 'customer'
    ROLE_LAB_MANAGER = 'lab_manager'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_CUSTOMER, 'Customer'),
        (ROLE_LAB_MANAGER, 'Lab Manager'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)
    phone = models.CharField(max_length=20, blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True, help_text='With country code e.g. +923001234567')
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_customer(self):
        return self.role == self.ROLE_CUSTOMER

    @property
    def is_lab_manager(self):
        return self.role == self.ROLE_LAB_MANAGER
