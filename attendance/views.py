from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
import csv
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from .models import (
    Employee, Roster, Attendance, DepartmentOption, AppLayoutBlock,
    AssignmentGroup, SupportEngineer, SupportTicket, TicketActivity, EmployeeSupportPermission,
    LeoxurEmail, LeoxurMessage, LeoxurTask, LeoxurTaskComment
)
from .forms import EmployeeForm


def get_or_seed_layout_blocks():
    blocks = AppLayoutBlock.objects.all().order_by('order')
    if not blocks.exists():
        default_blocks = [
            ('header', 'Branding Header', 1),
            ('classroom_tabs', 'Department Selection Tabs', 2),
            ('stats_banner', 'Roster Stats Banner', 3),
            ('student_grid', 'Employee Roster Grid', 4)
        ]
        for bid, name, o in default_blocks:
            AppLayoutBlock.objects.create(block_id=bid, title=name, order=o, is_visible=True)
        blocks = AppLayoutBlock.objects.all().order_by('order')
    return blocks


def get_shift_schedule_status():
    import datetime
    local_now = timezone.localtime()
    current_time = local_now.time()
    
    # Parse times
    morning_start = datetime.time(6, 0)
    afternoon_start = datetime.time(14, 0)
    night_start = datetime.time(22, 0)
    
    # Check current active shift
    if morning_start <= current_time < afternoon_start:
        status = "Morning Shift 🌅"
        message = "Active Shift: 06:00 AM - 02:00 PM. Check-in active."
        badge = "morning"
    elif afternoon_start <= current_time < night_start:
        status = "Afternoon Shift ☀️"
        message = "Active Shift: 02:00 PM - 10:00 PM. Check-in active."
        badge = "afternoon"
    else:
        status = "Night Shift 🌙"
        message = "Active Shift: 10:00 PM - 06:00 AM. Check-in active."
        badge = "night"
        
    milestones = [
        {'time_str': '06:00 AM', 'time': morning_start, 'label': 'Morning Shift 🌅'},
        {'time_str': '02:00 PM', 'time': afternoon_start, 'label': 'Afternoon Shift ☀️'},
        {'time_str': '10:00 PM', 'time': night_start, 'label': 'Night Shift 🌙'},
    ]
    
    active_idx = -1
    if morning_start <= current_time < afternoon_start:
        active_idx = 0
    elif afternoon_start <= current_time < night_start:
        active_idx = 1
    else:
        active_idx = 2
            
    for idx, m in enumerate(milestones):
        if idx < active_idx:
            m['status_class'] = 'completed'
        elif idx == active_idx:
            m['status_class'] = 'active'
        else:
            m['status_class'] = 'upcoming'
            
    return {
        'status': status,
        'message': message,
        'badge': badge,
        'current_time_str': local_now.strftime('%I:%M %p'),
        'milestones': milestones,
    }


def home(request):
    return render(request, 'attendance/home.html')


def employee_grid(request):
    selected_dept_name = request.GET.get('classroom')  # keep query param classroom for url continuity
    
    # Get all active departments
    all_depts = DepartmentOption.objects.filter(is_active=True).order_by('order')
    
    # Default to first department if not provided
    if not selected_dept_name:
        selected_dept = all_depts.first()
        if not selected_dept:
            return render(request, 'attendance/student_grid.html', {'error': 'No active departments found'})
        selected_dept_name = selected_dept.name
        selected_dept_display = selected_dept.display_value
    else:
        try:
            selected_dept = all_depts.get(name=selected_dept_name)
            selected_dept_display = selected_dept.display_value
        except DepartmentOption.DoesNotExist:
            selected_dept = all_depts.first()
            if not selected_dept:
                return render(request, 'attendance/student_grid.html', {'error': 'No active departments found'})
            selected_dept_name = selected_dept.name
            selected_dept_display = selected_dept.display_value
        
    employees = Employee.objects.filter(department=selected_dept_name, is_active=True).order_by('first_name')
    today = timezone.localdate()
    
    # Prefetch today's attendance and rosters
    today_attendances = {
        att.employee_id: att 
        for att in Attendance.objects.filter(date=today, employee__department=selected_dept_name)
    }
    today_rosters = {
        rost.employee_id: rost 
        for rost in Roster.objects.filter(date=today, employee__department=selected_dept_name)
    }
    
    # Attach status and roster to employee objects
    for emp in employees:
        emp.today_status = today_attendances.get(emp.id)
        emp.roster_assigned = today_rosters.get(emp.id)

    total_employees = employees.count()
    present_today = sum(1 for e in employees if e.today_status and e.today_status.status in ['present', 'late'])
    attendance_rate = int((present_today / total_employees * 100)) if total_employees > 0 else 0
    
    depts_display = [(d.name, d.display_value) for d in all_depts]
    current_shift = Attendance.get_current_shift_by_time()

    context = {
        'students': employees,  # template compatibility
        'selected_classroom': selected_dept_display,
        'selected_classroom_name': selected_dept_name,
        'classrooms': depts_display,
        'total_students': total_employees,
        'present_today': present_today,
        'attendance_rate': attendance_rate,
        'today': today,
        'current_time_period': current_shift,
        'layout_blocks': get_or_seed_layout_blocks(),
        'schedule_status': get_shift_schedule_status(),
    }
    return render(request, 'attendance/student_grid.html', context)


@require_POST
def toggle_attendance(request):
    employee_id = request.POST.get('student_id') or request.POST.get('employee_id')
    action = request.POST.get('action', 'check_in')  # 'check_in' or 'check_out'
    status = request.POST.get('status', 'present')
    work_mode = request.POST.get('mood', 'office')  # maps mood field to work_mode
    
    try:
        employee = Employee.objects.get(id=employee_id, is_active=True)
    except Employee.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Employee not found'}, status=404)
        
    today = timezone.localdate()
    attendance = Attendance.objects.filter(employee=employee, date=today).first()
    
    if action == 'check_in':
        if attendance:
            # Already checked in, check if we need to update work mode
            attendance.work_mode = work_mode
            attendance.save()
        else:
            # Determine roster shift or current time shift
            roster = employee.today_roster()
            shift = roster.shift if roster else Attendance.get_current_shift_by_time()
            
            # Check if late based on shift
            import datetime
            local_now = timezone.localtime()
            current_time = local_now.time()
            is_late = False
            
            if shift == 'morning' and current_time > datetime.time(6, 15):
                is_late = True
            elif shift == 'afternoon' and current_time > datetime.time(14, 15):
                is_late = True
            elif shift == 'night' and current_time > datetime.time(22, 15):
                is_late = True
                
            status = 'late' if is_late else 'present'
            
            attendance = Attendance.objects.create(
                employee=employee,
                date=today,
                shift=shift,
                status=status,
                work_mode=work_mode,
                checked_in_at=timezone.now()
            )
            
        time_str = timezone.localtime(attendance.checked_in_at).strftime('%I:%M %p')
        return JsonResponse({
            'success': True,
            'status': attendance.status,
            'mood': attendance.work_mode,  # compatibility
            'mood_emoji': attendance.get_work_mode_display().split()[-1] if attendance.work_mode else '',
            'time': time_str,
            'action': 'created',
            'student_id': employee_id
        })
        
    elif action == 'check_out':
        if not attendance:
            return JsonResponse({'success': False, 'error': 'Cannot check out without checking in first.'}, status=400)
            
        attendance.checked_out_at = timezone.now()
        attendance.save()
        
        time_str = timezone.localtime(attendance.checked_out_at).strftime('%I:%M %p')
        return JsonResponse({
            'success': True,
            'status': 'absent',  # triggers card reset/update in frontend logic (we will map it properly)
            'mood': '',
            'mood_emoji': '',
            'time': time_str,
            'hours_worked': attendance.hours_worked,
            'action': 'removed',  # maps to action in JS
            'student_id': employee_id
        })
        
    return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)


@require_POST
def verify_pin(request):
    employee_id = request.POST.get('student_id') or request.POST.get('employee_id')
    pin_code = request.POST.get('pin_code')
    try:
        employee = Employee.objects.get(id=employee_id, is_active=True)
        if employee.pin_code == pin_code:
            att = employee.today_attendance()
            roster = employee.today_roster()
            
            state = 'not_checked_in'
            check_in_time = '-'
            check_out_time = '-'
            hours_worked = 0.0
            
            if att:
                if att.checked_out_at:
                    state = 'checked_out'
                    check_out_time = timezone.localtime(att.checked_out_at).strftime('%I:%M %p')
                else:
                    state = 'checked_in'
                check_in_time = timezone.localtime(att.checked_in_at).strftime('%I:%M %p')
                hours_worked = att.hours_worked
                
            rostered_shift = roster.get_shift_display() if roster else 'Not Rostered (Default Shift)'
            rostered_shift_key = roster.shift if roster else 'none'
            
            return JsonResponse({
                'success': True,
                'state': state,
                'check_in_time': check_in_time,
                'check_out_time': check_out_time,
                'hours_worked': hours_worked,
                'rostered_shift': rostered_shift,
                'rostered_shift_key': rostered_shift_key,
                'work_mode': att.work_mode if att else 'office'
            })
        else:
            return JsonResponse({'success': False, 'error': 'Invalid PIN. Please try again! 🤫'})
    except Employee.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Employee not found.'}, status=404)


def manager_login(request):
    if request.user.is_authenticated:
        return redirect('teacher_dashboard')
        
    employees = Employee.objects.filter(is_active=True).order_by('department', 'first_name')
    depts = DepartmentOption.objects.filter(is_active=True).order_by('order')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f"Welcome back, Manager {user.username}! 💼")
            return redirect('teacher_dashboard')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()
        
    context = {
        'form': form,
        'action': 'login',
        'students': employees,
        'classrooms': depts,
        'schedule_status': get_shift_schedule_status(),
    }
    return render(request, 'attendance/login.html', context)


def manager_register(request):
    if not request.user.is_authenticated or (not request.user.is_staff and not request.user.is_superuser):
        messages.error(request, "Access denied. Only administrators can register new manager accounts. 🔐")
        return redirect('teacher_login')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Manager account '{user.username}' created successfully! 💼")
            return redirect('teacher_dashboard')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = UserCreationForm()
    return render(request, 'attendance/login.html', {'form': form, 'action': 'register'})


def manager_logout(request):
    auth_logout(request)
    messages.info(request, "You have been logged out. See you soon! 👋")
    return redirect('student_grid')


@login_required(login_url='teacher_login')
def manager_dashboard(request):
    today = timezone.localdate()
    dept_filter = request.GET.get('classroom', 'All')
    
    # Parse roster date from query parameters (defaults to today)
    roster_date_str = request.GET.get('roster_date')
    if roster_date_str:
        try:
            roster_date = timezone.datetime.strptime(roster_date_str, '%Y-%m-%d').date()
        except ValueError:
            roster_date = today
    else:
        roster_date = today
        
    # Calculate metrics (real-time stats are always for today)
    employees_query = Employee.objects.filter(is_active=True)
    attendance_query = Attendance.objects.filter(date=today)
    
    # Fetch roster assignments for the selected roster date
    rosters_query = Roster.objects.filter(date=roster_date)
    
    if dept_filter != 'All':
        employees_query = employees_query.filter(department=dept_filter)
        attendance_query = attendance_query.filter(employee__department=dept_filter)
        rosters_query = rosters_query.filter(employee__department=dept_filter)
        
    employees = employees_query.order_by('department', 'first_name')
    total_employees = employees.count()
    
    # Map attendance and roster details for easy lookup
    attendance_map = {att.employee_id: att for att in attendance_query}
    roster_map = {rost.employee_id: rost for rost in rosters_query}
    
    present_count = 0
    late_count = 0
    absent_count = 0
    
    for emp in employees:
        att = attendance_map.get(emp.id)
        rost = roster_map.get(emp.id)
        emp.today_status = att
        emp.today_roster = rost  # holds roster for the selected date
        if att:
            if att.status == 'present':
                present_count += 1
            elif att.status == 'late':
                late_count += 1
            else:
                absent_count += 1
        else:
            absent_count += 1

    attendance_percentage = int(((present_count + late_count) / total_employees * 100)) if total_employees > 0 else 0

    active_depts = DepartmentOption.objects.filter(is_active=True).order_by('order')
    depts = [('All', 'All Departments 🏢')] + [(d.name, d.display_value) for d in active_depts]

    # Check support permissions
    can_raise_support = False
    tickets_list = []
    if request.user.is_authenticated:
        can_raise_support = request.user.is_superuser
        if not can_raise_support:
            perm, created = EmployeeSupportPermission.objects.get_or_create(user=request.user)
            can_raise_tickets = perm.can_raise_tickets if perm else False
            can_raise_support = can_raise_tickets
            
        if can_raise_support:
            tickets_list = SupportTicket.objects.all().order_by('-created_at')

    context = {
        'students': employees,
        'today': today,
        'roster_date': roster_date,
        'roster_date_str': roster_date.strftime('%Y-%m-%d'),
        'total_students': total_employees,
        'present_count': present_count,
        'late_count': late_count,
        'absent_count': absent_count,
        'attendance_percentage': attendance_percentage,
        'classrooms': depts,
        'selected_classroom': dept_filter,
        'schedule_status': get_shift_schedule_status(),
        'current_time_period': Attendance.get_current_shift_by_time(),
        'can_raise_support': can_raise_support,
        'tickets_list': tickets_list,
    }
    return render(request, 'attendance/teacher_dashboard.html', context)


@login_required(login_url='teacher_login')
def add_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f"Welcome to the company, {employee.full_name}! 🎉")
            return redirect('teacher_dashboard')
    else:
        form = EmployeeForm()
        
    return render(request, 'attendance/student_form.html', {'form': form, 'title': 'Add New Employee 👔'})


@login_required(login_url='teacher_login')
def edit_employee(request, pk):
    employee = get_object_or_404(Employee, id=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated details for {employee.full_name}! 📝")
            return redirect('teacher_dashboard')
    else:
        form = EmployeeForm(instance=employee)
        
    return render(request, 'attendance/student_form.html', {'form': form, 'title': f'Edit Details for {employee.first_name} ✏️'})


@login_required(login_url='teacher_login')
def delete_employee(request, pk):
    employee = get_object_or_404(Employee, id=pk)
    if request.method == 'POST':
        employee.is_active = False  # Soft delete
        employee.save()
        messages.warning(request, f"Goodbye {employee.full_name}! 👋")
        return redirect('teacher_dashboard')
    return render(request, 'attendance/student_confirm_delete.html', {'student': employee})


@login_required(login_url='teacher_login')
def export_attendance_csv(request):
    dept_filter = request.GET.get('classroom', 'All')
    
    employees = Employee.objects.filter(is_active=True)
    if dept_filter != 'All':
        employees = employees.filter(department=dept_filter)
        
    employees = employees.order_by('department', 'first_name')
    today = timezone.localdate()
    
    today_attendances = {
        att.employee_id: att 
        for att in Attendance.objects.filter(date=today)
    }
    today_rosters = {
        rost.employee_id: rost 
        for rost in Roster.objects.filter(date=today)
    }
    
    response = HttpResponse(content_type='text/csv')
    filename = f"employee_attendance_{dept_filter}_{today}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Employee ID', 'First Name', 'Last Name', 'Department', 
        'Rostered Shift', 'Work Status', 'Work Mode', 'Check-in Time', 'Check-out Time', 'Hours Worked'
    ])
    
    for emp in employees:
        att = today_attendances.get(emp.id)
        rost = today_rosters.get(emp.id)
        
        rostered_shift = rost.get_shift_display() if rost else '-'
        status = att.get_status_display() if att else 'Absent ❌'
        work_mode = att.get_work_mode_display() if att else '-'
        
        checkin_time = timezone.localtime(att.checked_in_at).strftime('%I:%M %p') if (att and att.checked_in_at) else '-'
        checkout_time = timezone.localtime(att.checked_out_at).strftime('%I:%M %p') if (att and att.checked_out_at) else '-'
        hours_worked = att.hours_worked if att else 0.0
            
        writer.writerow([
            emp.id, emp.first_name, emp.last_name, emp.department,
            rostered_shift, status, work_mode, checkin_time, checkout_time, hours_worked
        ])
        
    return response


@login_required(login_url='teacher_login')
def assign_roster_shift(request):
    date_str = request.POST.get('date')
    classroom = request.POST.get('classroom')
    
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        shift = request.POST.get('shift')
        
        try:
            date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.localdate()
            employee = Employee.objects.get(id=employee_id, is_active=True)
            
            if shift == 'none':
                Roster.objects.filter(employee=employee, date=date).delete()
                messages.success(request, f"Removed shift assignment for {employee.full_name}.")
            else:
                roster, created = Roster.objects.update_or_create(
                    employee=employee,
                    date=date,
                    defaults={'shift': shift}
                )
                messages.success(request, f"Assigned {employee.full_name} to {roster.get_shift_display()} on {date}.")
        except Exception as e:
            messages.error(request, f"Failed to assign roster shift: {e}")
            
    # Redirect back, preserving date and classroom query parameters
    redirect_url = '/manager/'
    params = []
    if date_str:
        params.append(f"roster_date={date_str}")
    if classroom:
        params.append(f"classroom={classroom}")
    if params:
        redirect_url += '?' + '&'.join(params)
    return redirect(redirect_url)


@login_required(login_url='teacher_login')
@ensure_csrf_cookie
def admin_developer_page(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied. Only administrators can use the customizer page. 🔐")
        return redirect('teacher_dashboard')
        
    # Handle permission toggle POST form
    if request.method == 'POST' and 'toggle_support_user_id' in request.POST:
        user_id = request.POST.get('toggle_support_user_id')
        user_to_toggle = get_object_or_404(User, pk=user_id)
        perm, created = EmployeeSupportPermission.objects.get_or_create(user=user_to_toggle)
        perm.can_raise_tickets = not perm.can_raise_tickets
        perm.save()
        messages.success(request, f"Updated support ticket permissions for {user_to_toggle.username} to: {perm.can_raise_tickets}")
        return redirect('admin_developer_page')

    layout_blocks = get_or_seed_layout_blocks()
    
    # Get all users to manage permissions
    all_users = User.objects.all().order_by('username')
    teachers_permissions = []
    for user in all_users:
        perm, created = EmployeeSupportPermission.objects.get_or_create(user=user)
        display_allowed = True if user.is_superuser else perm.can_raise_tickets
        teachers_permissions.append({
            'user': user,
            'can_raise_tickets': display_allowed,
            'is_superuser': user.is_superuser
        })

    return render(request, 'attendance/developer_page.html', {
        'layout_blocks': layout_blocks,
        'teachers_permissions': teachers_permissions
    })


@login_required(login_url='teacher_login')
@require_POST
def save_layout(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
    import json
    try:
        data = json.loads(request.body)
        blocks_data = data.get('blocks', [])
        for block_item in blocks_data:
            bid = block_item.get('id')
            order = block_item.get('order')
            is_visible = block_item.get('is_visible', True)
            AppLayoutBlock.objects.filter(block_id=bid).update(order=order, is_visible=is_visible)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required(login_url='teacher_login')
@require_POST
def ai_chat_command(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
    import json
    
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip().lower()
        api_key = data.get('api_key', '').strip()
        
        action = None
        target_block = None
        message_response = ""
        
        if api_key:
            system_prompt = (
                "You are an AI assistant for an Employee Attendance app layout customizer. "
                "Available blocks are: 'header', 'classroom_tabs', 'stats_banner', 'student_grid'.\n"
                "Understand the user request and map it to a JSON response of this exact schema:\n"
                "{\n"
                "  \"action\": \"hide\" | \"show\" | \"move_top\" | \"move_bottom\" | \"reset\",\n"
                "  \"block\": \"header\" | \"classroom_tabs\" | \"stats_banner\" | \"student_grid\" | null,\n"
                "  \"reply\": \"A friendly short response to the user explaining what you did in corporate-like professional tone ✨\"\n"
                "}\n"
                "Only reply with the JSON block. Do not write explanation outside the JSON."
            )
            
            try:
                import urllib.request
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                req_headers = {'Content-Type': 'application/json'}
                req_payload = {
                    "contents": [{"parts": [{"text": f"{system_prompt}\nUser request: {user_message}"}]}],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                    }
                }
                
                req = urllib.request.Request(
                    url, 
                    data=json.dumps(req_payload).encode('utf-8'), 
                    headers=req_headers, 
                    method='POST'
                )
                
                with urllib.request.urlopen(req, timeout=8) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    text_out = res_data['candidates'][0]['content']['parts'][0]['text']
                    json_res = json.loads(text_out.strip())
                    
                    action = json_res.get('action')
                    target_block = json_res.get('block')
                    message_response = json_res.get('reply', '')
            except Exception as api_err:
                message_response = f"(Gemini API error, using offline backup) "
        
        if not action:
            if any(k in user_message for k in ['reset', 'default', 'restore']):
                action = 'reset'
                message_response += "Resetting everything back to the default order! 🌟"
            elif any(k in user_message for k in ['hide', 'remove', 'disable', 'delete', 'invisible']):
                action = 'hide'
                if any(x in user_message for x in ['stat', 'banner', 'metric', 'pill']):
                    target_block = 'stats_banner'
                    message_response += "Stats banner has been hidden. ☁️"
                elif any(x in user_message for x in ['classroom', 'tab', 'class', 'picker', 'department', 'dept']):
                    target_block = 'classroom_tabs'
                    message_response += "Department tabs are now hidden."
                elif any(x in user_message for x in ['header', 'logo', 'title', 'brand']):
                    target_block = 'header'
                    message_response += "Header has been hidden."
                elif any(x in user_message for x in ['grid', 'student', 'roster', 'employee', 'card']):
                    target_block = 'student_grid'
                    message_response += "Employee grid has been hidden."
                else:
                    action = None
            elif any(k in user_message for k in ['show', 'display', 'enable', 'visible', 'add', 'reveal']):
                action = 'show'
                if any(x in user_message for x in ['stat', 'banner', 'metric', 'pill']):
                    target_block = 'stats_banner'
                    message_response += "Stats banner is now visible."
                elif any(x in user_message for x in ['classroom', 'tab', 'class', 'picker', 'department', 'dept']):
                    target_block = 'classroom_tabs'
                    message_response += "Department tabs are now visible."
                elif any(x in user_message for x in ['header', 'logo', 'title', 'brand']):
                    target_block = 'header'
                    message_response += "Header is now visible."
                elif any(x in user_message for x in ['grid', 'student', 'roster', 'employee', 'card']):
                    target_block = 'student_grid'
                    message_response += "Employee grid is now visible."
                else:
                    action = None
            elif any(k in user_message for k in ['top', 'above', 'start', 'first', 'up']):
                action = 'move_top'
                if any(x in user_message for x in ['stat', 'banner', 'metric', 'pill']):
                    target_block = 'stats_banner'
                    message_response += "Metrics banner moved to the top!"
                elif any(x in user_message for x in ['classroom', 'tab', 'class', 'picker', 'department', 'dept']):
                    target_block = 'classroom_tabs'
                    message_response += "Department tabs moved to the top."
                elif any(x in user_message for x in ['header', 'logo', 'title', 'brand']):
                    target_block = 'header'
                    message_response += "Header moved to the top."
                elif any(x in user_message for x in ['grid', 'student', 'roster', 'employee', 'card']):
                    target_block = 'student_grid'
                    message_response += "Employee grid moved to the top."
                else:
                    action = None
            elif any(k in user_message for k in ['bottom', 'below', 'end', 'last', 'down']):
                action = 'move_bottom'
                if any(x in user_message for x in ['stat', 'banner', 'metric', 'pill']):
                    target_block = 'stats_banner'
                    message_response += "Metrics banner moved to the bottom."
                elif any(x in user_message for x in ['classroom', 'tab', 'class', 'picker', 'department', 'dept']):
                    target_block = 'classroom_tabs'
                    message_response += "Department tabs moved to the bottom."
                elif any(x in user_message for x in ['header', 'logo', 'title', 'brand']):
                    target_block = 'header'
                    message_response += "Header moved to the bottom."
                elif any(x in user_message for x in ['grid', 'student', 'roster', 'employee', 'card']):
                    target_block = 'student_grid'
                    message_response += "Employee grid moved to the bottom."
                else:
                    action = None

            if not action or (action != 'reset' and not target_block):
                action = None
                message_response = "I did not recognize that command. Try 'hide stats banner', 'move student_grid to top', or 'reset layout'!"
        
        if action:
            if action == 'hide' and target_block:
                AppLayoutBlock.objects.filter(block_id=target_block).update(is_visible=False)
            elif action == 'show' and target_block:
                AppLayoutBlock.objects.filter(block_id=target_block).update(is_visible=True)
            elif action == 'move_top' and target_block:
                AppLayoutBlock.objects.filter(block_id=target_block).update(order=0)
                all_blocks = list(AppLayoutBlock.objects.all().order_by('order'))
                for idx, b in enumerate(all_blocks):
                    b.order = idx + 1
                    b.save()
            elif action == 'move_bottom' and target_block:
                AppLayoutBlock.objects.filter(block_id=target_block).update(order=99)
                all_blocks = list(AppLayoutBlock.objects.all().order_by('order'))
                for idx, b in enumerate(all_blocks):
                    b.order = idx + 1
                    b.save()
            elif action == 'reset':
                default_blocks = {'header': 1, 'classroom_tabs': 2, 'stats_banner': 3, 'student_grid': 4}
                for bid, o in default_blocks.items():
                    AppLayoutBlock.objects.filter(block_id=bid).update(order=o, is_visible=True)
        
        updated_blocks = list(AppLayoutBlock.objects.all().order_by('order').values('block_id', 'title', 'order', 'is_visible'))
        return JsonResponse({
            'success': True,
            'message': message_response,
            'action': action,
            'block': target_block,
            'blocks': updated_blocks
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def schedule_context_processor(request):
    engineers_all = []
    active_engineer = None
    can_raise_support = False
    try:
        engineers_all = list(SupportEngineer.objects.all())
        active_engineer_id = request.session.get('engineer_id', '')
        if active_engineer_id:
            active_engineer = SupportEngineer.objects.filter(pk=active_engineer_id).first()

        if request.user.is_authenticated:
            if request.user.is_superuser:
                can_raise_support = True
            else:
                perm, created = EmployeeSupportPermission.objects.get_or_create(user=request.user)
                can_raise_support = perm.can_raise_tickets
    except Exception:
        pass

    return {
        'schedule_status': get_shift_schedule_status(),
        'engineers_all': engineers_all,
        'active_engineer': active_engineer,
        'can_raise_support': can_raise_support,
        'app_name': getattr(settings, 'APP_NAME', 'My Organization'),
    }


def ensure_support_seeded():
    if not AssignmentGroup.objects.exists():
        l2 = AssignmentGroup.objects.create(name="L2 Support Team", description="Tier 2 technical issues, app configuration, layout adjustments.")
        l3 = AssignmentGroup.objects.create(name="L3 Support Team", description="Tier 3 database fixes, data migrations, developer APIs.")
        l4 = AssignmentGroup.objects.create(name="L4 Support Team", description="Tier 4 system bugs, core server deployment, critical errors.")
        
        # Seed engineers
        spock = SupportEngineer.objects.create(name="Spock L2", email="spock@vulcan.com")
        spock.groups.add(l2)
        
        data_eng = SupportEngineer.objects.create(name="Data L3", email="data@enterprise.com")
        data_eng.groups.add(l3)
        
        worf = SupportEngineer.objects.create(name="Worf L4", email="worf@klingon.com")
        worf.groups.add(l4)
        
        # Create a default ticket
        t = SupportTicket.objects.create(
            caller="Manager Jenny",
            subject="Department emojis not loading correctly",
            description="The Engineering department layout seems to have lost its custom branding color in the grid view. Please restore it.",
            priority="moderate",
            state="new",
            assignment_group=l2
        )
        
        TicketActivity.objects.create(
            ticket=t,
            activity_type="work_note",
            author="System Seeder",
            content="Ticket automatically routed to L2 Support Team based on category 'layout adjustments'."
        )
        TicketActivity.objects.create(
            ticket=t,
            activity_type="customer_comment",
            author="System Seeder",
            content="Hello Manager Jenny, we have logged this ticket and assigned it to our L2 support group. An engineer will follow up shortly."
        )


def has_support_permission(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    perm, created = EmployeeSupportPermission.objects.get_or_create(user=user)
    return perm.can_raise_tickets


def support_home(request):
    if not request.user.is_authenticated:
        return redirect('teacher_login')
    if not has_support_permission(request.user):
        messages.error(request, "Access denied. You do not have permission to raise support tickets. 🔐")
        return redirect('home')

    # Simple search
    search_query = request.GET.get('ticket_number', '').strip()
    if search_query:
        ticket = SupportTicket.objects.filter(number__iexact=search_query).first()
        if ticket:
            return redirect('support_ticket_view', number=ticket.number)
        else:
            messages.error(request, f"No ticket found with number '{search_query}'. Please try again.")
            
    if request.method == 'POST':
        caller = request.POST.get('caller', '').strip()
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()
        priority = request.POST.get('priority', 'moderate')
        
        if not caller or not subject or not description:
            messages.error(request, "Please fill in all fields.")
        else:
            ticket = SupportTicket.objects.create(
                caller=caller,
                subject=subject,
                description=description,
                priority=priority,
                state='new'
            )
            TicketActivity.objects.create(
                ticket=ticket,
                activity_type='customer_comment',
                author='System Desk',
                content=f"Ticket '{ticket.number}' has been created successfully. Welcome to our workforce support queue!"
            )
            messages.success(request, f"Ticket {ticket.number} has been created successfully!")
            return redirect('support_ticket_view', number=ticket.number)
            
    tickets = SupportTicket.objects.all().order_by('-created_at')
    
    return render(request, 'attendance/support_home.html', {
        'tickets': tickets
    })


def support_ticket_view(request, number):
    if not request.user.is_authenticated:
        return redirect('teacher_login')
    if not has_support_permission(request.user):
        messages.error(request, "Access denied. You do not have permission to access support tickets. 🔐")
        return redirect('home')

    ensure_support_seeded()
    ticket = get_object_or_404(SupportTicket, number=number)
    
    if request.method == 'POST':
        author = request.POST.get('author', '').strip()
        comment = request.POST.get('comment', '').strip()
        
        if not author or not comment:
            messages.error(request, "Please fill in your name and message.")
        else:
            TicketActivity.objects.create(
                ticket=ticket,
                activity_type='customer_comment',
                author=author,
                content=comment
            )
            messages.success(request, "Your comment has been added successfully.")
            return redirect('support_ticket_view', number=ticket.number)
            
    activities = ticket.activities.filter(activity_type='customer_comment').order_by('created_at')
    
    return render(request, 'attendance/support_ticket_detail.html', {
        'ticket': ticket,
        'activities': activities
    })


def engineer_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('engineer_id'):
            return redirect('engineer_login')
        eng = SupportEngineer.objects.filter(pk=request.session['engineer_id'], is_active=True).first()
        if not eng:
            if 'engineer_id' in request.session:
                del request.session['engineer_id']
            messages.error(request, "Your session is invalid or your engineer account has been deactivated.")
            return redirect('engineer_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def engineer_login_view(request):
    if request.session.get('engineer_id'):
        return redirect('engineer_dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not email or not password:
            messages.error(request, "Please enter both email and password.")
        else:
            eng = SupportEngineer.objects.filter(email__iexact=email).first()
            if eng and eng.password == password:
                if not eng.is_active:
                    messages.error(request, "This account has been deactivated.")
                else:
                    request.session['engineer_id'] = eng.pk
                    messages.success(request, f"Successfully logged in as {eng.name}.")
                    return redirect('engineer_dashboard')
            else:
                messages.error(request, "Invalid email or password.")
                
    return render(request, 'attendance/support/engineer_login.html')


def engineer_logout_view(request):
    if 'engineer_id' in request.session:
        del request.session['engineer_id']
    messages.success(request, "Logged out of IT Tech Services portal.")
    return render(request, 'attendance/support/engineer_logout.html')


@engineer_login_required
def engineer_dashboard(request):
    ensure_support_seeded()
    
    group_filter = request.GET.get('group', '')
    state_filter = request.GET.get('state', '')
    priority_filter = request.GET.get('priority', '')
    
    tickets = SupportTicket.objects.all().order_by('-created_at')
    if group_filter:
        tickets = tickets.filter(assignment_group_id=group_filter)
    if state_filter:
        tickets = tickets.filter(state=state_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
        
    groups = AssignmentGroup.objects.all()
    engineers = SupportEngineer.objects.all()
    
    active_engineer_id = request.session.get('active_engineer_id', '')
    active_engineer = None
    if active_engineer_id:
        active_engineer = SupportEngineer.objects.filter(pk=active_engineer_id).first()
        
    if request.method == 'POST' and 'set_engineer_id' in request.POST:
        eng_id = request.POST.get('set_engineer_id', '')
        if eng_id:
            request.session['active_engineer_id'] = eng_id
        else:
            if 'active_engineer_id' in request.session:
                del request.session['active_engineer_id']
        return redirect('engineer_dashboard')

    engineer_breakdown = []
    for eng in SupportEngineer.objects.filter(is_active=True):
        total_assigned = eng.assigned_tickets.count()
        active_assigned = eng.assigned_tickets.exclude(state__in=['resolved', 'closed']).count()
        grp_names = ", ".join([g.name for g in eng.groups.all()])
        engineer_breakdown.append({
            'name': eng.name,
            'email': eng.email,
            'groups_str': grp_names or "None",
            'total_count': total_assigned,
            'active_count': active_assigned,
        })
    engineer_breakdown.sort(key=lambda x: x['active_count'], reverse=True)

    sla_breached_count = 0
    active_sla_count = 0
    unassigned_count = SupportTicket.objects.filter(assigned_to__isnull=True).exclude(state__in=['resolved', 'closed']).count()
    for t in SupportTicket.objects.exclude(state__in=['resolved', 'closed']):
        status_info = t.get_sla_status()
        if status_info['status'] == 'breached':
            sla_breached_count += 1
        elif status_info['status'] in ['active', 'warning']:
            active_sla_count += 1

    return render(request, 'attendance/support/engineer_dashboard.html', {
        'tickets': tickets,
        'groups': groups,
        'engineers': engineers,
        'active_engineer': active_engineer,
        'selected_group': group_filter,
        'selected_state': state_filter,
        'selected_priority': priority_filter,
        'engineer_breakdown': engineer_breakdown,
        'sla_breached_count': sla_breached_count,
        'active_sla_count': active_sla_count,
        'unassigned_count': unassigned_count,
    })


@engineer_login_required
def engineer_ticket_detail(request, number):
    ensure_support_seeded()
    ticket = get_object_or_404(SupportTicket, number=number)
    
    active_engineer_id = request.session.get('active_engineer_id', '')
    active_engineer = None
    if active_engineer_id:
        active_engineer = SupportEngineer.objects.filter(pk=active_engineer_id).first()
        
    if request.method == 'POST':
        state = request.POST.get('state', '')
        priority = request.POST.get('priority', '')
        group_id = request.POST.get('assignment_group', '')
        assigned_id = request.POST.get('assigned_to', '')
        
        author_name = active_engineer.name if active_engineer else "Support System"
        
        if state:
            ticket.state = state
        if priority:
            ticket.priority = priority
            
        if group_id:
            ticket.assignment_group_id = group_id
        else:
            ticket.assignment_group = None
            
        if assigned_id:
            ticket.assigned_to_id = assigned_id
        else:
            ticket.assigned_to = None
            
        ticket.save()
        
        work_note_content = request.POST.get('work_note', '').strip()
        customer_comment_content = request.POST.get('customer_comment', '').strip()
        
        if work_note_content:
            TicketActivity.objects.create(
                ticket=ticket,
                activity_type='work_note',
                author=author_name,
                content=work_note_content
            )
            messages.success(request, "Internal Work Note added successfully.")
            
        if customer_comment_content:
            TicketActivity.objects.create(
                ticket=ticket,
                activity_type='customer_comment',
                author=author_name,
                content=customer_comment_content
            )
            messages.success(request, "Customer Comment added successfully.")
            
        messages.success(request, f"Ticket {ticket.number} updated successfully.")
        return redirect('engineer_ticket_detail', number=ticket.number)
        
    groups = AssignmentGroup.objects.all()
    engineers = SupportEngineer.objects.all()
    if ticket.assignment_group:
        engineers = engineers.filter(groups=ticket.assignment_group)
        
    activities = ticket.activities.all().order_by('-created_at')
    
    return render(request, 'attendance/support/engineer_ticket_detail.html', {
        'ticket': ticket,
        'groups': groups,
        'engineers': engineers,
        'activities': activities,
        'active_engineer': active_engineer,
    })


@engineer_login_required
def engineer_list(request):
    ensure_support_seeded()
    engineers = SupportEngineer.objects.all()
    return render(request, 'attendance/support/engineer_list.html', {
        'engineers': engineers
    })


@engineer_login_required
def engineer_create(request):
    ensure_support_seeded()
    groups = AssignmentGroup.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        group_ids = request.POST.getlist('groups')
        is_active = request.POST.get('is_active', '') == 'true'
        
        if not name or not email:
            messages.error(request, "Please enter name and email.")
        else:
            eng = SupportEngineer.objects.create(
                name=name,
                email=email,
                is_active=is_active
            )
            if group_ids:
                eng.groups.set(group_ids)
            messages.success(request, f"Engineer {name} created successfully.")
            return redirect('engineer_list')
            
    return render(request, 'attendance/support/engineer_form.html', {
        'groups': groups,
        'action': 'Create'
    })


@engineer_login_required
def engineer_edit(request, pk):
    ensure_support_seeded()
    engineer = get_object_or_404(SupportEngineer, pk=pk)
    groups = AssignmentGroup.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        group_ids = request.POST.getlist('groups')
        is_active = request.POST.get('is_active', '') == 'true'
        
        if not name or not email:
            messages.error(request, "Please enter name and email.")
        else:
            engineer.name = name
            engineer.email = email
            engineer.is_active = is_active
            engineer.save()
            engineer.groups.set(group_ids)
            messages.success(request, f"Engineer {name} updated successfully.")
            return redirect('engineer_list')
            
    return render(request, 'attendance/support/engineer_form.html', {
        'engineer': engineer,
        'groups': groups,
        'action': 'Edit'
    })


@engineer_login_required
def engineer_delete(request, pk):
    ensure_support_seeded()
    engineer = get_object_or_404(SupportEngineer, pk=pk)
    name = engineer.name
    if request.method == 'POST':
        engineer.delete()
        messages.success(request, f"Engineer {name} deleted successfully.")
        return redirect('engineer_list')
    return render(request, 'attendance/support/engineer_confirm_delete.html', {
        'engineer': engineer
    })


@engineer_login_required
def group_list(request):
    ensure_support_seeded()
    groups = AssignmentGroup.objects.all()
    return render(request, 'attendance/support/group_list.html', {
        'groups': groups
    })


@engineer_login_required
def group_create(request):
    ensure_support_seeded()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, "Please enter a group name.")
        else:
            try:
                AssignmentGroup.objects.create(name=name, description=description)
                messages.success(request, f"Group {name} created successfully.")
                return redirect('group_list')
            except Exception as e:
                messages.error(request, f"Error creating group: {e}")
                
    return render(request, 'attendance/support/group_form.html', {
        'action': 'Create'
    })


@engineer_login_required
def group_edit(request, pk):
    ensure_support_seeded()
    group = get_object_or_404(AssignmentGroup, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, "Please enter a group name.")
        else:
            try:
                group.name = name
                group.description = description
                group.save()
                messages.success(request, f"Group {name} updated successfully.")
                return redirect('group_list')
            except Exception as e:
                messages.error(request, f"Error updating group: {e}")
                
    return render(request, 'attendance/support/group_form.html', {
        'group': group,
        'action': 'Edit'
    })


@engineer_login_required
def group_delete(request, pk):
    ensure_support_seeded()
    group = get_object_or_404(AssignmentGroup, pk=pk)
    name = group.name
    if request.method == 'POST':
        group.delete()
        messages.success(request, f"Group {name} deleted successfully.")
        return redirect('group_list')
    return render(request, 'attendance/support/group_confirm_delete.html', {
        'group': group
    })


@engineer_login_required
def identity_manager(request):
    ensure_support_seeded()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'toggle_teacher_permission':
            user_id = request.POST.get('user_id')
            user_to_toggle = get_object_or_404(User, pk=user_id)
            perm, created = EmployeeSupportPermission.objects.get_or_create(user=user_to_toggle)
            perm.can_raise_tickets = not perm.can_raise_tickets
            perm.save()
            messages.success(request, f"Updated support ticket permissions for {user_to_toggle.username} to: {perm.can_raise_tickets}")
            return redirect('identity_manager')
            
        elif action == 'update_engineer_groups':
            engineer_id = request.POST.get('engineer_id')
            engineer = get_object_or_404(SupportEngineer, pk=engineer_id)
            group_ids = request.POST.getlist('groups')
            group_pks = [int(gid) for gid in group_ids if gid.isdigit()]
            engineer.groups.set(AssignmentGroup.objects.filter(pk__in=group_pks))
            engineer.save()
            messages.success(request, f"Updated assignment groups for engineer {engineer.name}.")
            return redirect('identity_manager')

        elif action == 'toggle_staff_status':
            user_id = request.POST.get('user_id')
            user_to_toggle = get_object_or_404(User, pk=user_id)
            user_to_toggle.is_staff = not user_to_toggle.is_staff
            user_to_toggle.save()
            messages.success(request, f"Updated admin (is_staff) status for {user_to_toggle.username} to: {user_to_toggle.is_staff}")
            return redirect('identity_manager')

    users = User.objects.all().order_by('username')
    engineers = SupportEngineer.objects.all().order_by('name')
    groups = AssignmentGroup.objects.all().order_by('name')

    user_perms = []
    for u in users:
        perm, created = EmployeeSupportPermission.objects.get_or_create(user=u)
        user_perms.append({
            'user': u,
            'can_raise': perm.can_raise_tickets or u.is_superuser
        })

    return render(request, 'attendance/support/identity_manager.html', {
        'user_perms': user_perms,
        'engineers': engineers,
        'groups': groups,
    })


# ==============================================================================
# LEOXUR MAILS & CHAT COMMUNICATION SUITE VIEWS
# ==============================================================================

def get_all_leoxur_participants():
    participants = []
    
    # 1. Managers (Django Users)
    for u in User.objects.all():
        participants.append({
            'id': f"manager_{u.id}",
            'name': f"{u.username} (Manager)",
            'role': 'Manager',
            'email': u.email or f"{u.username}@leoxur.com",
            'avatar_emoji': '💼',
            'avatar_color': '#4F46E5',
        })
        
    # 2. Support Engineers
    for eng in SupportEngineer.objects.filter(is_active=True):
        participants.append({
            'id': f"engineer_{eng.id}",
            'name': f"{eng.name} (Support Engineer)",
            'role': 'Support Engineer',
            'email': eng.email,
            'avatar_emoji': '🛠️',
            'avatar_color': '#10B981',
        })
        
    # 3. Employees
    for emp in Employee.objects.filter(is_active=True):
        participants.append({
            'id': f"employee_{emp.id}",
            'name': f"{emp.full_name} (Employee - {emp.department})",
            'role': 'Employee',
            'email': f"{emp.first_name.lower()}.{emp.last_name.lower()}@leoxur.com",
            'avatar_emoji': emp.avatar_emoji or '👤',
            'avatar_color': emp.avatar_color or '#6B7280',
        })
        
    return participants

def get_participant_by_id(participant_id):
    parts = participant_id.split('_')
    if len(parts) < 2:
        return None
    role, pk_str = parts[0], parts[1]
    if not pk_str.isdigit():
        return None
    pk = int(pk_str)
    
    if role == 'manager':
        u = User.objects.filter(pk=pk).first()
        if u:
            return {
                'id': participant_id,
                'name': f"{u.username} (Manager)",
                'role': 'Manager',
                'email': u.email or f"{u.username}@leoxur.com",
                'avatar_emoji': '💼',
                'avatar_color': '#4F46E5',
            }
    elif role == 'engineer':
        eng = SupportEngineer.objects.filter(pk=pk).first()
        if eng:
            return {
                'id': participant_id,
                'name': f"{eng.name} (Support Engineer)",
                'role': 'Support Engineer',
                'email': eng.email,
                'avatar_emoji': '🛠️',
                'avatar_color': '#10B981',
            }
    elif role == 'employee':
        emp = Employee.objects.filter(pk=pk).first()
        if emp:
            return {
                'id': participant_id,
                'name': f"{emp.full_name} (Employee - {emp.department})",
                'role': 'Employee',
                'email': f"{emp.first_name.lower()}.{emp.last_name.lower()}@leoxur.com",
                'avatar_emoji': emp.avatar_emoji or '👤',
                'avatar_color': emp.avatar_color or '#6B7280',
            }
    return None

def leoxur_comm_dashboard(request):
    # Determine active communication user
    active_user_id = request.session.get('leoxur_user_id')
    active_user = None

    # Auto-login if Django user is authenticated and session is empty
    if not active_user_id and request.user.is_authenticated:
        active_user_id = f"manager_{request.user.id}"
        request.session['leoxur_user_id'] = active_user_id
        
    if active_user_id:
        active_user = get_participant_by_id(active_user_id)
        
    # Get all active participants for dropdowns/pickers
    all_users = get_all_leoxur_participants()
    all_employees = Employee.objects.filter(is_active=True).order_by('first_name')
    all_engineers = SupportEngineer.objects.filter(is_active=True).order_by('name')
    
    context = {
        'active_user_id': active_user_id,
        'active_user': active_user,
        'all_users': all_users,
        'all_employees': all_employees,
        'all_engineers': all_engineers,
        'schedule_status': get_shift_schedule_status(),
    }
    return render(request, 'attendance/leoxur_comm.html', context)


@require_POST
def leoxur_comm_auth(request):
    import json
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')  # e.g., 'manager_1', 'employee_3', 'engineer_2'
        secret = data.get('secret', '').strip()  # password or pin
        
        if not user_id:
            return JsonResponse({'success': False, 'error': 'Please select a profile.'})
            
        parts = user_id.split('_')
        if len(parts) < 2:
            return JsonResponse({'success': False, 'error': 'Invalid profile ID.'})
            
        role, pk_str = parts[0], parts[1]
        if not pk_str.isdigit():
            return JsonResponse({'success': False, 'error': 'Invalid profile ID.'})
        pk = int(pk_str)
        
        if role == 'manager':
            # Check if already authenticated via Django session
            if request.user.is_authenticated and request.user.id == pk:
                request.session['leoxur_user_id'] = user_id
                return JsonResponse({'success': True, 'user_id': user_id})
            else:
                u = User.objects.filter(pk=pk).first()
                if not u:
                    return JsonResponse({'success': False, 'error': 'Manager not found.'})
                # Authenticate with credentials
                from django.contrib.auth import authenticate
                user = authenticate(username=u.username, password=secret)
                if user is not None:
                    auth_login(request, user)
                    request.session['leoxur_user_id'] = user_id
                    return JsonResponse({'success': True, 'user_id': user_id})
                else:
                    return JsonResponse({'success': False, 'error': 'Invalid password.'})
                    
        elif role == 'engineer':
            eng = SupportEngineer.objects.filter(pk=pk, is_active=True).first()
            if not eng:
                return JsonResponse({'success': False, 'error': 'Support Engineer not found or inactive.'})
            if eng.password == secret:
                request.session['leoxur_user_id'] = user_id
                return JsonResponse({'success': True, 'user_id': user_id})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid engineer password.'})
                
        elif role == 'employee':
            emp = Employee.objects.filter(pk=pk, is_active=True).first()
            if not emp:
                return JsonResponse({'success': False, 'error': 'Employee not found or inactive.'})
            if emp.pin_code == secret:
                request.session['leoxur_user_id'] = user_id
                return JsonResponse({'success': True, 'user_id': user_id})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid PIN.'})
                
        return JsonResponse({'success': False, 'error': 'Access Denied: Invalid role.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def leoxur_comm_logout(request):
    if 'leoxur_user_id' in request.session:
        del request.session['leoxur_user_id']
    return JsonResponse({'success': True})


def leoxur_comm_data(request):
    active_user_id = request.session.get('leoxur_user_id')
    if not active_user_id:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
    participants = get_all_leoxur_participants()
    participant_map = {p['id']: p for p in participants}
    
    # 1. Emails: sent to or received by the active user
    emails_qs = LeoxurEmail.objects.filter(Q(sender_id=active_user_id) | Q(receiver_id=active_user_id)).order_by('-created_at')
    emails = []
    for email in emails_qs:
        sender = participant_map.get(email.sender_id, {'name': email.sender_id, 'avatar_emoji': '✉️', 'avatar_color': '#9CA3AF'})
        receiver = participant_map.get(email.receiver_id, {'name': email.receiver_id, 'avatar_emoji': '✉️', 'avatar_color': '#9CA3AF'})
        emails.append({
            'id': email.id,
            'sender_id': email.sender_id,
            'sender': sender,
            'receiver_id': email.receiver_id,
            'receiver': receiver,
            'subject': email.subject,
            'body': email.body,
            'created_at': timezone.localtime(email.created_at).strftime('%b %d, %Y %I:%M %p'),
            'is_read': email.is_read,
        })
        
    # 2. Chats/Messages:
    # Get group channel rooms: 'general', 'support', 'managers' (restricted to managers)
    # Plus direct message rooms involving active user: 'direct_a_b'
    rooms = ['general', 'support']
    if active_user_id.startswith('manager_'):
        rooms.append('managers')
        
    messages_qs = LeoxurMessage.objects.filter(
        Q(room_id__in=rooms) |
        (Q(room_id__startswith='direct_') & Q(room_id__contains=active_user_id))
    ).order_by('created_at')
    
    messages = []
    for msg in messages_qs:
        # Extra security check: if direct chat, verify user is in room_id
        if msg.room_id.startswith('direct_') and active_user_id not in msg.room_id:
            continue
            
        sender = participant_map.get(msg.sender_id, {'name': msg.sender_id, 'avatar_emoji': '👤', 'avatar_color': '#9CA3AF'})
        
        # Populate parent message details for quoted replies
        parent_sender_name = None
        parent_content = None
        if msg.parent_message:
            parent_sender = participant_map.get(msg.parent_message.sender_id, {'name': msg.parent_message.sender_id})
            parent_sender_name = parent_sender['name']
            parent_content = msg.parent_message.content
            
        messages.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'sender': sender,
            'receiver_id': msg.receiver_id,
            'room_id': msg.room_id,
            'content': msg.content,
            'message_type': msg.message_type,
            'created_at': timezone.localtime(msg.created_at).strftime('%I:%M %p'),
            'created_at_full': timezone.localtime(msg.created_at).strftime('%b %d, %Y %I:%M %p'),
            'parent_id': msg.parent_message.id if msg.parent_message else None,
            'parent_sender_name': parent_sender_name,
            'parent_content': parent_content,
        })
        
    # 3. Tasks/Jira Board Tasks
    # Auto-archive tasks that have been in 'done' status for more than 24 hours
    cutoff_time = timezone.now() - timedelta(hours=24)
    LeoxurTask.objects.filter(status='done', updated_at__lte=cutoff_time).update(status='archived')

    tasks_qs = LeoxurTask.objects.all().order_by('-created_at')
    tasks = []
    for task in tasks_qs:
        creator = participant_map.get(task.creator_id, {'name': task.creator_id, 'avatar_emoji': '👤', 'avatar_color': '#9CA3AF'})
        assignee = participant_map.get(task.assignee_id, {'name': 'Unassigned', 'avatar_emoji': '👤', 'avatar_color': '#E5E7EB'}) if task.assignee_id else {'name': 'Unassigned', 'avatar_emoji': '👤', 'avatar_color': '#E5E7EB'}
        
        comments_qs = task.comments.all().order_by('created_at')
        comments = []
        for comment in comments_qs:
            comments.append({
                'id': comment.id,
                'author_id': comment.author_id,
                'author_name': comment.author_name,
                'content': comment.content,
                'created_at': timezone.localtime(comment.created_at).strftime('%b %d, %Y %I:%M %p'),
            })

        tasks.append({
            'id': task.id,
            'title': task.title,
            'description': task.description or '',
            'priority': task.priority,
            'status': task.status,
            'creator_id': task.creator_id,
            'creator': creator,
            'assignee_id': task.assignee_id or '',
            'assignee': assignee,
            'created_at': timezone.localtime(task.created_at).strftime('%b %d, %Y %I:%M %p'),
            'updated_at': timezone.localtime(task.updated_at).strftime('%b %d, %Y %I:%M %p'),
            'comments': comments,
        })

    active_user = participant_map.get(active_user_id)
    
    return JsonResponse({
        'success': True,
        'active_user': active_user,
        'participants': participants,
        'emails': emails,
        'messages': messages,
        'tasks': tasks,
        'meetings': [],
    })


@require_POST
def leoxur_send_email(request):
    active_user_id = request.session.get('leoxur_user_id')
    if not active_user_id:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
    import json
    try:
        data = json.loads(request.body)
        receiver_id = data.get('receiver_id')
        subject = data.get('subject', '').strip()
        body = data.get('body', '').strip()
        
        if not receiver_id or not subject or not body:
            return JsonResponse({'success': False, 'error': 'Receiver, Subject, and Body are required.'})
            
        email = LeoxurEmail.objects.create(
            sender_id=active_user_id,
            receiver_id=receiver_id,
            subject=subject,
            body=body
        )
        return JsonResponse({'success': True, 'email_id': email.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def leoxur_send_chat(request):
    active_user_id = request.session.get('leoxur_user_id')
    if not active_user_id:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
    import json
    try:
        data = json.loads(request.body)
        room_id = data.get('room_id')
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'text')
        parent_id = data.get('parent_id')
        
        if not room_id or not content:
            return JsonResponse({'success': False, 'error': 'Room ID and Content are required.'})
            
        # Security checks
        if room_id == 'managers' and not active_user_id.startswith('manager_'):
            return JsonResponse({'success': False, 'error': 'Access denied to managers channel.'}, status=403)
            
        if room_id.startswith('direct_') and active_user_id not in room_id:
            return JsonResponse({'success': False, 'error': 'Access denied to direct chat room.'}, status=403)
            
        # Determine direct receiver if direct chat room
        receiver_id = None
        if room_id.startswith('direct_'):
            parts = room_id.replace('direct_', '').split('_')
            # Look up other user from participants
            for participant in get_all_leoxur_participants():
                p_id = participant['id']
                if p_id != active_user_id and p_id in room_id:
                    receiver_id = p_id
                    break
                    
        parent_msg = None
        if parent_id:
            parent_msg = LeoxurMessage.objects.filter(id=parent_id).first()
            
        msg = LeoxurMessage.objects.create(
            sender_id=active_user_id,
            receiver_id=receiver_id,
            room_id=room_id,
            content=content,
            message_type=message_type,
            parent_message=parent_msg
        )
        return JsonResponse({'success': True, 'message_id': msg.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def leoxur_read_email(request):
    active_user_id = request.session.get('leoxur_user_id')
    if not active_user_id:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    import json
    try:
        data = json.loads(request.body)
        email_id = data.get('email_id')
        LeoxurEmail.objects.filter(id=email_id, receiver_id=active_user_id).update(is_read=True)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def leoxur_create_task(request):
    active_user_id = request.session.get('leoxur_user_id')
    if not active_user_id:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
    import json
    try:
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        priority = data.get('priority', 'medium').strip().lower()
        status = data.get('status', 'backlog').strip().lower()
        assignee_id = data.get('assignee_id', '').strip() or None
        
        if not title:
            return JsonResponse({'success': False, 'error': 'Title is required.'})
            
        task = LeoxurTask.objects.create(
            title=title,
            description=description,
            priority=priority,
            status=status,
            creator_id=active_user_id,
            assignee_id=assignee_id
        )
        return JsonResponse({'success': True, 'task_id': task.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def leoxur_update_task(request):
    active_user_id = request.session.get('leoxur_user_id')
    if not active_user_id:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
    import json
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        task = get_object_or_404(LeoxurTask, id=task_id)
        
        if 'status' in data:
            new_status = data.get('status').strip().lower()
            if new_status != task.status:
                # 1. Review status transition check: only managers can move out of in_review
                if task.status == 'in_review':
                    if not active_user_id.startswith('manager_'):
                        return JsonResponse({'success': False, 'error': 'Only managers can approve or reject issues in review.'}, status=403)
                # 2. Assignee check: if assigned, only the assignee or a manager can move it
                elif task.assignee_id and task.assignee_id != active_user_id and not active_user_id.startswith('manager_'):
                    return JsonResponse({'success': False, 'error': 'Only the assignee can change the status of this task.'}, status=403)
                
                task.status = new_status
                
        if 'title' in data:
            task.title = data.get('title').strip()
        if 'description' in data:
            task.description = data.get('description').strip()
        if 'priority' in data:
            task.priority = data.get('priority').strip().lower()
        if 'assignee_id' in data:
            assignee_id = data.get('assignee_id', '').strip() or None
            task.assignee_id = assignee_id
            
        task.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def leoxur_delete_task(request):
    active_user_id = request.session.get('leoxur_user_id')
    if not active_user_id:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
    import json
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        task = get_object_or_404(LeoxurTask, id=task_id)
        task.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def leoxur_create_task_comment(request):
    active_user_id = request.session.get('leoxur_user_id')
    if not active_user_id:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
    import json
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        content = data.get('content', '').strip()
        if not content:
            return JsonResponse({'success': False, 'error': 'Comment content cannot be empty.'})
            
        task = get_object_or_404(LeoxurTask, id=task_id)
        
        # Get active user display name
        participants = get_all_leoxur_participants()
        participant_map = {p['id']: p for p in participants}
        active_user = participant_map.get(active_user_id, {'name': active_user_id})
        
        comment = LeoxurTaskComment.objects.create(
            task=task,
            author_id=active_user_id,
            author_name=active_user.get('name', active_user_id),
            content=content
        )
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'author_id': comment.author_id,
                'author_name': comment.author_name,
                'content': comment.content,
                'created_at': timezone.localtime(comment.created_at).strftime('%b %d, %Y %I:%M %p'),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


