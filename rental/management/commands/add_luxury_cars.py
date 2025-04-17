import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from rental.models import Car
from decimal import Decimal
import shutil

class Command(BaseCommand):
    help = 'Add luxury cars with images to the database'

    def handle(self, *args, **kwargs):
        # Define cars to add
        luxury_cars = [
            {
                'name': 'Mercedes-Benz',
                'model': 'AMG GT',
                'number_plate': 'MER-AMGT',
                'price_per_day': Decimal('175.00'),
                'image_name': 'luxury1.svg',
                'availability': True
            },
            {
                'name': 'Range Rover',
                'model': 'Sport HSE',
                'number_plate': 'RR-HSE21',
                'price_per_day': Decimal('160.00'),
                'image_name': 'luxury2.svg',
                'availability': True
            },
            {
                'name': 'Lamborghini',
                'model': 'Huracán EVO',
                'number_plate': 'LAMBO-EVO',
                'price_per_day': Decimal('350.00'),
                'image_name': 'luxury3.svg',
                'availability': True
            },
            {
                'name': 'Bentley',
                'model': 'Continental GT',
                'number_plate': 'BENT-GT',
                'price_per_day': Decimal('275.00'),
                'image_name': 'luxury4.svg',
                'availability': True
            },
            {
                'name': 'Ferrari',
                'model': '488 GTB',
                'number_plate': 'FER-488',
                'price_per_day': Decimal('325.00'),
                'image_name': 'luxury5.svg',
                'availability': True
            },
            {
                'name': 'Audi',
                'model': 'R8 Spyder',
                'number_plate': 'AUDI-R8S',
                'price_per_day': Decimal('220.00'),
                'image_name': 'luxury1.svg',  # Reusing image for now
                'availability': True
            },
            {
                'name': 'Rolls-Royce',
                'model': 'Ghost',
                'number_plate': 'RR-GHOST',
                'price_per_day': Decimal('400.00'),
                'image_name': 'luxury4.svg',  # Reusing image for now
                'availability': True
            },
            {
                'name': 'Maserati',
                'model': 'GranTurismo',
                'number_plate': 'MAS-GT',
                'price_per_day': Decimal('180.00'),
                'image_name': 'luxury5.svg',  # Reusing image for now
                'availability': True
            },
            {
                'name': 'Aston Martin',
                'model': 'DB11',
                'number_plate': 'AST-DB11',
                'price_per_day': Decimal('290.00'),
                'image_name': 'luxury3.svg',  # Reusing image for now
                'availability': True
            },
            {
                'name': 'Porsche',
                'model': 'Taycan Turbo S',
                'number_plate': 'POR-TYCS',
                'price_per_day': Decimal('230.00'),
                'image_name': 'luxury2.svg',  # Reusing image for now
                'availability': True
            }
        ]
        
        # Create media/cars directory if it doesn't exist
        media_car_dir = os.path.join(settings.MEDIA_ROOT, 'cars')
        os.makedirs(media_car_dir, exist_ok=True)
        
        # Path to static SVG files
        static_car_dir = os.path.join(settings.STATIC_ROOT, 'img', 'cars')
        
        # Add each car
        for car_data in luxury_cars:
            # Check if car already exists with same number plate
            if Car.objects.filter(number_plate=car_data['number_plate']).exists():
                self.stdout.write(self.style.WARNING(
                    f"Car with number plate {car_data['number_plate']} already exists. Skipping."
                ))
                continue
                
            # Create car object
            car = Car(
                name=car_data['name'],
                model=car_data['model'],
                number_plate=car_data['number_plate'],
                price_per_day=car_data['price_per_day'],
                availability=car_data['availability']
            )
            
            # Copy image from static to media
            src_path = os.path.join(static_car_dir, car_data['image_name'])
            if os.path.exists(src_path):
                # Copy the file to media directory
                dst_path = os.path.join(media_car_dir, car_data['image_name'])
                shutil.copy(src_path, dst_path)
                
                # Set the image field with the relative path
                relative_path = f"cars/{car_data['image_name']}"
                car.image = relative_path
                
                self.stdout.write(self.style.SUCCESS(
                    f"Image copied from {src_path} to {dst_path}"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"Image not found at {src_path}. Car added without image."
                ))
            
            # Save the car to the database
            car.save()
            
            self.stdout.write(self.style.SUCCESS(
                f"Added {car.name} {car.model} with plate {car.number_plate}"
            ))

        self.stdout.write(self.style.SUCCESS("Finished adding luxury cars!"))
