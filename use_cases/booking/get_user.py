from ports.bookings_port import BookingRepository


def get_user(repo: BookingRepository, incoming_user_id: int):
    return repo.get_user(incoming_user_id)
