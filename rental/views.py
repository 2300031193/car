from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import User
from .models import Car, Booking, Location
from .forms import UserRegisterForm, CarForm, BookingForm
from datetime import date
from django.utils import timezone

def is_admin(user):
    """Check if the user is an admin"""
    return user.is_staff

def home(request):
    """Home page view"""
    cars = Car.objects.filter(availability=True)[:6]  # Show 6 available cars on homepage
    return render(request, 'rental/new_home.html', {'cars': cars})

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})

def logout_view(request):
    """Custom logout view that works with both GET and POST requests"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

@login_required
def car_list(request):
    """View all available cars with search and filter functionality"""
    # Start with all cars or only available cars if no filter applied
    show_all = request.GET.get('show_all', '') == 'true'
    if show_all:
        cars = Car.objects.all()
    else:
        cars = Car.objects.filter(availability=True)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        # Search in name, model, or number_plate fields
        from django.db.models import Q
        cars = cars.filter(
            Q(name__icontains=search_query) |
            Q(model__icontains=search_query) |
            Q(number_plate__icontains=search_query)
        )
    
    # Price filter
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    
    # Handle min price
    min_price_value = None
    if min_price:
        try:
            min_price_value = float(min_price)
            cars = cars.filter(price_per_day__gte=min_price_value)
        except ValueError:
            # Invalid value, but we'll keep it for the form display
            messages.warning(request, "Invalid minimum price value. Please enter a valid number.")
    
    # Handle max price
    max_price_value = None
    if max_price:
        try:
            max_price_value = float(max_price)
            cars = cars.filter(price_per_day__lte=max_price_value)
        except ValueError:
            # Invalid value, but we'll keep it for the form display
            messages.warning(request, "Invalid maximum price value. Please enter a valid number.")
            
    # Validate price range (min should be less than max)
    if min_price_value and max_price_value and min_price_value > max_price_value:
        messages.warning(request, "Minimum price cannot be greater than maximum price. Showing all cars within the individual price ranges.")
    
    # Sort functionality
    sort_by = request.GET.get('sort', '')
    if sort_by == 'price_low':
        cars = cars.order_by('price_per_day')
    elif sort_by == 'price_high':
        cars = cars.order_by('-price_per_day')
    elif sort_by == 'name':
        cars = cars.order_by('name')
    
    context = {
        'cars': cars,
        'search_query': search_query,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'show_all': show_all
    }
    
    return render(request, 'rental/new_car_list.html', context)

@login_required
def book_car(request, car_id):
    """Book a car"""
    car = get_object_or_404(Car, id=car_id)
    
    # Check if car is available first
    if not car.availability:
        messages.error(request, 
            f'Sorry, {car.name} {car.model} is currently not available for booking. Please choose another vehicle.')
        return redirect('car_list')
    
    locations = Location.objects.filter(is_active=True)
    
    # Check if we have locations in the database
    if not locations.exists():
        messages.warning(request, 
            'No pickup locations are currently available in the system. Please contact customer service.')
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.car = car
            booking.status = 'pending'  # Set initial status
            
            # Temporarily mark the car as unavailable
            car.availability = False
            car.save()
            
            # Save to generate total price with additional options
            booking.save()
            
            messages.success(request, 
                f'You have successfully booked the {car.name} {car.model}! '
                f'Your booking reference is: #{booking.pk}')
            
            # Send confirmation email (commented out for now)
            # send_booking_confirmation_email(request.user, booking)
            
            return redirect('booking_history')
    else:
        # Create default values for a new booking
        from datetime import date, timedelta
        tomorrow = date.today() + timedelta(days=1)
        five_days_later = date.today() + timedelta(days=5)
        
        # Set default values for a new booking
        initial_data = {
            'car': car,
            'start_date': tomorrow,
            'end_date': five_days_later,
            # Default to first location for both pickup and return if available
            'pickup_location': locations.first() if locations.exists() else None,
            'return_location': locations.first() if locations.exists() else None,
        }
        form = BookingForm(initial=initial_data)
    
    # Get existing bookings for this car to show availability
    existing_bookings = Booking.objects.filter(
        car=car, 
        status__in=['pending', 'confirmed', 'active'],
        end_date__gte=date.today()

    ).order_by('start_date')
    
    # For the calendar UI - mark dates that are already booked
    booked_periods = []
    for booking in existing_bookings:
        booked_periods.append({
            'from': booking.start_date.strftime('%Y-%m-%d'),
            'to': booking.end_date.strftime('%Y-%m-%d'),
            'booking_id': booking.id
        })
    
    context = {
        'form': form, 
        'car': car,
        'locations': locations,
        'existing_bookings': existing_bookings,
        'booked_periods': booked_periods,
        # Calculate rental cost for preview
        'daily_price': car.price_per_day,
        'additional_options': {
            'gps_navigation': 5,
            'child_seat': 3,
            'additional_driver': 10
        }
    }
    
    return render(request, 'rental/new_car_booking.html', context)

@login_required
def booking_history(request):
    """View booking history for the current user"""
    bookings = Booking.objects.filter(user=request.user)
    
    # Get the current date for template context
    from datetime import datetime
    from django.db.models import Sum
    now = datetime.now().date()
    
    # Group bookings by status
    upcoming_bookings = []
    active_bookings = []
    past_bookings = []
    cancelled_bookings = []
    
    for booking in bookings:
        if booking.status == 'cancelled':
            cancelled_bookings.append(booking)
        elif booking.is_upcoming():
            upcoming_bookings.append(booking)
        elif booking.is_active():
            active_bookings.append(booking)
        else:
            past_bookings.append(booking)
    
    # Find next upcoming booking if any exists
    next_booking = None
    if upcoming_bookings:
        next_booking = min(upcoming_bookings, key=lambda b: b.start_date)
    
    # Calculate total money spent
    total_spent = bookings.exclude(status='cancelled').aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    # Get frequently booked cars
    car_bookings = {}
    favorite_car = None
    for booking in bookings:
        car_id = booking.car.id
        if car_id in car_bookings:
            car_bookings[car_id]['count'] += 1
        else:
            car_bookings[car_id] = {
                'car': booking.car,
                'count': 1
            }
    
    if car_bookings:
        favorite_car = max(car_bookings.values(), key=lambda x: x['count'])['car']
    
    # Calculate total rental days
    total_days = sum([booking.get_duration_days() for booking in bookings.exclude(status='cancelled')])
    
    # If no bookings, pass some available cars for recommendations
    context = {
        'all_bookings': bookings,
        'bookings': bookings,  # For backwards compatibility
        'upcoming_bookings': upcoming_bookings,
        'active_bookings': active_bookings,
        'past_bookings': past_bookings,
        'cancelled_bookings': cancelled_bookings,
        'now': now,
        'next_booking': next_booking,
        'total_spent': total_spent,
        'favorite_car': favorite_car,
        'total_days': total_days
    }
    
    if not bookings.exists():
        recommended_cars = Car.objects.filter(availability=True)[:3]
        context['recommended_cars'] = recommended_cars
        
    return render(request, 'rental/new_booking_history.html', context)

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard to view all bookings"""
    from django.utils import timezone
    today = timezone.now().date()
    
    bookings = Booking.objects.all()
    cars = Car.objects.all()
    
    # Get unavailable cars count
    unavailable_cars = Car.objects.filter(availability=False)
    unavailable_count = unavailable_cars.count()
    total_cars = Car.objects.count()
    available_count = total_cars - unavailable_count
    
    context = {
        'bookings': bookings,
        'cars': cars,
        'unavailable_cars': unavailable_cars,
        'unavailable_count': unavailable_count,
        'available_count': available_count,
        'total_cars': total_cars,
    }
    
    return render(request, 'rental/admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def add_car(request):
    """Add a new car"""
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Car added successfully!')
            return redirect('admin_dashboard')
    else:
        form = CarForm()
    return render(request, 'rental/car_form.html', {'form': form, 'title': 'Add Car'})

@login_required
@user_passes_test(is_admin)
def edit_car(request, car_id):
    """Edit an existing car"""
    car = get_object_or_404(Car, id=car_id)
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            form.save()
            messages.success(request, 'Car updated successfully!')
            return redirect('admin_dashboard')
    else:
        form = CarForm(instance=car)
    return render(request, 'rental/car_form.html', {'form': form, 'title': 'Edit Car'})

@login_required
@user_passes_test(is_admin)
def delete_car(request, car_id):
    """Delete a car"""
    car = get_object_or_404(Car, id=car_id)
    car.delete()
    messages.success(request, 'Car deleted successfully!')
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin)
def manage_users(request):
    """View all users (read-only for now)"""
    users = User.objects.all()
    return render(request, 'rental/manage_users.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def manage_bookings(request):
    """Manage all bookings with options to accept or decline"""
    all_bookings = Booking.objects.all().order_by('-booking_date')
    
    # Filter functionality
    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = all_bookings.filter(status=status_filter)
    else:
        bookings = all_bookings
    
    # Date range filter
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    
    if from_date:
        bookings = bookings.filter(start_date__gte=from_date)
    if to_date:
        bookings = bookings.filter(end_date__lte=to_date)
    
    # Search by user or car
    search_query = request.GET.get('search', '')
    if search_query:
        from django.db.models import Q
        bookings = bookings.filter(
            Q(user__username__icontains=search_query) |
            Q(car__name__icontains=search_query) |
            Q(car__model__icontains=search_query) |
            Q(invoice_number__icontains=search_query)
        )
    
    from django.utils import timezone
    today = timezone.now().date()
    # Group bookings by status for tab display
    pending_bookings = all_bookings.filter(status='pending')
    confirmed_bookings = all_bookings.filter(status='confirmed')
    # Get active bookings that need attention (haven't been accepted/declined yet)
    active_bookings = Booking.objects.filter(
        status='active',
        end_date__gte=today
    ).order_by('-booking_date')
    
    # Get upcoming bookings that need attention
    upcoming_bookings = Booking.objects.filter(
        status='confirmed',
        start_date__gt=today
    ).order_by('start_date')
    
    # Combine active and upcoming bookings
    active_and_upcoming = list(active_bookings) + list(upcoming_bookings)
    
    # Get pending active bookings (those that haven't been accepted/declined)
    pending_active_bookings = Booking.objects.filter(
        status='active',
        end_date__gte=today,
        payment_status=False  # These need attention for payment
    ).order_by('-booking_date')
    completed_bookings = all_bookings.filter(status='completed')
    declined_bookings = all_bookings.filter(status='cancelled')
    
    context = {
        'bookings': bookings,
        'pending_bookings': pending_bookings,
        'confirmed_bookings': confirmed_bookings,
        'active_bookings': active_bookings,
        'completed_bookings': completed_bookings,
        'declined_bookings': declined_bookings,
        'status_filter': status_filter,
        'from_date': from_date,
        'to_date': to_date,
        'search_query': search_query,
    }
    
    return render(request, 'rental/manage_bookings.html', context)

@login_required
@user_passes_test(is_admin)
def booking_action(request, booking_id, action):
    """Accept or decline a booking"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    if action == 'accept':
        booking.status = 'confirmed'
        
        # If the booking is for the current date, mark it as active
        from datetime import date
        today = date.today()
        if booking.start_date <= today <= booking.end_date:
            booking.status = 'active'
            
        messages.success(request, f'Booking #{booking.id} has been accepted.')
        
    elif action == 'decline':
        booking.status = 'cancelled'
        # Make the car available again
        booking.car.availability = True
        booking.car.save()
        messages.success(request, f'Booking #{booking.id} has been declined.')
        
    elif action == 'complete':
        booking.status = 'completed'
        # Make the car available again
        booking.car.availability = True
        booking.car.save()
        messages.success(request, f'Booking #{booking.id} has been marked as completed.')
    
    # Always save booking after status change
    booking.save()
    
    # Redirect back to the booking management page
    return redirect('manage_bookings')
