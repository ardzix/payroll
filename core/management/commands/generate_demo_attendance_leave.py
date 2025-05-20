from django.core.management.base import BaseCommand
from core.models import Employee, Attendance, Leave
from faker import Faker
import random
import datetime

class Command(BaseCommand):
    help = 'Clear and generate random attendance and leave data for all employees for the current month.'

    def handle(self, *args, **kwargs):
        fake = Faker('id_ID')
        today = datetime.date.today()
        first_day = today.replace(day=1)
        last_day = (first_day + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
        # Clear current month attendance and leave
        Attendance.objects.filter(date__gte=first_day, date__lte=last_day).delete()
        Leave.objects.filter(start_date__lte=last_day, end_date__gte=first_day).delete()
        employees = Employee.objects.all()
        attendance_count = 0
        leave_count = 0
        for emp in employees:
            # 60% chance of 0 leave, 30% chance of 1, 7% chance of 2, 3% chance of 3
            leave_days_count = random.choices([0, 1, 2, 3], weights=[60, 30, 7, 3])[0]
            leave_days = set(random.sample(range(1, last_day.day+1), k=leave_days_count)) if leave_days_count > 0 else set()
            for day in range(1, last_day.day+1):
                date = today.replace(day=day)
                if day in leave_days:
                    # Create a leave record (single day leave)
                    Leave.objects.create(
                        employee=emp,
                        start_date=date,
                        end_date=date,
                        leave_type=random.choice(['paid', 'unpaid'])
                    )
                    leave_count += 1
                elif date.weekday() < 5:  # Weekdays only
                    # Create attendance record
                    check_in = datetime.time(hour=random.randint(7, 9), minute=random.choice([0, 15, 30, 45]))
                    check_out = datetime.time(hour=random.randint(16, 18), minute=random.choice([0, 15, 30, 45]))
                    hours_worked = ((datetime.datetime.combine(date, check_out) - datetime.datetime.combine(date, check_in)).seconds) / 3600.0
                    Attendance.objects.create(
                        employee=emp,
                        date=date,
                        check_in=check_in,
                        check_out=check_out,
                        hours_worked=round(hours_worked, 2)
                    )
                    attendance_count += 1
        self.stdout.write(self.style.SUCCESS(
            f"Generated {attendance_count} attendance and {leave_count} leave records for {employees.count()} employees in {today.strftime('%B %Y')}."
        )) 