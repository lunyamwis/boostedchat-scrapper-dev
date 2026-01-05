# Create your views here.
from django.shortcuts import render
from api.bookings.models import Room, AirbnbListing, AirbnbReservation
from api.bookings.services.dashboard_service import booking_kpis, revenue_timeseries, airbnb_kpis, airbnb_revenue_chart
from api.bookings.services.sync_reservations import sync_reservations
from api.bookings.services.payout_service import process_airbnb_payout
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

import json


def dashboard(request, booking_room_id):
    room = Room.objects.get(booking_room_id=booking_room_id)

    kpis = booking_kpis(room)
    labels, data = revenue_timeseries(room)

    return render(request, "bookings/dashboard.html", {
        "room": room,
        "kpis": kpis,
        "labels": labels,
        "data": data
    })

def airbnb_dashboard(request, listing_id):
    listing = AirbnbListing.objects.get(id=listing_id)

    kpis = airbnb_kpis(listing)
    labels, data = airbnb_revenue_chart(listing)

    return render(request, "bookings/airbnb_dashboard.html", {
        "listing": listing,
        "kpis": kpis,
        "labels": json.dumps(labels),
        "data": json.dumps(data)
    })



@csrf_exempt
def airbnb_webhook(request):
    payload = json.loads(request.body)
    event_type = payload.get("event")
    res = payload.get("reservation")

    if event_type == "reservation.created":
        listing = AirbnbListing.objects.get(listing_id=res["listing_id"])
        reservation,_ = AirbnbReservation.objects.update_or_create(
            reservation_id=res["id"],
            defaults={
                "listing": listing,
                "guest_name": res["guest_name"],
                "checkin": res["checkin"],
                "checkout": res["checkout"],
                "total_amount": res["total_amount"],
                "status": res["status"]
            }
        )
        process_airbnb_payout(reservation)
    elif event_type == "reservation.cancelled":
        try:
            booking = AirbnbReservation.objects.get(reservation_id=res["id"])
            booking.status = "cancelled"
            booking.save()
        except AirbnbReservation.DoesNotExist:
            pass

    return JsonResponse({"status": "ok"})


@csrf_exempt
def booking_com_webhook(request):
    payload = json.loads(request.body)
    try:
        # Webhook can send single or multiple reservations
        reservations = payload.get("reservations", [payload])
        for r in reservations:
            sync_reservations(r)

        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)