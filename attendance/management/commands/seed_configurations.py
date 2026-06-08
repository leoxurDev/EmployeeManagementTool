from django.core.management.base import BaseCommand
from attendance.models import DepartmentOption, AvatarEmoji, AvatarColor


class Command(BaseCommand):
    help = 'Seed initial configuration options (departments, avatar emojis, colors)'

    def handle(self, *args, **options):
        # Department options
        departments = [
            {'emoji': '💻', 'name': 'Engineering', 'description': 'Software Development & IT', 'order': 0},
            {'emoji': '📈', 'name': 'Sales & Marketing', 'description': 'Customer Acquisition & Growth', 'order': 1},
            {'emoji': '🤝', 'name': 'Human Resources', 'description': 'People Operations & Talent', 'order': 2},
            {'emoji': '📞', 'name': 'Customer Success', 'description': 'Support & Client Relations', 'order': 3},
            {'emoji': '🚚', 'name': 'Operations', 'description': 'Logistics & Supply Chain', 'order': 4},
            {'emoji': '💰', 'name': 'Finance', 'description': 'Accounting & Treasury', 'order': 5},
            {'emoji': '🎨', 'name': 'Design', 'description': 'Product & Creative UI/UX', 'order': 6},
            {'emoji': '💡', 'name': 'Research & Dev', 'description': 'Innovation & New Products', 'order': 7},
        ]
        
        for dept in departments:
            obj, created = DepartmentOption.objects.get_or_create(
                name=dept['name'],
                defaults={
                    'emoji': dept['emoji'],
                    'description': dept['description'],
                    'order': dept['order']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created department: {obj}"))
            else:
                self.stdout.write(f"Department already exists: {obj}")
        
        # Avatar emojis (Professional and office theme)
        emojis = [
            {'emoji': '💼', 'name': 'Briefcase', 'order': 0},
            {'emoji': '💻', 'name': 'Laptop', 'order': 1},
            {'emoji': '📊', 'name': 'Bar Chart', 'order': 2},
            {'emoji': '📈', 'name': 'Line Chart', 'order': 3},
            {'emoji': '🎨', 'name': 'Palette', 'order': 4},
            {'emoji': '🛠️', 'name': 'Hammer & Wrench', 'order': 5},
            {'emoji': '🚀', 'name': 'Rocket', 'order': 6},
            {'emoji': '💡', 'name': 'Light Bulb', 'order': 7},
            {'emoji': '🔑', 'name': 'Key', 'order': 8},
            {'emoji': '📣', 'name': 'Megaphone', 'order': 9},
            {'emoji': '📦', 'name': 'Package', 'order': 10},
            {'emoji': '🩺', 'name': 'Stethoscope', 'order': 11},
            {'emoji': '⚖️', 'name': 'Scales', 'order': 12},
            {'emoji': '🛡️', 'name': 'Shield', 'order': 13},
            {'emoji': '☕', 'name': 'Coffee', 'order': 14},
            {'emoji': '🎯', 'name': 'Bullseye', 'order': 15},
        ]
        
        for emoji in emojis:
            obj, created = AvatarEmoji.objects.get_or_create(
                emoji=emoji['emoji'],
                defaults={'name': emoji['name'], 'order': emoji['order']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created emoji: {obj}"))
            else:
                self.stdout.write(f"Emoji already exists: {obj}")
        
        # Avatar colors
        colors = [
            {'hex_code': '#FFADAD', 'name': 'Pastel Red', 'order': 0},
            {'hex_code': '#FFD6A5', 'name': 'Pastel Orange', 'order': 1},
            {'hex_code': '#2F2F2F', 'name': 'Pastel Black', 'order': 2},
            {'hex_code': '#FDFFB6', 'name': 'Pastel Yellow', 'order': 3},
            {'hex_code': '#CAFFBF', 'name': 'Pastel Green', 'order': 4},
            {'hex_code': '#9BF6FF', 'name': 'Pastel Cyan', 'order': 5},
            {'hex_code': '#A0C4FF', 'name': 'Pastel Blue', 'order': 6},
            {'hex_code': '#BDB2FF', 'name': 'Pastel Purple', 'order': 7},
            {'hex_code': '#FFC6FF', 'name': 'Pastel Pink', 'order': 8},
        ]
        
        for color in colors:
            obj, created = AvatarColor.objects.get_or_create(
                hex_code=color['hex_code'],
                defaults={'name': color['name'], 'order': color['order']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created color: {obj}"))
            else:
                self.stdout.write(f"Color already exists: {obj}")
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded all configurations!'))
