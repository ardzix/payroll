from django.core.management.base import BaseCommand
from core.models import Employee
from faker import Faker
import random

class Command(BaseCommand):
    help = 'Generate 30 random demo employees.'

    def handle(self, *args, **kwargs):
        fake = Faker('id_ID')
        created = 0
        statuses = ['staff', 'contract', 'outsourced']
        pay_periods = ['monthly', 'biweekly', 'weekly']
        work_types = ['9-5', 'shift']
        ptkp_statuses = ['TK0', 'K0', 'K1', 'K2', 'K3']
        for _ in range(30):
            full_name = fake.name()
            nik = fake.unique.random_number(digits=16, fix_len=True)
            npwp = fake.unique.random_number(digits=15, fix_len=True)
            status = random.choice(statuses)
            pay_period = random.choice(pay_periods)
            work_type = random.choice(work_types)
            bank_name = random.choice(['BCA', 'Mandiri', 'BRI', 'BNI', 'CIMB'])
            bank_account_number = fake.unique.random_number(digits=10, fix_len=True)
            account_holder_name = full_name
            base_salary = random.randint(4000000, 15000000)
            ptkp_status = random.choice(ptkp_statuses)
            if not Employee.objects.filter(nik=nik).exists():
                Employee.objects.create(
                    full_name=full_name,
                    nik=nik,
                    npwp=npwp,
                    status=status,
                    pay_period=pay_period,
                    work_type=work_type,
                    bank_name=bank_name,
                    bank_account_number=bank_account_number,
                    account_holder_name=account_holder_name,
                    base_salary=base_salary,
                    ptkp_status=ptkp_status,
                )
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Generated {created} demo employees.')) 