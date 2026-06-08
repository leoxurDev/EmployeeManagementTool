import json
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import (
    Employee, DepartmentOption, AvatarEmoji, AvatarColor, AppLayoutBlock,
    AssignmentGroup, SupportEngineer, SupportTicket, TicketActivity, EmployeeSupportPermission
)


class EmployeePINCodeTests(TestCase):
    def setUp(self):
        self.dept = DepartmentOption.objects.create(emoji="💻", name="Engineering", order=1)
        self.emoji = AvatarEmoji.objects.create(emoji="💼", name="Briefcase", order=1)
        self.color = AvatarColor.objects.create(hex_code="#A0C4FF", name="Pastel Blue", order=1)
        
        self.employee = Employee.objects.create(
            first_name="Alice",
            last_name="Smith",
            department="Engineering",
            avatar_emoji="💼",
            avatar_color="#A0C4FF",
            pin_code="1234"
        )

    def test_valid_pin_code(self):
        self.employee.full_clean()
        
        self.employee.pin_code = "9876"
        self.employee.full_clean()  # Should not raise ValidationError

    def test_invalid_pin_code_length(self):
        self.employee.pin_code = "123"
        with self.assertRaises(ValidationError):
            self.employee.full_clean()

        self.employee.pin_code = "12345"
        with self.assertRaises(ValidationError):
            self.employee.full_clean()

    def test_invalid_pin_code_chars(self):
        self.employee.pin_code = "abcd"
        with self.assertRaises(ValidationError):
            self.employee.full_clean()

        self.employee.pin_code = "12a4"
        with self.assertRaises(ValidationError):
            self.employee.full_clean()


class EmployeePINVerifyAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.employee = Employee.objects.create(
            first_name="Alice",
            last_name="Smith",
            department="Engineering",
            avatar_emoji="💼",
            avatar_color="#A0C4FF",
            pin_code="1234"
        )

    def test_verify_pin_success(self):
        url = reverse('verify_pin')
        response = self.client.post(url, {
            'student_id': self.employee.id,
            'pin_code': '1234'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

    def test_verify_pin_failure(self):
        url = reverse('verify_pin')
        response = self.client.post(url, {
            'student_id': self.employee.id,
            'pin_code': '1111'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    def test_verify_pin_non_existent_employee(self):
        url = reverse('verify_pin')
        response = self.client.post(url, {
            'student_id': 99999,
            'pin_code': '1234'
        })
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data['success'])


class ManagerAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.manager_user = User.objects.create_user(
            username='teacher_test',
            email='test@company.com',
            password='testpassword123'
        )
        self.dept = DepartmentOption.objects.create(emoji="💻", name="Engineering", order=1)
        self.employee = Employee.objects.create(
            first_name="Bob",
            last_name="Johnson",
            department="Engineering",
            avatar_emoji="💼",
            avatar_color="#CAFFBF",
            pin_code="1002"
        )

    def test_unauthenticated_redirect(self):
        url = reverse('teacher_dashboard')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('teacher_login') + f"?next={url}")

    def test_manager_login_success(self):
        url = reverse('teacher_login')
        response = self.client.post(url, {
            'username': 'teacher_test',
            'password': 'testpassword123'
        })
        self.assertRedirects(response, reverse('teacher_dashboard'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_manager_login_failure(self):
        url = reverse('teacher_login')
        response = self.client.post(url, {
            'username': 'teacher_test',
            'password': 'wrong_password'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_manager_registration(self):
        url = reverse('teacher_register')
        response = self.client.post(url, {
            'username': 'new_teacher',
            'password1': 'newpassword123',
            'password2': 'newpassword123'
        })
        self.assertRedirects(response, reverse('teacher_dashboard'))
        self.assertTrue(User.objects.filter(username='new_teacher').exists())

    def test_manager_logout(self):
        self.client.login(username='teacher_test', password='testpassword123')
        self.assertTrue(self.client.session.keys())
        
        url = reverse('teacher_logout')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('student_grid'))
        
        dashboard_url = reverse('teacher_dashboard')
        dashboard_response = self.client.get(dashboard_url)
        self.assertRedirects(dashboard_response, reverse('teacher_login') + f"?next={dashboard_url}")

    def test_unified_login_context(self):
        url = reverse('unified_login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('students', response.context)
        self.assertIn('classrooms', response.context)


class DeveloperCustomizerTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='admin_test',
            email='admin@company.com',
            password='adminpassword123',
            is_staff=True,
            is_superuser=True
        )
        self.regular_user = User.objects.create_user(
            username='teacher_non_admin',
            email='manager@company.com',
            password='password123'
        )

    def test_developer_page_unauthenticated_redirect(self):
        url = reverse('admin_developer_page')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('teacher_login') + f"?next={url}")

    def test_developer_page_non_staff_denied(self):
        self.client.login(username='teacher_non_admin', password='password123')
        url = reverse('admin_developer_page')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('teacher_dashboard'))

    def test_developer_page_staff_success(self):
        self.client.login(username='admin_test', password='adminpassword123')
        url = reverse('admin_developer_page')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('layout_blocks', response.context)
        self.assertEqual(len(response.context['layout_blocks']), 4)

    def test_save_layout_api(self):
        self.client.login(username='admin_test', password='adminpassword123')
        self.client.get(reverse('admin_developer_page'))
        
        url = reverse('save_layout')
        payload = {
            'blocks': [
                {'id': 'stats_banner', 'order': 1, 'is_visible': False},
                {'id': 'header', 'order': 2, 'is_visible': True},
                {'id': 'classroom_tabs', 'order': 3, 'is_visible': True},
                {'id': 'student_grid', 'order': 4, 'is_visible': True}
            ]
        }
        response = self.client.post(
            url, 
            data=json.dumps(payload), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        block = AppLayoutBlock.objects.get(block_id='stats_banner')
        self.assertEqual(block.order, 1)
        self.assertFalse(block.is_visible)

    def test_ai_chat_command_fallback(self):
        self.client.login(username='admin_test', password='adminpassword123')
        self.client.get(reverse('admin_developer_page'))
        
        url = reverse('ai_chat_command')
        payload = {
            'message': 'hide stats banner',
            'api_key': ''
        }
        response = self.client.post(
            url, 
            data=json.dumps(payload), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertTrue(res_json['success'])
        self.assertEqual(res_json['action'], 'hide')
        self.assertEqual(res_json['block'], 'stats_banner')
        self.assertFalse(AppLayoutBlock.objects.get(block_id='stats_banner').is_visible)


class TechSupportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.group_l2 = AssignmentGroup.objects.create(name="L2 Team", description="Tier 2")
        self.group_l3 = AssignmentGroup.objects.create(name="L3 Team", description="Tier 3")
        
        self.eng_spock = SupportEngineer.objects.create(name="Spock", email="spock@vulcan.com")
        self.eng_spock.groups.add(self.group_l2)
        self.eng_data = SupportEngineer.objects.create(name="Data", email="data@enterprise.com")
        self.eng_data.groups.add(self.group_l3)

        self.user = User.objects.create_user(username='test_teacher', password='password123', email='manager@company.com')
        EmployeeSupportPermission.objects.create(user=self.user, can_raise_tickets=True)
        self.client.login(username='test_teacher', password='password123')

    def test_client_create_ticket_success(self):
        url = reverse('support_home')
        response = self.client.post(url, {
            'caller': 'Manager Jenkins',
            'subject': 'Kiosk display frozen',
            'description': 'The check-in kiosk tablet screen is completely frozen.',
            'priority': 'moderate'
        })
        ticket = SupportTicket.objects.filter(caller='Manager Jenkins').first()
        self.assertIsNotNone(ticket)
        self.assertRedirects(response, reverse('support_ticket_view', kwargs={'number': ticket.number}))
        
        comment = ticket.activities.filter(activity_type='customer_comment').first()
        self.assertIsNotNone(comment)
        self.assertIn("created successfully", comment.content)

    def test_ticket_number_generation(self):
        t1 = SupportTicket.objects.create(
            caller="Manager Bob",
            subject="Test 1",
            description="Test description 1"
        )
        self.assertTrue(t1.number.startswith("TKT"))
        t2 = SupportTicket.objects.create(
            caller="Manager Bob",
            subject="Test 2",
            description="Test description 2"
        )
        self.assertTrue(t2.number.startswith("TKT"))
        n1 = int(t1.number[3:])
        n2 = int(t2.number[3:])
        self.assertEqual(n2, n1 + 1)

    def test_client_comments_visible_work_notes_hidden(self):
        ticket = SupportTicket.objects.create(
            caller="Employee Alice",
            subject="PIN issue",
            description="PIN code does not work"
        )
        TicketActivity.objects.create(
            ticket=ticket,
            activity_type='work_note',
            author='Spock',
            content='This is a secret internal work note.'
        )
        TicketActivity.objects.create(
            ticket=ticket,
            activity_type='customer_comment',
            author='Spock',
            content='This is a message visible to the customer.'
        )
        
        client_url = reverse('support_ticket_view', kwargs={'number': ticket.number})
        response = self.client.get(client_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This is a message visible to the customer.')
        self.assertNotContains(response, 'This is a secret internal work note.')

    def test_engineer_view_displays_both(self):
        session = self.client.session
        session['engineer_id'] = self.eng_spock.pk
        session.save()

        ticket = SupportTicket.objects.create(
            caller="Employee Alice",
            subject="PIN issue",
            description="PIN code does not work"
        )
        TicketActivity.objects.create(
            ticket=ticket,
            activity_type='work_note',
            author='Spock',
            content='Internal detail note.'
        )
        TicketActivity.objects.create(
            ticket=ticket,
            activity_type='customer_comment',
            author='Spock',
            content='Visible customer reply.'
        )
        
        eng_url = reverse('engineer_ticket_detail', kwargs={'number': ticket.number})
        response = self.client.get(eng_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Internal detail note.')
        self.assertContains(response, 'Visible customer reply.')

    def test_engineer_multiple_groups(self):
        eng = SupportEngineer.objects.create(name="Kirk", email="kirk@enterprise.com")
        eng.groups.add(self.group_l2)
        eng.groups.add(self.group_l3)
        self.assertEqual(eng.groups.count(), 2)
        self.assertIn(self.group_l2, eng.groups.all())
        self.assertIn(self.group_l3, eng.groups.all())

    def test_sla_calculations(self):
        ticket = SupportTicket.objects.create(
            caller="Manager Jenny",
            subject="Urgent issue",
            description="The internet connection is completely down.",
            priority="critical"
        )
        sla_info = ticket.get_sla_status()
        self.assertEqual(sla_info['status'], 'active')
        self.assertIn('SLA: Active', sla_info['label'])
        self.assertIn('left', sla_info['label'])
        
        ticket.priority = 'moderate'
        ticket.save()
        sla_info = ticket.get_sla_status()
        self.assertIn('left', sla_info['label'])
        
        ticket.state = 'resolved'
        ticket.save()
        sla_info = ticket.get_sla_status()
        self.assertEqual(sla_info['status'], 'met')
        self.assertEqual(sla_info['label'], 'SLA: Met')

    def test_identity_manager_loads(self):
        session = self.client.session
        session['engineer_id'] = self.eng_spock.pk
        session.save()

        url = reverse('identity_manager')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Identity & Access Manager')
        self.assertContains(response, 'test_teacher')
        self.assertContains(response, 'Spock')

    def test_identity_manager_toggle_teacher(self):
        session = self.client.session
        session['engineer_id'] = self.eng_spock.pk
        session.save()

        perm = EmployeeSupportPermission.objects.get(user=self.user)
        self.assertTrue(perm.can_raise_tickets)

        url = reverse('identity_manager')
        response = self.client.post(url, {
            'action': 'toggle_teacher_permission',
            'user_id': self.user.pk
        })
        self.assertRedirects(response, reverse('identity_manager'))
        
        perm.refresh_from_db()
        self.assertFalse(perm.can_raise_tickets)

    def test_identity_manager_update_engineer_groups(self):
        session = self.client.session
        session['engineer_id'] = self.eng_spock.pk
        session.save()

        self.assertEqual(self.eng_spock.groups.count(), 1)
        self.assertIn(self.group_l2, self.eng_spock.groups.all())

        url = reverse('identity_manager')
        response = self.client.post(url, {
            'action': 'update_engineer_groups',
            'engineer_id': self.eng_spock.pk,
            'groups': [self.group_l2.pk, self.group_l3.pk]
        })
        self.assertRedirects(response, reverse('identity_manager'))
        
        self.eng_spock.refresh_from_db()
        self.assertEqual(self.eng_spock.groups.count(), 2)
        self.assertIn(self.group_l3, self.eng_spock.groups.all())

    def test_identity_manager_toggle_staff(self):
        session = self.client.session
        session['engineer_id'] = self.eng_spock.pk
        session.save()

        self.assertFalse(self.user.is_staff)

        url = reverse('identity_manager')
        response = self.client.post(url, {
            'action': 'toggle_staff_status',
            'user_id': self.user.pk
        })
        self.assertRedirects(response, reverse('identity_manager'))
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_staff)
