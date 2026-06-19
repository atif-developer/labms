from twilio.rest import Client
from django.conf import settings


def send_whatsapp_notification(to_number, pdf_url):
    try:
        client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        message = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to_number}",
            body=f"Your lab test results are ready! Download your report here: {pdf_url}"
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

        to_number = to_number.strip().replace(' ', '').replace('-', '')
        if to_number.startswith('0'):
            to_number = '+92' + to_number[1:]
        if not to_number.startswith('+'):
            to_number = '+' + to_number

        site_url = settings.SITE_URL.rstrip('/')
        first_result = order.order_tests.filter(result_file__isnull=False).exclude(result_file='').first()
        if not first_result:
            print(f"ERROR: No result files found for order {order.order_number}")
            return False
        pdf_url = f"{site_url}/tests/results/{first_result.pk}/download/"

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
