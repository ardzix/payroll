from django import forms
from .models import Employee, Attendance, Leave
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
            'date': DateInput(attrs={'type': 'date'}),
            'check_in': TimeInput(attrs={'type': 'time'}),
            'check_out': TimeInput(attrs={'type': 'time'}),
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
            'start_date': DateInput(attrs={'type': 'date'}),
            'end_date': DateInput(attrs={'type': 'date'}),
        } 