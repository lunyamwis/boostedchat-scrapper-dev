from django.db.models import Sum, Avg, Count, F
from datetime import date, timedelta
from api.bookings.models import Booking, RoomInventory,AirbnbReservation

def booking_kpis(room):
    bookings = Booking.objects.filter(room=room,status="confirmed")

    revenue = bookings.aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    adr = bookings.aggregate(
        adr=Avg("total_amount")
    )["adr"] or 0

    inventory = RoomInventory.objects.filter(room=room)

    occupancy = inventory.aggregate(
        occ=Avg(F("booked_units") * 1.0 / F("total_units"))
    )["occ"] or 0

    revpar = adr * occupancy

    return {
        "revenue": revenue,
        "adr": round(adr, 2),
        "occupancy": round(occupancy * 100, 2),
        "revpar": round(revpar, 2)
    }



def revenue_timeseries(room):
    qs = (
        Booking.objects
        .filter(room=room,status="confirmed")
        .extra(select={"day": "date(checkin)"})
        .values("day")
        .annotate(total=Sum("total_amount"))
        .order_by("day")
    )

    labels = [str(x["day"]) for x in qs]
    data = [float(x["total"]) for x in qs]

    return labels, data

def airbnb_kpis(listing):
    reservations = AirbnbReservation.objects.filter(listing=listing, status="confirmed")

    revenue = reservations.aggregate(total=Sum("total_amount"))["total"] or 0
    adr = reservations.aggregate(adr=Avg("total_amount"))["adr"] or 0

    # Occupancy calculation (simplified: booked nights / total nights in next 7 days)
    today = date.today()
    booked_nights = sum([(r.checkout - r.checkin).days for r in reservations if r.checkout >= today])
    total_nights = 7 * 1  # 1 unit per listing, next 7 days
    occupancy = booked_nights / total_nights if total_nights else 0

    revpar = adr * occupancy
    return {
        "revenue": revenue,
        "adr": round(adr, 2),
        "occupancy": round(occupancy * 100, 2),
        "revpar": round(revpar, 2)
    }

def airbnb_revenue_chart(listing):
    today = date.today()
    labels = []
    data = []
    for i in range(7):
        day = today + timedelta(days=i)
        daily_revenue = AirbnbReservation.objects.filter(
            listing=listing,
            status="confirmed",
            checkin__lte=day,
            checkout__gt=day
        ).aggregate(total=Sum("total_amount"))["total"] or 0
        labels.append(day.strftime("%Y-%m-%d"))
        data.append(float(daily_revenue))
    return labels, data
