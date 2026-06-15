"""
Service layer for WhatsApp notifications and business logic.
"""
from django.conf import settings
from django.utils import timezone
from .models import Notification


def send_whatsapp_notification(user, order, message):
    """Send WhatsApp notification via Twilio."""
    notification = Notification.objects.create(
        user=user,
        order=order,
        notification_type=Notification.TYPE_WHATSAPP,
        message=message,
    )

    if not user.whatsapp_number:
        notification.error_message = "No WhatsApp number on file."
        notification.save()
        return False

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        to_number = f"whatsapp:{user.whatsapp_number}"
        msg = client.messages.create(
            body=message,
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=to_number,
        )
        notification.is_sent = True
        notification.sent_at = timezone.now()
        notification.save()
        return True
    except Exception as e:
        notification.error_message = str(e)
        notification.save()
        return False


def notify_result_ready(order):
    """Notify customer that test results are ready."""
    customer = order.customer
    user = customer.user
    site_url = settings.SITE_URL

    message = (
        f"*Lab Results Ready* ✅\n\n"
        f"Dear {user.get_full_name()},\n\n"
        f"Your test results for Order *{order.order_number}* are now available.\n\n"
        f"🔬 Laboratory: {order.laboratory.name}\n"
        f"📋 Patient ID: {customer.patient_id}\n\n"
        f"You can download your results by visiting:\n"
        f"{site_url}/orders/{order.id}/results/\n\n"
        f"For queries, contact the lab at: {order.laboratory.phone}\n\n"
        f"_This is an automated message. Please do not reply._"
    )

    return send_whatsapp_notification(user, order, message)


def calculate_order_total(order):
    """Calculate and update order total."""
    total = sum(ot.price for ot in order.order_tests.all())
    order.total_amount = total
    order.save(update_fields=['total_amount'])
    return total


def check_all_results_uploaded(order):
    """Check if all tests in an order have results uploaded."""
    order_tests = order.order_tests.all()
    if not order_tests.exists():
        return False
    return all(
        ot.result_file for ot in order_tests
    )
