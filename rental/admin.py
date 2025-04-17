from django.contrib import admin
from .models import Car, Booking

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('name', 'model', 'number_plate', 'price_per_day', 'availability')
    list_filter = ('availability', 'model')
    search_fields = ('name', 'model', 'number_plate')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'car', 'start_date', 'end_date', 'total_price', 'booking_date')
    list_filter = ('start_date', 'end_date', 'booking_date')
    search_fields = ('user__username', 'car__name', 'car__model')
