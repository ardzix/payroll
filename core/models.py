from django.db import models

# Create your models here.

class Employee(models.Model):
    STATUS_CHOICES = [
        ('staff', 'Staff'),
        ('contract', 'Contract'),
        ('outsourced', 'Outsourced'),
    ]
    PAY_PERIOD_CHOICES = [
        ('monthly', 'Monthly'),
        ('biweekly', 'Biweekly'),
        ('weekly', 'Weekly'),
    ]
    WORK_TYPE_CHOICES = [
        ('9-5', '9-5'),
        ('shift', 'Shift'),
    ]
    PTKP_CHOICES = [
        ('TK0', 'TK0'),
        ('K0', 'K0'),
        ('K1', 'K1'),
        ('K2', 'K2'),
        ('K3', 'K3'),
    ]
    full_name = models.CharField(max_length=128)
    nik = models.CharField(max_length=32)
    npwp = models.CharField(max_length=32)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    pay_period = models.CharField(max_length=16, choices=PAY_PERIOD_CHOICES)
    work_type = models.CharField(max_length=16, choices=WORK_TYPE_CHOICES)
    bank_name = models.CharField(max_length=64)
    bank_account_number = models.CharField(max_length=64)
    account_holder_name = models.CharField(max_length=128)
    base_salary = models.IntegerField()
    ptkp_status = models.CharField(max_length=4, choices=PTKP_CHOICES)

    def __str__(self):
        return f"{self.full_name} ({self.nik})"

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    hours_worked = models.FloatField()

    def __str__(self):
        return f"{self.employee.full_name} - {self.date}"

class Leave(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    leave_type = models.CharField(max_length=8, choices=LEAVE_TYPE_CHOICES)

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type} ({self.start_date} to {self.end_date})"

class PayrollRun(models.Model):
    period_start = models.DateField()
    period_end = models.DateField()
    run_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Payroll {self.period_start} to {self.period_end}"

class PayrollItem(models.Model):
    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    gross_salary = models.IntegerField()
    tax_deduction = models.IntegerField()
    other_deductions = models.IntegerField()
    bpjs_kesehatan_employee = models.IntegerField(default=0, help_text='BPJS Kesehatan portion paid by employee')
    bpjs_kesehatan_employer = models.IntegerField(default=0, help_text='BPJS Kesehatan portion paid by employer')
    bpjs_ketenagakerjaan_employee = models.IntegerField(default=0, help_text='BPJS Ketenagakerjaan portion paid by employee')
    bpjs_ketenagakerjaan_employer = models.IntegerField(default=0, help_text='BPJS Ketenagakerjaan portion paid by employer')
    bpjs_jp_employee = models.IntegerField(default=0, help_text='BPJS Ketenagakerjaan JP portion paid by employee')
    bpjs_jp_employer = models.IntegerField(default=0, help_text='BPJS Ketenagakerjaan JP portion paid by employer')
    total_deductions = models.IntegerField(default=0, help_text='Sum of all deductions (tax + BPJS + other)')
    net_salary = models.IntegerField()
    notes = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # BPJS Kesehatan calculation (capped at 12,000,000)
        bpjs_kes_cap = 12000000
        base_for_bpjs_kes = min(self.gross_salary, bpjs_kes_cap)
        self.bpjs_kesehatan_employee = int(base_for_bpjs_kes * 0.01)
        self.bpjs_kesehatan_employer = int(base_for_bpjs_kes * 0.04)
        # BPJS Ketenagakerjaan JHT (no cap)
        self.bpjs_ketenagakerjaan_employee = int(self.gross_salary * 0.02)
        self.bpjs_ketenagakerjaan_employer = int(self.gross_salary * 0.037)
        # BPJS Ketenagakerjaan JP (capped at 9,810,000)
        bpjs_jp_cap = 9810000
        base_for_bpjs_jp = min(self.gross_salary, bpjs_jp_cap)
        self.bpjs_jp_employee = int(base_for_bpjs_jp * 0.01)
        self.bpjs_jp_employer = int(base_for_bpjs_jp * 0.02)
        # Calculate annual gross for tax
        annual_gross = self.gross_salary * 12
        # PTKP (2024)
        PTKP = {
            'TK0': 54000000,
            'K0': 58500000,
            'K1': 63000000,
            'K2': 67500000,
            'K3': 72000000,
        }
        ptkp = PTKP.get(getattr(self.employee, 'ptkp_status', 'TK0'), 54000000)
        taxable_income = max(0, annual_gross - ptkp)
        # PPh 21 progressive rates
        tax = 0
        brackets = [60000000, 250000000, 500000000]
        rates = [0.05, 0.15, 0.25, 0.3]
        remaining = taxable_income
        for i, bracket in enumerate(brackets):
            if remaining > bracket:
                tax += bracket * rates[i]
                remaining -= bracket
            else:
                tax += remaining * rates[i]
                remaining = 0
                break
        if remaining > 0:
            tax += remaining * rates[-1]
        self.tax_deduction = int(tax / 12)  # Monthly tax
        # Total deductions (employee side)
        self.total_deductions = (
            self.tax_deduction +
            self.other_deductions +
            self.bpjs_kesehatan_employee +
            self.bpjs_ketenagakerjaan_employee +
            self.bpjs_jp_employee
        )
        # Net salary
        self.net_salary = self.gross_salary - self.total_deductions
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.full_name} - {self.payroll_run}"

BENEFIT_TYPE_CHOICES = [
    ('meal', 'Meal Allowance'),
    ('transport', 'Transport Allowance'),
    ('communication', 'Communication Allowance'),
    ('overtime', 'Overtime Allowance'),
    ('position', 'Position Allowance'),
    ('attendance', 'Attendance Allowance'),
    ('thr', 'Holiday Allowance (THR)'),
    ('bonus', 'Bonus'),
    ('pension', 'Pension Fund'),
    ('housing', 'Housing Allowance'),
    ('child', 'Child Allowance'),
    ('other', 'Other'),
]

class EmployeeBenefit(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    benefit_type = models.CharField(max_length=32, choices=BENEFIT_TYPE_CHOICES)
    amount = models.IntegerField()

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_benefit_type_display()} ({self.amount})"

DEDUCTION_TYPE_CHOICES = [
    ('loan', 'Loan Repayment'),
    ('union', 'Union Fee'),
    ('other', 'Other'),
]

class EmployeeDeduction(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    deduction_type = models.CharField(max_length=32, choices=DEDUCTION_TYPE_CHOICES)
    amount = models.IntegerField()

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_deduction_type_display()} ({self.amount})"
