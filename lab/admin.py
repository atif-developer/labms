from django.contrib import admin
from .models import Laboratory


@admin.register(Laboratory)
class LaboratoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'phone', 'status', 'manager', 'created_at']
    list_filter = ['status', 'city']
    search_fields = ['name', 'city', 'phone']
    readonly_fields = ['created_at']
