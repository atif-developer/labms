from twilio.rest import Client
from django.conf import settings
import json


def send_whatsapp_notification(to_number, pdf_url):
    try:
        client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        message = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to_number}",
            content_sid="HXec23e7e9959fe0e7b00353256b9f6831",
            content_variables=json.dumps({
                "1": pdf_url
            }),
        )
        return True, message.sid
    except Exception as e:
        print(f"WhatsApp error: {e}")
        return False, str(e)


def notify_result_ready(order):
    try:
        customer = order.customer
        to_number = customer.user.whatsapp_number or customer.user.phone
        if not to_number:
            return False

        pdf_url = f"{settings.SITE_URL}/tests/orders/{order.pk}/download-result/"

        success, result = send_whatsapp_notification(to_number, pdf_url)

        if success:
            order.whatsapp_notified = True
            order.save(update_fields=['whatsapp_notified'])

            from .models import Notification
            Notification.objects.create(
                order=order,
                user=customer.user,
                notification_type=Notification.TYPE_WHATSAPP,
                message=f"WhatsApp sent to {to_number}",
                is_sent=True
            )
        return success
    except Exception as e:
        print(f"notify_result_ready error: {e}")
        return False


def check_all_results_uploaded(order):
    order_tests = order.order_tests.all()
    if not order_tests.exists():
        return False
    return all(ot.result_file for ot in order_tests)


def calculate_order_total(order):
    total = sum(ot.price for ot in order.order_tests.all())
    order.total_amount = total
    order.save(update_fields=['total_amount'])
    return total
