import os
import django

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'employee_attendance.settings')
django.setup()

from attendance.models import Employee, Roster, Attendance
from django.utils import timezone
import datetime

def seed_database():
    print("🌱 Starting employee database seeding...")
    
    # Seed manager user
    from django.contrib.auth.models import User
    User.objects.filter(username='teacher').delete()
    teacher = User.objects.create_user(username='teacher', email='manager@company.com', password='teacher123')
    teacher.is_staff = True
    teacher.is_superuser = True
    teacher.save()
    print("👤 Created default manager account: teacher / teacher123")
    
    # Clean existing data
    print("🧹 Cleaning out existing employee roster and attendance lists...")
    Attendance.objects.all().delete()
    Roster.objects.all().delete()
    Employee.objects.all().delete()
    
    # Define employees
    mock_employees = [
        # Engineering
        {"first_name": "Alice", "last_name": "Smith", "department": "Engineering", "avatar_emoji": "💻", "avatar_color": "#A0C4FF", "shift": "morning"},
        {"first_name": "Bob", "last_name": "Johnson", "department": "Engineering", "avatar_emoji": "💼", "avatar_color": "#CAFFBF", "shift": "afternoon"},
        {"first_name": "Charlie", "last_name": "Brown", "department": "Engineering", "avatar_emoji": "🚀", "avatar_color": "#9BF6FF", "shift": "night"},
        {"first_name": "Grace", "last_name": "Hopper", "department": "Engineering", "avatar_emoji": "💡", "avatar_color": "#BDB2FF", "shift": "morning"},
        
        # Sales & Marketing
        {"first_name": "Diana", "last_name": "Prince", "department": "Sales & Marketing", "avatar_emoji": "📈", "avatar_color": "#FFC6FF", "shift": "morning"},
        {"first_name": "Evan", "last_name": "Wright", "department": "Sales & Marketing", "avatar_emoji": "🎯", "avatar_color": "#FFD6A5", "shift": "afternoon"},
        {"first_name": "Hal", "last_name": "Jordan", "department": "Sales & Marketing", "avatar_emoji": "📣", "avatar_color": "#CAFFBF", "shift": "night"},
        
        # Human Resources
        {"first_name": "Fiona", "last_name": "Gallagher", "department": "Human Resources", "avatar_emoji": "🤝", "avatar_color": "#FDFFB6", "shift": "morning"},
        {"first_name": "George", "last_name": "Clooney", "department": "Human Resources", "avatar_emoji": "☕", "avatar_color": "#FFADAD", "shift": "morning"},
        
        # Operations
        {"first_name": "Tony", "last_name": "Stark", "department": "Operations", "avatar_emoji": "🛠️", "avatar_color": "#FFADAD", "shift": "afternoon"},
        {"first_name": "Bruce", "last_name": "Banner", "department": "Operations", "avatar_emoji": "📦", "avatar_color": "#CAFFBF", "shift": "morning"},
        
        # Customer Success
        {"first_name": "Clark", "last_name": "Kent", "department": "Customer Success", "avatar_emoji": "🛡️", "avatar_color": "#A0C4FF", "shift": "morning"}
    ]
    
    # Save to Database
    count = 0
    today = timezone.localdate()
    
    for emp_data in mock_employees:
        pin = f"{1000 + count + 1}"
        employee = Employee.objects.create(
            first_name=emp_data["first_name"],
            last_name=emp_data["last_name"],
            department=emp_data["department"],
            avatar_emoji=emp_data["avatar_emoji"],
            avatar_color=emp_data["avatar_color"],
            pin_code=pin
        )
        print(f"👔 Created employee: {employee.full_name} in {employee.department} ({employee.avatar_emoji}) - PIN: {employee.pin_code}")
        
        # Assign today's shift roster
        Roster.objects.create(
            employee=employee,
            date=today,
            shift=emp_data["shift"]
        )
        print(f"   📅 Scheduled roster: {emp_data['shift']} shift for today")
        
        # Pre-populate some attendance entries for today to make dashboard look rich and alive!
        if emp_data["first_name"] == "Alice":
            # Alice checked in at 06:05 AM (present) and has not checked out yet
            checkin = timezone.make_aware(datetime.datetime.combine(today, datetime.time(6, 5)))
            Attendance.objects.create(
                employee=employee,
                date=today,
                shift="morning",
                status="present",
                work_mode="office",
                checked_in_at=checkin
            )
            print("   ✅ Checked in Alice: Office (Active)")
            
        elif emp_data["first_name"] == "Fiona":
            # Fiona checked in at 06:10 AM (present) and checked out at 02:10 PM (completed 8 hours)
            checkin = timezone.make_aware(datetime.datetime.combine(today, datetime.time(6, 10)))
            checkout = timezone.make_aware(datetime.datetime.combine(today, datetime.time(14, 10)))
            Attendance.objects.create(
                employee=employee,
                date=today,
                shift="morning",
                status="present",
                work_mode="remote",
                checked_in_at=checkin,
                checked_out_at=checkout
            )
            print("   ✅ Checked out Fiona: Remote (Completed 8.0 hrs)")
            
        elif emp_data["first_name"] == "George":
            # George checked in at 07:15 AM (late for morning shift) and is still on-site
            checkin = timezone.make_aware(datetime.datetime.combine(today, datetime.time(7, 15)))
            Attendance.objects.create(
                employee=employee,
                date=today,
                shift="morning",
                status="late",
                work_mode="office",
                checked_in_at=checkin
            )
            print("   ⏰ Checked in George: Office (Late)")
            
        elif emp_data["first_name"] == "Diana":
            # Diana checked in at 06:00 AM (present) and checked out at 01:30 PM (completed 7.5 hours)
            checkin = timezone.make_aware(datetime.datetime.combine(today, datetime.time(6, 0)))
            checkout = timezone.make_aware(datetime.datetime.combine(today, datetime.time(13, 30)))
            Attendance.objects.create(
                employee=employee,
                date=today,
                shift="morning",
                status="present",
                work_mode="field",
                checked_in_at=checkin,
                checked_out_at=checkout
            )
            print("   ✅ Checked out Diana: Field (Completed 7.5 hrs)")

        count += 1
        
    print(f"✨ Seeding complete! Added {count} employees and shift assignments successfully.")

if __name__ == "__main__":
    seed_database()
