from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Home and authentication
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # User side
    path('cars/', views.car_list, name='car_list'),
    path('book/<int:car_id>/', views.book_car, name='book_car'),
    path('booking-history/', views.booking_history, name='booking_history'),
    
    # Admin side
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('add-car/', views.add_car, name='add_car'),
    path('edit-car/<int:car_id>/', views.edit_car, name='edit_car'),
    path('delete-car/<int:car_id>/', views.delete_car, name='delete_car'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('manage-bookings/', views.manage_bookings, name='manage_bookings'),
    path('booking-action/<int:booking_id>/<str:action>/', views.booking_action, name='booking_action'),
]
