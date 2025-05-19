from django.contrib import admin
from .models import Employee, Attendance, Leave, PayrollRun, PayrollItem

admin.site.register(Employee)
admin.site.register(Attendance)
admin.site.register(Leave)
admin.site.register(PayrollRun)
admin.site.register(PayrollItem)
