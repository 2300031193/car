from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Car, Booking, Location
from datetime import date, datetime

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['name', 'model', 'number_plate', 'price_per_day', 'image', 'availability']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'number_plate': forms.TextInput(attrs={'class': 'form-control'}),
            'price_per_day': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'availability': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class BookingForm(forms.ModelForm):
    # Add time fields separately to handle them properly
    pickup_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        required=False
    )
    return_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        required=False
    )
    
    # Add additional options
    gps_navigation = forms.BooleanField(
        required=False, 
        label='GPS Navigation ($5/day)',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    child_seat = forms.BooleanField(
        required=False, 
        label='Child Seat ($3/day)',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    additional_driver = forms.BooleanField(
        required=False, 
        label='Additional Driver ($10/day)',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Customer notes
    customer_notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    
    class Meta:
        model = Booking
        fields = [
            'car', 
            'start_date', 
            'end_date', 
            'pickup_location', 
            'return_location',
            'payment_method'
        ]
        widgets = {
            'car': forms.HiddenInput(),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'pickup_location': forms.Select(attrs={'class': 'form-control'}),
            'return_location': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Load active locations only
        active_locations = Location.objects.filter(is_active=True)
        self.fields['pickup_location'].queryset = active_locations
        self.fields['return_location'].queryset = active_locations
        
        # Set initial values if instance has them
        if self.instance and self.instance.pk:
            if self.instance.pickup_time:
                self.fields['pickup_time'].initial = self.instance.pickup_time
            if self.instance.return_time:
                self.fields['return_time'].initial = self.instance.return_time
            
            # Set additional options if they exist
            if self.instance.additional_options:
                if 'gps_navigation' in self.instance.additional_options:
                    self.fields['gps_navigation'].initial = True
                if 'child_seat' in self.instance.additional_options:
                    self.fields['child_seat'].initial = True
                if 'additional_driver' in self.instance.additional_options:
                    self.fields['additional_driver'].initial = True

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        car = cleaned_data.get('car')
        pickup_location = cleaned_data.get('pickup_location')
        return_location = cleaned_data.get('return_location')

        errors = []

        # Validate dates
        if start_date and end_date:
            # Check if start date is not in the past
            if start_date < date.today():
                errors.append(ValidationError("Start date cannot be in the past."))

            # Check if end date is after start date
            if end_date < start_date:
                errors.append(ValidationError("End date should be after start date."))

            # Check if car is available for the selected date range
            if car and not errors:  # Only check availability if dates are valid
                try:
                    # Exclude current booking if we're editing
                    bookings = Booking.objects.filter(car=car)
                    if self.instance and self.instance.pk:
                        bookings = bookings.exclude(pk=self.instance.pk)
                    
                    # Only consider confirmed, pending or active bookings
                    bookings = bookings.filter(status__in=['pending', 'confirmed', 'active'])
                    
                    for booking in bookings:
                        if (start_date <= booking.end_date and end_date >= booking.start_date):
                            errors.append(ValidationError(
                                f"This car is already booked for the selected dates. "
                                f"Available after {booking.end_date.strftime('%B %d, %Y')}."
                            ))
                            break  # Break after first conflict
                except Exception as e:
                    # Log the error but don't stop the form processing
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error checking car availability: {str(e)}")
        
        # Validate that pickup and return locations are provided
        if not pickup_location:
            errors.append(ValidationError("Please select a pickup location."))
        if not return_location:
            errors.append(ValidationError("Please select a return location."))

        # Raise all collected errors at once
        if errors:
            raise ValidationError(errors)

        return cleaned_data
        
    def save(self, commit=True):
        booking = super().save(commit=False)
        
        # Save times
        booking.pickup_time = self.cleaned_data.get('pickup_time')
        booking.return_time = self.cleaned_data.get('return_time')
        
        # Save customer notes
        booking.customer_notes = self.cleaned_data.get('customer_notes', '')
        
        # Process additional options
        additional_options = {}
        option_costs = {
            'gps_navigation': 5,
            'child_seat': 3,
            'additional_driver': 10
        }
        
        for option, cost in option_costs.items():
            if self.cleaned_data.get(option, False):
                # Calculate total cost based on number of days
                days = (booking.end_date - booking.start_date).days + 1
                total_option_cost = cost * days
                additional_options[option] = total_option_cost
        
        booking.additional_options = additional_options if additional_options else None
        
        if commit:
            booking.save()
        
        return booking
