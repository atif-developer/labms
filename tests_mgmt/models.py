from django.db import models
from django.utils import timezone
from accounts.models import User
from lab.models import Laboratory


class TestCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Test Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Test(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(TestCategory, on_delete=models.CASCADE, related_name='tests')
    description = models.TextField(blank=True)
    preparation_instructions = models.TextField(blank=True)
    unit = models.CharField(max_length=50, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE, related_name='tests', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tests')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.code:
            last = Test.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.code = f"TST{next_id:05d}"
        super().save(*args, **kwargs)


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    patient_id = models.CharField(max_length=20, unique=True, blank=True)
    laboratory = models.ForeignKey(
        Laboratory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers'
    )
    blood_group = models.CharField(max_length=5, blank=True, choices=[
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Patient: {self.user.get_full_name()} [{self.patient_id}]"

    def save(self, *args, **kwargs):
        if not self.patient_id:
            last = Customer.objects.order_by('-id').first()
            if last and last.patient_id:
                try:
                    num = int(last.patient_id.replace('PAT', '')) + 1
                except ValueError:
                    num = 1
            else:
                num = 1
            self.patient_id = f'PAT{num:05d}'
        super().save(*args, **kwargs)


class TestOrder(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_SAMPLE_COLLECTED = 'sample_collected'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SAMPLE_COLLECTED, 'Sample Collected'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    order_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE, related_name='orders')
    tests = models.ManyToManyField(Test, through='OrderTest')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    ordered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_orders')
    notes = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    whatsapp_notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number} - {self.customer}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            last = TestOrder.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.order_number = f"ORD{next_id:06d}"
        super().save(*args, **kwargs)


class OrderTest(models.Model):
    order = models.ForeignKey(TestOrder, on_delete=models.CASCADE, related_name='order_tests')
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    result_file = models.FileField(upload_to='results/', blank=True, null=True)

    def __str__(self):
        return f"{self.order.order_number} - {self.test.name}"

    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.test.price
        super().save(*args, **kwargs)


class Notification(models.Model):
    TYPE_WHATSAPP = 'whatsapp'
    TYPE_EMAIL = 'email'
    TYPE_SMS = 'sms'
    TYPE_CHOICES = [
        (TYPE_WHATSAPP, 'WhatsApp'),
        (TYPE_EMAIL, 'Email'),
        (TYPE_SMS, 'SMS'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    order = models.ForeignKey(TestOrder, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_WHATSAPP)
    message = models.TextField()
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} to {self.user} - {'Sent' if self.is_sent else 'Failed'}"
