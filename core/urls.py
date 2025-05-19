from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.employee_add, name='employee_add'),
    path('employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('work-calendar/', views.work_calendar, name='work_calendar'),
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/add/', views.attendance_add, name='attendance_add'),
    path('attendance/<int:pk>/edit/', views.attendance_edit, name='attendance_edit'),
    path('attendance/<int:pk>/delete/', views.attendance_delete, name='attendance_delete'),
    path('leave/', views.leave_list, name='leave_list'),
    path('leave/add/', views.leave_add, name='leave_add'),
    path('leave/<int:pk>/edit/', views.leave_edit, name='leave_edit'),
    path('leave/<int:pk>/delete/', views.leave_delete, name='leave_delete'),
] 