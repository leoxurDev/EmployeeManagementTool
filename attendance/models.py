from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.core.validators import RegexValidator
from django.contrib.auth.models import User


class DepartmentOption(models.Model):
    emoji = models.CharField(max_length=5, unique=True, blank=True, null=True)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Department Options'

    def __str__(self):
        if self.emoji:
            return f"{self.emoji} {self.name}"
        return self.name

    @property
    def display_value(self):
        if self.emoji:
            return f"{self.emoji} {self.name}"
        return self.name

    def clean(self):
        super().clean()
        if self.emoji == "":
            self.emoji = None

    def save(self, *args, **kwargs):
        if self.emoji == "":
            self.emoji = None
        super().save(*args, **kwargs)


class AvatarEmoji(models.Model):
    emoji = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=50)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Avatar Emoji'
        verbose_name_plural = 'Avatar Emojis'

    def __str__(self):
        return f"{self.emoji} {self.name}"


class AvatarColor(models.Model):
    hex_code = models.CharField(max_length=7, unique=True)
    name = models.CharField(max_length=50)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Avatar Colors'

    def __str__(self):
        return f"{self.name} ({self.hex_code})"

    @property
    def display_value(self):
        return self.hex_code


class Employee(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    department = models.CharField(max_length=50)
    avatar_emoji = models.CharField(max_length=5)
    avatar_color = models.CharField(max_length=7)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    pin_code = models.CharField(
        max_length=4,
        default="1234",
        validators=[RegexValidator(r'^\d{4}$', 'PIN code must be exactly 4 digits.')]
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.department})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def initials(self):
        first = self.first_name[0] if self.first_name else ''
        last = self.last_name[0] if self.last_name else ''
        return (first + last).upper()

    def today_attendance(self):
        today = timezone.localdate()
        return self.attendance_set.filter(date=today).first()

    def today_roster(self):
        today = timezone.localdate()
        return self.roster_set.filter(date=today).first()


class Roster(models.Model):
    SHIFT_CHOICES = [
        ('morning', 'Morning Shift (06:00 - 14:00)'),
        ('afternoon', 'Afternoon Shift (14:00 - 22:00)'),
        ('night', 'Night Shift (22:00 - 06:00)'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, default='morning')

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['date', 'employee__first_name']

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.get_shift_display()})"


class Attendance(models.Model):
    SHIFT_CHOICES = [
        ('morning', 'Morning Shift'),
        ('afternoon', 'Afternoon Shift'),
        ('night', 'Night Shift'),
    ]

    STATUS_CHOICES = [
        ('present', 'Present ✅'),
        ('absent', 'Absent ❌'),
        ('late', 'Late ⏰'),
    ]

    WORK_MODE_CHOICES = [
        ('office', 'Office 🏢'),
        ('remote', 'Remote 🏠'),
        ('field', 'Field 🚗'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    work_mode = models.CharField(max_length=15, choices=WORK_MODE_CHOICES, default='office')
    checked_in_at = models.DateTimeField(auto_now_add=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date', 'employee__first_name']

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.status})"

    @property
    def hours_worked(self):
        if self.checked_in_at and self.checked_out_at:
            duration = self.checked_out_at - self.checked_in_at
            return round(duration.total_seconds() / 3600.0, 2)
        return 0.0

    @staticmethod
    def get_current_shift_by_time():
        """Determine shift based on current hour."""
        hour = timezone.localtime().hour
        if 6 <= hour < 14:
            return 'morning'
        elif 14 <= hour < 22:
            return 'afternoon'
        else:
            return 'night'


class AppLayoutBlock(models.Model):
    block_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} (order: {self.order}, visible: {self.is_visible})"


class AssignmentGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SupportEngineer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    password = models.CharField(max_length=128, default="engineer123")
    groups = models.ManyToManyField(AssignmentGroup, blank=True, related_name='engineers')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        grps = ", ".join([g.name for g in self.groups.all()])
        if grps:
            return f"{self.name} ({grps})"
        return self.name


class SupportTicket(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    STATE_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    number = models.CharField(max_length=15, unique=True, blank=True)
    caller = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=15, choices=PRIORITY_CHOICES, default='moderate')
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='new')
    assignment_group = models.ForeignKey(AssignmentGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    assigned_to = models.ForeignKey(SupportEngineer, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.number} - {self.subject} ({self.state})"

    def save(self, *args, **kwargs):
        if self.state in ['resolved', 'closed']:
            if not self.resolved_at:
                self.resolved_at = timezone.now()
        else:
            self.resolved_at = None

        if not self.number:
            super().save(*args, **kwargs)
            self.number = f"TKT{100000 + self.id}"
            SupportTicket.objects.filter(pk=self.id).update(number=self.number)
        else:
            super().save(*args, **kwargs)

    def _format_timedelta(self, td):
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def get_sla_status(self):
        durations = {
            'critical': timedelta(hours=1),
            'high': timedelta(hours=4),
            'moderate': timedelta(hours=8),
            'low': timedelta(hours=24),
        }
        sla_duration = durations.get(self.priority, timedelta(hours=8))
        deadline = self.created_at + sla_duration
        
        # If resolved or closed, check if resolved before deadline
        if self.state in ['resolved', 'closed']:
            end_time = self.resolved_at or self.updated_at
            if end_time <= deadline:
                return {
                    'status': 'met',
                    'label': 'SLA: Met',
                    'class': 'badge-moderate'
                }
            else:
                overdue = end_time - deadline
                overdue_str = self._format_timedelta(overdue)
                return {
                    'status': 'breached_resolved',
                    'label': f'SLA: Breached (by {overdue_str})',
                    'class': 'badge-critical'
                }
        
        # If active, calculate remaining time
        now = timezone.now()
        if now > deadline:
            overdue = now - deadline
            overdue_str = self._format_timedelta(overdue)
            return {
                'status': 'breached',
                'label': f'SLA: Breached (by {overdue_str})',
                'class': 'badge-critical'
            }
        else:
            remaining = deadline - now
            remaining_str = self._format_timedelta(remaining)
            if remaining < (sla_duration / 4):
                return {
                    'status': 'warning',
                    'label': f'SLA: Warning ({remaining_str} left)',
                    'class': 'badge-high'
                }
            return {
                'status': 'active',
                'label': f'SLA: Active ({remaining_str} left)',
                'class': 'badge-state-new'
            }


class TicketActivity(models.Model):
    TYPE_CHOICES = [
        ('work_note', 'Work Note (Internal)'),
        ('customer_comment', 'Customer Comment (Visible to Client)'),
    ]

    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    author = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_activity_type_display()} by {self.author} at {self.created_at}"


class EmployeeSupportPermission(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='support_permission')
    can_raise_tickets = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - Can raise support: {self.can_raise_tickets}"


class LeoxurEmail(models.Model):
    sender_id = models.CharField(max_length=50) # e.g. employee_1, manager_1, engineer_1
    receiver_id = models.CharField(max_length=50) # e.g. employee_2
    subject = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Email from {self.sender_id} to {self.receiver_id}: {self.subject}"


class LeoxurMessage(models.Model):
    sender_id = models.CharField(max_length=50)
    receiver_id = models.CharField(max_length=50, blank=True, null=True) # None for group chats/channels
    room_id = models.CharField(max_length=100) # e.g. 'general', 'support', 'managers', or direct_chat key
    content = models.TextField()
    message_type = models.CharField(max_length=20, default='text') # text, system, meeting_invite
    created_at = models.DateTimeField(auto_now_add=True)
    parent_message = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message by {self.sender_id} in {self.room_id} at {self.created_at}"


class LeoxurTask(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('highest', 'Highest'),
    ]

    STATUS_CHOICES = [
        ('backlog', 'Backlog'),
        ('in_progress', 'In Progress'),
        ('in_review', 'In Review'),
        ('done', 'Done'),
        ('archived', 'Archived'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='backlog')
    creator_id = models.CharField(max_length=50) # e.g. manager_1, employee_1, engineer_1
    assignee_id = models.CharField(max_length=50, blank=True, null=True) # e.g. manager_1, employee_2, engineer_1
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.status}) - Priority: {self.priority}"


class LeoxurTaskComment(models.Model):
    task = models.ForeignKey(LeoxurTask, on_delete=models.CASCADE, related_name='comments')
    author_id = models.CharField(max_length=50) # e.g. employee_1, manager_1
    author_name = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author_name} on TSK-{self.task_id} at {self.created_at}"


