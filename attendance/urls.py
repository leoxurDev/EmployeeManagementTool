from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('grid/', views.employee_grid, name='student_grid'),
    path('toggle-attendance/', views.toggle_attendance, name='toggle_attendance'),
    path('verify-pin/', views.verify_pin, name='verify_pin'),
    path('manager/', views.manager_dashboard, name='teacher_dashboard'),
    path('manager/login/', views.manager_login, name='teacher_login'),
    path('login/', views.manager_login, name='unified_login'),
    path('manager/register/', views.manager_register, name='teacher_register'),
    path('manager/logout/', views.manager_logout, name='teacher_logout'),
    path('manager/add/', views.add_employee, name='add_student'),
    path('manager/edit/<int:pk>/', views.edit_employee, name='edit_student'),
    path('manager/delete/<int:pk>/', views.delete_employee, name='delete_student'),
    path('manager/export/', views.export_attendance_csv, name='export_student_csv'),
    path('manager/roster/assign/', views.assign_roster_shift, name='assign_roster_shift'),
    path('manager/developer/', views.admin_developer_page, name='admin_developer_page'),
    path('manager/developer/save/', views.save_layout, name='save_layout'),
    path('manager/developer/chat/', views.ai_chat_command, name='ai_chat_command'),

    # Client Support Portal
    path('support/', views.support_home, name='support_home'),
    path('support/ticket/<str:number>/', views.support_ticket_view, name='support_ticket_view'),

    # ServiceNow Engineer Support Portal
    path('support/engineer/login/', views.engineer_login_view, name='engineer_login'),
    path('support/engineer/logout/', views.engineer_logout_view, name='engineer_logout'),
    path('support/engineer/', views.engineer_dashboard, name='engineer_dashboard'),
    path('support/engineer/ticket/<str:number>/', views.engineer_ticket_detail, name='engineer_ticket_detail'),
    path('support/engineer/identity/', views.identity_manager, name='identity_manager'),

    # Engineer CRUD
    path('support/engineer/list/', views.engineer_list, name='engineer_list'),
    path('support/engineer/create/', views.engineer_create, name='engineer_create'),
    path('support/engineer/edit/<int:pk>/', views.engineer_edit, name='engineer_edit'),
    path('support/engineer/delete/<int:pk>/', views.engineer_delete, name='engineer_delete'),

    # Group CRUD
    path('support/group/list/', views.group_list, name='group_list'),
    path('support/group/create/', views.group_create, name='group_create'),
    path('support/group/edit/<int:pk>/', views.group_edit, name='group_edit'),
    path('support/group/delete/<int:pk>/', views.group_delete, name='group_delete'),

    # Leoxur Mails & Chat Communication Suite
    path('leoxur-comm/', views.leoxur_comm_dashboard, name='leoxur_comm_dashboard'),
    path('leoxur-comm/auth/', views.leoxur_comm_auth, name='leoxur_comm_auth'),
    path('leoxur-comm/logout/', views.leoxur_comm_logout, name='leoxur_comm_logout'),
    path('leoxur-comm/data/', views.leoxur_comm_data, name='leoxur_comm_data'),
    path('leoxur-comm/send-email/', views.leoxur_send_email, name='leoxur_send_email'),
    path('leoxur-comm/send-chat/', views.leoxur_send_chat, name='leoxur_send_chat'),
    path('leoxur-comm/read-email/', views.leoxur_read_email, name='leoxur_read_email'),
    path('leoxur-comm/create-task/', views.leoxur_create_task, name='leoxur_create_task'),
    path('leoxur-comm/update-task/', views.leoxur_update_task, name='leoxur_update_task'),
    path('leoxur-comm/delete-task/', views.leoxur_delete_task, name='leoxur_delete_task'),
    path('leoxur-comm/add-task-comment/', views.leoxur_create_task_comment, name='leoxur_create_task_comment'),
]
