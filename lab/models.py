from django.db import models
from accounts.models import User


class Laboratory(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    manager = models.OneToOneField(User, on_delete=models.CASCADE, related_name='laboratory')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Laboratory'
        verbose_name_plural = 'Laboratories'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.status})"

    @property
    def is_approved(self):
        return self.status == self.STATUS_APPROVED
