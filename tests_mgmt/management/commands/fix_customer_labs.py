from django.core.management.base import BaseCommand
from tests_mgmt.models import Customer, TestOrder


class Command(BaseCommand):
    help = 'Link existing customers to laboratory based on their orders'

    def handle(self, *args, **kwargs):
        fixed = 0
        customers = Customer.objects.filter(laboratory__isnull=True)

        for customer in customers:
            order = TestOrder.objects.filter(
                customer=customer
            ).select_related('laboratory').order_by('-created_at').first()

            if order and order.laboratory:
                customer.laboratory = order.laboratory
                customer.save(update_fields=['laboratory'])
                fixed += 1
                self.stdout.write(
                    f'Fixed: {customer.patient_id} → {order.laboratory.name}'
                )
            else:
                self.stdout.write(
                    f'No orders found for: {customer.patient_id} — skipped'
                )

        self.stdout.write(f'Done! Fixed {fixed} customers.')
