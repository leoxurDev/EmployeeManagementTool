from django.contrib import admin
from .models import (
    Employee, Roster, Attendance, DepartmentOption, AvatarEmoji, AvatarColor,
    AssignmentGroup, SupportEngineer, SupportTicket, TicketActivity, EmployeeSupportPermission,
    LeoxurEmail, LeoxurMessage, LeoxurTask
)


@admin.register(DepartmentOption)
class DepartmentOptionAdmin(admin.ModelAdmin):
    list_display = ('emoji', 'name', 'description', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'emoji')


@admin.register(AvatarEmoji)
class AvatarEmojiAdmin(admin.ModelAdmin):
    list_display = ('emoji', 'name', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'emoji')


@admin.register(AvatarColor)
class AvatarColorAdmin(admin.ModelAdmin):
    list_display = ('hex_code', 'name', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'hex_code')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'department', 'avatar_emoji', 'is_active', 'date_created')
    list_filter = ('department', 'is_active')
    search_fields = ('first_name', 'last_name')


@admin.register(Roster)
class RosterAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'shift')
    list_filter = ('date', 'shift', 'employee__department')
    search_fields = ('employee__first_name', 'employee__last_name')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'shift', 'status', 'work_mode', 'checked_in_at', 'checked_out_at', 'hours_worked')
    list_filter = ('status', 'work_mode', 'date', 'shift', 'employee__department')
    search_fields = ('employee__first_name', 'employee__last_name')


@admin.register(EmployeeSupportPermission)
class EmployeeSupportPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'can_raise_tickets')
    list_filter = ('can_raise_tickets',)
    search_fields = ('user__username',)


@admin.register(AssignmentGroup)
class AssignmentGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(SupportEngineer)
class SupportEngineerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'email')


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('number', 'caller', 'subject', 'state', 'priority', 'created_at')
    list_filter = ('state', 'priority', 'created_at')
    search_fields = ('number', 'caller', 'subject')


@admin.register(TicketActivity)
class TicketActivityAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'activity_type', 'author', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('ticket__number', 'author', 'content')


@admin.register(LeoxurEmail)
class LeoxurEmailAdmin(admin.ModelAdmin):
    list_display = ('sender_id', 'receiver_id', 'subject', 'created_at', 'is_read')
    list_filter = ('created_at', 'is_read')
    search_fields = ('sender_id', 'receiver_id', 'subject', 'body')


@admin.register(LeoxurMessage)
class LeoxurMessageAdmin(admin.ModelAdmin):
    list_display = ('sender_id', 'room_id', 'created_at', 'message_type')
    list_filter = ('room_id', 'created_at', 'message_type')
    search_fields = ('sender_id', 'content')


@admin.register(LeoxurTask)
class LeoxurTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'creator_id', 'assignee_id', 'created_at')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('title', 'description', 'creator_id', 'assignee_id')

