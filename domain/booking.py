from dataclasses import dataclass, field


@dataclass
class Booking:
    user_id: int
    date: str
    times: list[str]
    id: int | None = field(default=None)
