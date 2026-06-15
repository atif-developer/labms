from django.contrib import admin
from .models import TestCategory, Test, Customer, TestOrder, OrderTest, Notification


@admin.register(TestCategory)
class TestCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'price', 'is_active']
    list_filter = ['category', 'is_active', 'laboratory']
    search_fields = ['name', 'code']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['patient_id', 'user', 'blood_group']
    search_fields = ['patient_id', 'user__first_name', 'user__last_name']


class OrderTestInline(admin.TabularInline):
    model = OrderTest
    extra = 0
    readonly_fields = []


@admin.register(TestOrder)
class TestOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'laboratory', 'status', 'total_amount', 'is_paid', 'created_at']
    list_filter = ['status', 'is_paid', 'laboratory']
    search_fields = ['order_number']
    inlines = [OrderTestInline]
    readonly_fields = ['order_number']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'order', 'notification_type', 'is_sent', 'created_at']
    list_filter = ['notification_type', 'is_sent']
