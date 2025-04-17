from django.core.management.base import BaseCommand
from rental.models import Location

class Command(BaseCommand):
    help = 'Add initial locations to the database'

    def handle(self, *args, **kwargs):
        # Clear existing locations
        Location.objects.all().delete()
        
        # Create new locations
        locations = [
            {
                'name': 'Main Office',
                'address': '123 Main Street',
                'city': 'New York'
            },
            {
                'name': 'Airport Terminal',
                'address': 'Terminal 5, Airport Road',
                'city': 'New York'
            },
            {
                'name': 'Downtown Branch',
                'address': '555 Park Avenue',
                'city': 'New York'
            },
            {
                'name': 'Uptown Branch',
                'address': '789 Broadway',
                'city': 'New York'
            }
        ]
        
        for location_data in locations:
            Location.objects.create(**location_data)
            self.stdout.write(self.style.SUCCESS(f'Created location: {location_data["name"]}'))
            
        self.stdout.write(self.style.SUCCESS('Successfully added all locations'))