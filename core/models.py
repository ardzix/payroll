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
    net_salary = models.IntegerField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.payroll_run}"
