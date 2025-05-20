from django.shortcuts import render, get_object_or_404, redirect
from .models import PayrollRun, Employee, Attendance, Leave, PayrollItem, EmployeeBenefit, EmployeeDeduction
from .forms import EmployeeForm, AttendanceForm, LeaveForm, PayrollItemForm, EmployeeBenefitForm
from django.urls import reverse
from django.db.models import Q
from django.contrib import messages
import calendar
import datetime
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponse
from django.template.loader import render_to_string
import io
import zipfile
import csv
from django import forms
try:
    from weasyprint import HTML
except ImportError:
    HTML = None

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
    paginator = Paginator(employees, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'core/employee_list.html', {'page_obj': page_obj, 'request': request})

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

def compensation_list(request):
    items = PayrollItem.objects.select_related('employee', 'payroll_run').all()
    employee_id = request.GET.get('employee', '')
    payroll_run_id = request.GET.get('payroll_run', '')
    if employee_id:
        items = items.filter(employee_id=employee_id)
    if payroll_run_id:
        items = items.filter(payroll_run_id=payroll_run_id)
    items = items.order_by('-payroll_run__period_start', 'employee__full_name')
    employees = Employee.objects.all()
    payroll_runs = PayrollRun.objects.all().order_by('-period_start')
    paginator = Paginator(items, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'core/compensation_list.html', {
        'items': page_obj,
        'employees': employees,
        'payroll_runs': payroll_runs,
        'request': request,
    })

def compensation_add(request):
    if request.method == 'POST':
        form = PayrollItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Compensation & Benefit added successfully.')
            return redirect('compensation_list')
    else:
        form = PayrollItemForm()
    return render(request, 'core/compensation_form.html', {'form': form, 'form_title': 'Add Compensation & Benefit'})

def compensation_edit(request, pk):
    item = get_object_or_404(PayrollItem, pk=pk)
    if request.method == 'POST':
        form = PayrollItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Compensation & Benefit updated successfully.')
            return redirect('compensation_list')
    else:
        form = PayrollItemForm(instance=item)
    return render(request, 'core/compensation_form.html', {'form': form, 'form_title': 'Edit Compensation & Benefit'})

def compensation_delete(request, pk):
    item = get_object_or_404(PayrollItem, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Compensation & Benefit deleted successfully.')
        return redirect('compensation_list')
    return render(request, 'core/compensation_confirm_delete.html', {'item': item})

def employee_benefit_list(request):
    benefits = EmployeeBenefit.objects.select_related('employee').all()
    employee_id = request.GET.get('employee', '')
    if employee_id:
        benefits = benefits.filter(employee_id=employee_id)
    employees = Employee.objects.all()
    paginator = Paginator(benefits, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'core/employee_benefit_list.html', {
        'benefits': page_obj,
        'employees': employees,
        'request': request,
    })

def employee_benefit_add(request):
    if request.method == 'POST':
        form = EmployeeBenefitForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Benefit added to employee successfully.')
            return redirect('employee_benefit_list')
    else:
        form = EmployeeBenefitForm()
    return render(request, 'core/employee_benefit_form.html', {'form': form, 'form_title': 'Add Employee Benefit'})

def employee_benefit_edit(request, pk):
    benefit = get_object_or_404(EmployeeBenefit, pk=pk)
    if request.method == 'POST':
        form = EmployeeBenefitForm(request.POST, instance=benefit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee benefit updated successfully.')
            return redirect('employee_benefit_list')
    else:
        form = EmployeeBenefitForm(instance=benefit)
    return render(request, 'core/employee_benefit_form.html', {'form': form, 'form_title': 'Edit Employee Benefit'})

def employee_benefit_delete(request, pk):
    benefit = get_object_or_404(EmployeeBenefit, pk=pk)
    if request.method == 'POST':
        benefit.delete()
        messages.success(request, 'Employee benefit deleted successfully.')
        return redirect('employee_benefit_list')
    return render(request, 'core/employee_benefit_confirm_delete.html', {'benefit': benefit})

def payroll_run_list(request):
    runs = PayrollRun.objects.all().order_by('-period_start')
    period_start = request.GET.get('period_start', '')
    period_end = request.GET.get('period_end', '')
    if period_start:
        runs = runs.filter(period_start__gte=period_start)
    if period_end:
        runs = runs.filter(period_end__lte=period_end)
    paginator = Paginator(runs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'core/payroll_run_list.html', {
        'runs': page_obj,
        'request': request,
    })

def payroll_run_add(request):
    if request.method == 'POST':
        period_start = request.POST.get('period_start')
        period_end = request.POST.get('period_end')
        notes = request.POST.get('notes')
        if period_start and period_end:
            PayrollRun.objects.create(period_start=period_start, period_end=period_end, notes=notes)
            messages.success(request, 'Payroll run added successfully.')
            return redirect('payroll_run_list')
        else:
            messages.error(request, 'Please provide both period start and end.')
    return render(request, 'core/payroll_run_form.html', {'form_title': 'Add Payroll Run'})

def payroll_run_edit(request, pk):
    run = get_object_or_404(PayrollRun, pk=pk)
    if request.method == 'POST':
        period_start = request.POST.get('period_start')
        period_end = request.POST.get('period_end')
        notes = request.POST.get('notes')
        if period_start and period_end:
            run.period_start = period_start
            run.period_end = period_end
            run.notes = notes
            run.save()
            messages.success(request, 'Payroll run updated successfully.')
            return redirect('payroll_run_list')
        else:
            messages.error(request, 'Please provide both period start and end.')
    return render(request, 'core/payroll_run_form.html', {'form_title': 'Edit Payroll Run', 'run': run})

def payroll_run_delete(request, pk):
    run = get_object_or_404(PayrollRun, pk=pk)
    if request.method == 'POST':
        run.delete()
        messages.success(request, 'Payroll run deleted successfully.')
        return redirect('payroll_run_list')
    return render(request, 'core/payroll_run_confirm_delete.html', {'run': run})

def payroll_run_detail(request, pk):
    run = get_object_or_404(PayrollRun, pk=pk)
    employees = Employee.objects.all()
    employee_data = []
    for emp in employees:
        benefits = EmployeeBenefit.objects.filter(employee=emp)
        total_benefits = sum(b.amount for b in benefits)
        deductions = EmployeeDeduction.objects.filter(employee=emp)
        total_custom_deductions = sum(d.amount for d in deductions)
        gross_salary = emp.base_salary + total_benefits
        payroll_item = PayrollItem.objects.filter(payroll_run=run, employee=emp).first()
        employee_data.append({
            'employee': emp,
            'base_salary': emp.base_salary,
            'benefits': benefits,
            'total_benefits': total_benefits,
            'gross_salary': gross_salary,
            'payroll_item': payroll_item,
            'custom_deductions': deductions,
            'total_custom_deductions': total_custom_deductions,
        })
    return render(request, 'core/payroll_run_detail.html', {
        'run': run,
        'employee_data': employee_data,
    })

def generate_payroll_items(request, run_id):
    run = get_object_or_404(PayrollRun, pk=run_id)
    employees = Employee.objects.all()
    created_count = 0
    for emp in employees:
        if not PayrollItem.objects.filter(payroll_run=run, employee=emp).exists():
            benefits = EmployeeBenefit.objects.filter(employee=emp)
            total_benefits = sum(b.amount for b in benefits)
            deductions = EmployeeDeduction.objects.filter(employee=emp)
            total_custom_deductions = sum(d.amount for d in deductions)
            gross_salary = emp.base_salary + total_benefits
            PayrollItem.objects.create(
                payroll_run=run,
                employee=emp,
                gross_salary=gross_salary,
                tax_deduction=0,  # You can implement tax logic later
                other_deductions=total_custom_deductions,
                notes='',
            )
            created_count += 1
    messages.success(request, f'Generated payroll items for {created_count} employees.')
    return HttpResponseRedirect(reverse('payroll_run_detail', args=[run_id]))

def payslip_view(request, pk):
    item = get_object_or_404(PayrollItem, pk=pk)
    return render(request, 'core/payslip.html', {'item': item})

def export_payslips_zip(request, run_id):
    run = get_object_or_404(PayrollRun, pk=run_id)
    items = PayrollItem.objects.filter(payroll_run=run).select_related('employee')
    if not HTML:
        messages.error(request, 'WeasyPrint is not installed. PDF export is unavailable.')
        return redirect('payroll_run_detail', pk=run_id)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for item in items:
            html_string = render_to_string('core/payslip.html', {'item': item, 'request': request})
            pdf_bytes = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
            filename = f"{item.employee.full_name.replace(' ', '_')}_payslip.pdf"
            zip_file.writestr(filename, pdf_bytes)
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="payslips_{run.period_start}_{run.period_end}.zip"'
    return response

def export_payroll_csv(request, run_id):
    run = get_object_or_404(PayrollRun, pk=run_id)
    items = PayrollItem.objects.filter(payroll_run=run).select_related('employee')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="payroll_{run.period_start}_{run.period_end}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Employee Name', 'NIK', 'Bank Name', 'Bank Account Number', 'Net Salary'])
    for item in items:
        writer.writerow([
            item.employee.full_name,
            item.employee.nik,
            item.employee.bank_name,
            item.employee.bank_account_number,
            int(item.net_salary),
        ])
    return response

class PayrollRunSelectForm(forms.Form):
    payroll_run = forms.ModelChoiceField(queryset=PayrollRun.objects.all().order_by('-period_start'), required=True, label='Payroll Run')

def get_ptkp(ptkp_status):
    PTKP = {
        'TK0': 54000000,
        'K0': 58500000,
        'K1': 63000000,
        'K2': 67500000,
        'K3': 72000000,
    }
    return PTKP.get(ptkp_status, 54000000)

def tax_bpjs_report(request):
    form = PayrollRunSelectForm(request.GET or None)
    payroll_items = []
    run = None
    if form.is_valid():
        run = form.cleaned_data['payroll_run']
        payroll_items = PayrollItem.objects.filter(payroll_run=run).select_related('employee')
        for item in payroll_items:
            item.taxable_income_year = max(0, item.gross_salary * 12 - get_ptkp(getattr(item.employee, 'ptkp_status', 'TK0')))
    return render(request, 'core/tax_bpjs_report.html', {'form': form, 'payroll_items': payroll_items, 'run': run})
