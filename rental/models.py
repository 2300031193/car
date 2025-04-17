from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class Car(models.Model):
    name = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    number_plate = models.CharField(max_length=20, unique=True)
    price_per_day = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='cars/', null=True, blank=True)
    availability = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.model} ({self.number_plate})"

class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.city}"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('cash', 'Cash on Pickup'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    booking_date = models.DateTimeField(auto_now_add=True)
    
    # New fields
    pickup_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='pickup_bookings')
    return_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='return_bookings')
    pickup_time = models.TimeField(null=True, blank=True)
    return_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    payment_status = models.BooleanField(default=False)
    invoice_number = models.CharField(max_length=20, null=True, blank=True)
    additional_options = models.JSONField(null=True, blank=True)  # Stores optional extras like GPS, child seat, etc.
    customer_notes = models.TextField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.car.name} ({self.start_date} to {self.end_date})"

    def save(self, *args, **kwargs):
        # Calculate total price based on the number of days and price per day
        days = (self.end_date - self.start_date).days + 1
        
        # Base price calculation
        base_price = days * self.car.price_per_day
        
        # Add costs of any additional options
        additional_cost = 0
        if self.additional_options:
            for option, cost in self.additional_options.items():
                if isinstance(cost, (int, float)):
                    additional_cost += cost
        
        self.total_price = base_price + additional_cost
        
        # Generate invoice number if needed
        if not self.invoice_number and self.status == 'confirmed':
            # Format: INV-YYYY-XXXXX (year-sequential number)
            from django.utils import timezone
            year = timezone.now().year
            last_invoice = Booking.objects.filter(invoice_number__isnull=False).order_by('-invoice_number').first()
            
            if last_invoice and last_invoice.invoice_number:
                try:
                    last_num = int(last_invoice.invoice_number.split('-')[2])
                    new_num = last_num + 1
                except (IndexError, ValueError):
                    new_num = 1
            else:
                new_num = 1
                
            self.invoice_number = f"INV-{year}-{new_num:05d}"
        
        super().save(*args, **kwargs)
    
    def get_duration_days(self):
        """Returns the rental duration in days"""
        return (self.end_date - self.start_date).days + 1
    
    def is_upcoming(self):
        """Check if this is an upcoming booking"""
        from django.utils import timezone
        return self.start_date > timezone.now().date()
    
    def is_active(self):
        """Check if this is an active booking (customer currently has the car)"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date and self.status != 'cancelled'
        
    def is_completed(self):
        """Check if this booking is completed (past the end date)"""
        from django.utils import timezone
        return self.end_date < timezone.now().date() and self.status != 'cancelled'
    
    def days_until_pickup(self):
        """Returns the number of days until pickup"""
        from django.utils import timezone
        today = timezone.now().date()
        if self.start_date > today:
            return (self.start_date - today).days
        return 0
        
    class Meta:
        ordering = ['-booking_date']
