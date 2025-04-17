from django.test import TestCase
from django.contrib.auth.models import User
from .models import Car, Booking
from datetime import date, timedelta

class CarRentalTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )

        # Create a test car
        self.car = Car.objects.create(
            name='Toyota',
            model='Corolla',
            number_plate='ABC123',
            price_per_day=50.00,
            availability=True
        )

    def test_car_creation(self):
        """Test if car is created correctly"""
        self.assertEqual(self.car.name, 'Toyota')
        self.assertEqual(self.car.model, 'Corolla')
        self.assertEqual(self.car.number_plate, 'ABC123')
        self.assertEqual(self.car.price_per_day, 50.00)
        self.assertTrue(self.car.availability)

    def test_booking_creation(self):
        """Test if booking is created correctly with proper total price calculation"""
        start_date = date.today()
        end_date = start_date + timedelta(days=3)
        
        booking = Booking.objects.create(
            user=self.user,
            car=self.car,
            start_date=start_date,
            end_date=end_date
        )
        
        # Check if total price is calculated correctly (4 days * $50 = $200)
        self.assertEqual(booking.total_price, 200.00)
