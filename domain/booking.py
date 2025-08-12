from dataclasses import dataclass


@dataclass
class Booking:
    user_id: int
    date: str
    times: list[str]
