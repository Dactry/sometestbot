from ports.bookings_port import BookingRepository


def list_bookings_for_date(repo: BookingRepository, incoming_date: str):
    return repo.list_bookings_for_date(incoming_date)
