# from domain.booking import Booking
# from domain.user import User

# first_date, first_times = "2025-12-11", ["10:00AM", "11:00AM"]
# second_date, second_times = "2025-12-12", ["00:00PM", "01:00PM"]

# first_booking = Booking(first_date, first_times)
# second_booking = Booking(second_date, second_times)
# booking_list = [first_booking, second_booking]
# max = User(1, "Max", "dactry", booking_list)


# def test_user():
#     assert max.id == 1
#     assert max.first_name == "Max"
#     assert max.username == "dactry"
#     assert max.booking_list == booking_list
#     assert booking_list[0] in max.booking_list
#     max.remove_booking("")
#     assert len(max.booking_list) == 2
#     max.remove_booking(first_booking.date, first_times[0])
#     assert len(max.booking_list) == 2
#     max.remove_booking(first_booking.date, first_times[1])
#     assert len(max.booking_list) == 1
#     assert len(max.booking_list) == len(booking_list) - 1
