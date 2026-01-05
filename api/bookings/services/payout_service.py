import requests
import os
from django.conf import settings
from django.core.mail import send_mail
from api.bookings.models import Payout, AirbnbReservation
from api.bookings.services.airbnb_api import AirbnbAPI

PAYSTACK_URL = "https://api.paystack.co/transfer"

def process_payout(booking):
    commission = booking.total_amount * 0.10
    payout_amount = booking.total_amount - commission

    amount = booking.total_amount  # in KES

    # Create payment request via Paystack
    payload = {
        "amount": int(amount * 100),  # Paystack expects amount in the smallest currency unit
        "email": booking.guest_email,
        "currency": "KES",
        "callback_url": "https://lunyamwi.org",
        "reference": f"BOOKING-{booking.booking_id}"
    }

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    r = requests.post("https://api.paystack.co/paymentrequest", json=payload, headers=headers)
    r.raise_for_status()
    data = r.json()
    payment_link = data.get("data", {}).get("authorization_url")

    # Send email to guest
    subject = f"Payment for your booking {booking.booking_id}"
    message = (
        f"Hello {booking.guest_name},\n\n"
        f"Thank you for booking {booking.room.name}.\n"
        f"Please complete your payment of KES {amount:,} using the link below:\n\n"
        f"{payment_link}\n\n"
        f"If you have any questions or need assistance, feel free to chat with me on WhatsApp: "
        f"https://wa.me/{booking.host_number}"
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [booking.guest_email],
        fail_silently=False
    )

    # Optional: mark booking as payment requested
    booking.payment_requested = True
    booking.save()


def process_airbnb_payout(reservation):
    """
    Generate Paystack payment link for Airbnb reservation and send it to the guest via Airbnb message.
    """
    if reservation.payout_processed:
        return

    # 1️⃣ Calculate payout and commission
    commission = reservation.total_amount * 0.10
    payment_amount = reservation.total_amount  # full amount the guest should pay

    # 2️⃣ Create Paystack Payment Request (checkout link)
    payload = {
        "amount": int(payment_amount * 100),  # Paystack expects amount in smallest unit (kobo)
        "email": reservation.guest_email,     # if available; Airbnb may not provide
        "currency": "KES",
        "callback_url": "https://lunyamwi.org",
        "reference": f"AIRBNB-{reservation.reservation_id}"
    }

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.post("https://api.paystack.co/paymentrequest", json=payload, headers=headers)
        r.raise_for_status()
        payment_data = r.json().get("data", {})
        payment_link = payment_data.get("authorization_url", None)
    except Exception as e:
        print(f"Failed to create Paystack payment link: {e}")
        payment_link = None

    # 3️⃣ Send message to Airbnb guest via Airbnb API
    api = AirbnbAPI()
    message_text = f"Hello {reservation.guest_name},\n\n"
    message_text += f"Thank you for booking {reservation.listing.name}.\n"
    if payment_link:
        message_text += f"Please complete your payment of KES {payment_amount:,} using this link:\n{payment_link}\n\n"
    else:
        message_text += f"Your total payment of KES {payment_amount:,} is due. Please contact us if you have any issues.\n\n"
    message_text += f"If you have any questions or need assistance, feel free to chat with me on WhatsApp: https://wa.me/{reservation.host_number}"
    
    try:
        api.send_message(reservation_id=reservation.reservation_id, message=message_text)
    except Exception as e:
        print(f"Failed to send Airbnb message: {e}")

    # 4️⃣ Mark reservation as payout/payment link sent
    reservation.payout_processed = True
    reservation.save()

