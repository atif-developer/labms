from twilio.rest import Client
from django.conf import settings
import json


def send_whatsapp_notification(to_number, pdf_url):
    try:
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        from_number = settings.TWILIO_WHATSAPP_FROM

        if not account_sid or not auth_token:
            print("ERROR: Twilio credentials missing!")
            return False

        client = Client(account_sid, auth_token)
        message = client.messages.create(
            from_=from_number,
            to=f"whatsapp:{to_number}",
            content_sid="HXec23e7e9959fe0e7b00353256b9f6831",
            content_variables=json.dumps({
                "1": pdf_url
            }),
        )
        print(f"WhatsApp sent! SID: {message.sid}")
        return True
    except Exception as e:
        print(f"WhatsApp ERROR: {e}")
        return False


def notify_result_ready(order):
    try:
        customer = order.customer
        user = customer.user

        to_number = user.whatsapp_number or user.phone
        if not to_number:
            print(f"ERROR: No WhatsApp/phone number for {user.get_full_name()}")
            return False

        to_number = to_number.strip().replace(' ', '')

        site_url = settings.SITE_URL.rstrip('/')
        pdf_url = f"{site_url}/tests/orders/{order.pk}/download-result/"

        print(f"Sending WhatsApp to: {to_number}")
        print(f"PDF URL: {pdf_url}")

        success = send_whatsapp_notification(to_number, pdf_url)

        from .models import Notification
        Notification.objects.create(
            order=order,
            user=user,
            message=f"WhatsApp {'sent' if success else 'FAILED'} to {to_number}. PDF: {pdf_url}",
            is_sent=success
        )

        if success:
            order.whatsapp_notified = True
            order.save(update_fields=['whatsapp_notified'])

        return success

    except Exception as e:
        print(f"notify_result_ready ERROR: {e}")
        try:
            from .models import Notification
            Notification.objects.create(
                order=order,
                message=f"WhatsApp FAILED — Error: {str(e)}",
                is_sent=False
            )
        except Exception:
            pass
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
