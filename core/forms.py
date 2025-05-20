from django import forms
from .models import Employee, Attendance, Leave, PayrollItem, EmployeeBenefit
from django.forms import DateInput, TimeInput
import datetime

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = '__all__'
        widgets = {
            'employee': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-700'}),
            'date': DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 border rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-700'}),
            'check_in': TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-700'}),
            'check_out': TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-700'}),
            'hours_worked': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-700', 'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hours_worked'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        if check_in and check_out:
            delta = (datetime.datetime.combine(datetime.date.today(), check_out) -
                     datetime.datetime.combine(datetime.date.today(), check_in))
            hours = delta.total_seconds() / 3600.0
            if hours < 0:
                hours += 24  # handle overnight
            cleaned_data['hours_worked'] = round(hours, 2)
        return cleaned_data

class LeaveForm(forms.ModelForm):
    class Meta:
        model = Leave
        fields = '__all__'
        widgets = {
            'employee': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-700'}),
            'start_date': DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 border rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-700'}),
            'end_date': DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 border rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-700'}),
            'leave_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-700'}),
        }

class PayrollItemForm(forms.ModelForm):
    class Meta:
        model = PayrollItem
        exclude = [
            'bpjs_kesehatan_employee',
            'bpjs_kesehatan_employer',
            'bpjs_ketenagakerjaan_employee',
            'bpjs_ketenagakerjaan_employer',
            'total_deductions',
            'net_salary',
        ]
        widgets = {
            'gross_salary': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-700'}),
            'tax_deduction': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-700'}),
            'other_deductions': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-700'}),
            'notes': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-700'}),
        }

class EmployeeBenefitForm(forms.ModelForm):
    class Meta:
        model = EmployeeBenefit
        fields = '__all__'
        widgets = {
            'employee': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-700'}),
            'benefit_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-700'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-700'}),
        } 