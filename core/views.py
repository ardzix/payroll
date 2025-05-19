from django.shortcuts import render, get_object_or_404, redirect
from .models import PayrollRun, Employee, Attendance, Leave
from .forms import EmployeeForm, AttendanceForm, LeaveForm
from django.urls import reverse
from django.db.models import Q
from django.contrib import messages
import calendar
import datetime
from django.core.paginator import Paginator

def index(request):
    payroll_runs = PayrollRun.objects.order_by('-period_start')
    return render(request, 'core/index.html', {'payroll_runs': payroll_runs})

def employee_list(request):
    employees = Employee.objects.all()
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    sort = request.GET.get('sort', '')
    if q:
        employees = employees.filter(Q(full_name__icontains=q) | Q(nik__icontains=q))
    if status:
        employees = employees.filter(status=status)
    if sort in ['full_name', 'status', 'base_salary']:
        employees = employees.order_by(sort)
    return render(request, 'core/employee_list.html', {'employees': employees})

def employee_add(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee added successfully.')
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'core/employee_form.html', {'form': form, 'form_title': 'Add Employee'})

def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee updated successfully.')
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'core/employee_form.html', {'form': form, 'form_title': 'Edit Employee'})

def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Employee deleted successfully.')
        return redirect('employee_list')
    return render(request, 'core/employee_confirm_delete.html', {'employee': employee})

def work_calendar(request):
    today = datetime.date.today()
    cal = calendar.Calendar(firstweekday=6)  # Sunday start
    month_days = cal.monthdatescalendar(today.year, today.month)
    employee_id = request.GET.get('employee', '')
    employees = Employee.objects.all()
    # Filter attendance and leave by employee if selected
    attendance_qs = Attendance.objects.select_related('employee').filter(date__month=today.month, date__year=today.year)
    leave_qs = Leave.objects.select_related('employee').filter(
        start_date__lte=datetime.date(today.year, today.month, 31),
        end_date__gte=datetime.date(today.year, today.month, 1)
    )
    if employee_id:
        attendance_qs = attendance_qs.filter(employee_id=employee_id)
        leave_qs = leave_qs.filter(employee_id=employee_id)
    # Build a dict for quick lookup
    attendance_map = {}
    for att in attendance_qs:
        attendance_map.setdefault(att.date, []).append(att)
    leave_map = {}
    for lv in leave_qs:
        d = lv.start_date
        while d <= lv.end_date:
            leave_map.setdefault(d, []).append(lv)
            d += datetime.timedelta(days=1)
    calendar_weeks = []
    for week in month_days:
        week_days = []
        for d in week:
            week_days.append({
                'day': d.day if d.month == today.month else '',
                'is_today': d == today,
                'is_weekend': d.weekday() >= 5,
                'is_holiday': False,  # Placeholder for future holiday logic
                'attendances': attendance_map.get(d, []),
                'leaves': leave_map.get(d, []),
                'date': d,
            })
        calendar_weeks.append(week_days)
    return render(request, 'core/work_calendar.html', {
        'calendar_weeks': calendar_weeks,
        'employees': employees,
        'selected_employee': employee_id,
        'request': request,
    })

def attendance_list(request):
    attendances = Attendance.objects.select_related('employee').all()
    employee_id = request.GET.get('employee', '')
    date = request.GET.get('date', '')
    if employee_id:
        attendances = attendances.filter(employee_id=employee_id)
    if date:
        attendances = attendances.filter(date=date)
    attendances = attendances.order_by('-date')
    employees = Employee.objects.all()
    paginator = Paginator(attendances, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'core/attendance_list.html', {'attendances': page_obj, 'employees': employees, 'request': request})

def attendance_add(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Attendance added successfully.')
            return redirect('attendance_list')
        print(form.errors)
    else:
        form = AttendanceForm()
    return render(request, 'core/attendance_form.html', {'form': form, 'form_title': 'Add Attendance'})

def attendance_edit(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)
    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Attendance updated successfully.')
            return redirect('attendance_list')
    else:
        form = AttendanceForm(instance=attendance)
    return render(request, 'core/attendance_form.html', {'form': form, 'form_title': 'Edit Attendance'})

def attendance_delete(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)
    if request.method == 'POST':
        attendance.delete()
        messages.success(request, 'Attendance deleted successfully.')
        return redirect('attendance_list')
    return render(request, 'core/attendance_confirm_delete.html', {'attendance': attendance})

def leave_list(request):
    leaves = Leave.objects.select_related('employee').all()
    employee_id = request.GET.get('employee', '')
    date = request.GET.get('date', '')
    leave_type = request.GET.get('leave_type', '')
    if employee_id:
        leaves = leaves.filter(employee_id=employee_id)
    if date:
        leaves = leaves.filter(start_date__lte=date, end_date__gte=date)
    if leave_type:
        leaves = leaves.filter(leave_type=leave_type)
    leaves = leaves.order_by('-start_date')
    employees = Employee.objects.all()
    paginator = Paginator(leaves, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'core/leave_list.html', {'leaves': page_obj, 'employees': employees, 'request': request})

def leave_add(request):
    if request.method == 'POST':
        form = LeaveForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Leave added successfully.')
            return redirect('leave_list')
    else:
        form = LeaveForm()
    return render(request, 'core/leave_form.html', {'form': form, 'form_title': 'Add Leave'})

def leave_edit(request, pk):
    leave = get_object_or_404(Leave, pk=pk)
    if request.method == 'POST':
        form = LeaveForm(request.POST, instance=leave)
        if form.is_valid():
            form.save()
            messages.success(request, 'Leave updated successfully.')
            return redirect('leave_list')
    else:
        form = LeaveForm(instance=leave)
    return render(request, 'core/leave_form.html', {'form': form, 'form_title': 'Edit Leave'})

def leave_delete(request, pk):
    leave = get_object_or_404(Leave, pk=pk)
    if request.method == 'POST':
        leave.delete()
        messages.success(request, 'Leave deleted successfully.')
        return redirect('leave_list')
    return render(request, 'core/leave_confirm_delete.html', {'leave': leave})
