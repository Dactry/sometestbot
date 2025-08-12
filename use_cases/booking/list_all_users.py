from ports.bookings_port import BookingRepository


def list_all_users(repo: BookingRepository):
    return repo.list_all_users()
