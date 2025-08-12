# def to_minutes(hhmm: str) -> int:
#     """Перетворює час 'HH:MM' у кількість хвилин від півночі."""
#     hours, minutes = map(int, hhmm.split(":"))
#     return hours * 60 + minutes


# def intervals_overlap(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
#     """Повертає True, якщо інтервали [a_start, a_end) і [b_start, b_end) перетинаються."""
#     a_start_min = to_minutes(a_start)
#     a_end_min = to_minutes(a_end)
#     b_start_min = to_minutes(b_start)
#     b_end_min = to_minutes(b_end)

#     return a_start_min < b_end_min and b_start_min < a_end_min


# # Приклади:
# print(intervals_overlap("09:00", "10:00", "09:30", "10:30"))  # True (перетин)
# print(intervals_overlap("09:00", "10:00", "10:00", "11:00"))  # False (дотик)
# print(intervals_overlap("10:00", "12:00", "10:30", "11:30"))  # True (вкладений)
# print(intervals_overlap("09:00", "09:30", "09:31", "10:00"))  # False (розрив)
