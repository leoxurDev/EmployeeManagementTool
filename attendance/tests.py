import json
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import (
    Employee, DepartmentOption, AvatarEmoji, AvatarColor, AppLayoutBlock,
    AssignmentGroup, SupportEngineer, SupportTicket, TicketActivity, EmployeeSupportPermission,
    LeoxurTask
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
        admin = User.objects.create_superuser(
            username='admin_register_test',
            email='admin_reg@company.com',
            password='adminpassword123'
        )
        self.client.login(username='admin_register_test', password='adminpassword123')
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

    def test_manager_login_redirect_next_valid(self):
        url = reverse('teacher_login')
        next_url = reverse('admin_developer_page')
        response = self.client.post(f"{url}?next={next_url}", {
            'username': 'teacher_test',
            'password': 'testpassword123'
        })
        self.assertRedirects(response, next_url, fetch_redirect_response=False)

    def test_manager_login_redirect_next_invalid_host(self):
        url = reverse('teacher_login')
        next_url = "http://malicious.com/stolen"
        response = self.client.post(f"{url}?next={next_url}", {
            'username': 'teacher_test',
            'password': 'testpassword123'
        })
        self.assertRedirects(response, reverse('teacher_dashboard'))


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

    def test_engineer_login_redirect_next_valid(self):
        self.eng_spock.password = "engineer123"
        self.eng_spock.save()
        url = reverse('engineer_login')
        next_url = reverse('identity_manager')
        response = self.client.post(f"{url}?next={next_url}", {
            'email': self.eng_spock.email,
            'password': 'engineer123'
        })
        self.assertRedirects(response, next_url, fetch_redirect_response=False)

    def test_engineer_login_redirect_next_invalid_host(self):
        self.eng_spock.password = "engineer123"
        self.eng_spock.save()
        url = reverse('engineer_login')
        next_url = "http://malicious.com/stolen"
        response = self.client.post(f"{url}?next={next_url}", {
            'email': self.eng_spock.email,
            'password': 'engineer123'
        })
        self.assertRedirects(response, reverse('engineer_dashboard'), fetch_redirect_response=False)

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


class LeoxurCommTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = DepartmentOption.objects.create(emoji="💻", name="Engineering", order=1)
        self.employee = Employee.objects.create(
            first_name="Alice",
            last_name="Smith",
            department="Engineering",
            avatar_emoji="💼",
            avatar_color="#A0C4FF",
            pin_code="1001"
        )
        self.engineer = SupportEngineer.objects.create(
            name="Spock",
            email="spock@vulcan.com",
            password="engineerpassword123"
        )
        self.manager_user = User.objects.create_user(
            username='manager_test',
            email='manager@leoxur.com',
            password='managerpassword123'
        )

    def test_auth_manager_success(self):
        url = reverse('leoxur_comm_auth')
        # Simulate active Django login authentication check
        self.client.login(username='manager_test', password='managerpassword123')
        payload = {
            'user_id': f'manager_{self.manager_user.id}',
            'secret': 'managerpassword123'
        }
        response = self.client.post(url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

    def test_auth_employee_success(self):
        url = reverse('leoxur_comm_auth')
        payload = {
            'user_id': f'employee_{self.employee.id}',
            'secret': '1001'
        }
        response = self.client.post(url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(self.client.session['leoxur_user_id'], f'employee_{self.employee.id}')

    def test_auth_employee_wrong_pin(self):
        url = reverse('leoxur_comm_auth')
        payload = {
            'user_id': f'employee_{self.employee.id}',
            'secret': '9999'
        }
        response = self.client.post(url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertNotIn('leoxur_user_id', self.client.session)

    def test_auth_engineer_success(self):
        url = reverse('leoxur_comm_auth')
        payload = {
            'user_id': f'engineer_{self.engineer.id}',
            'secret': 'engineerpassword123'
        }
        response = self.client.post(url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(self.client.session['leoxur_user_id'], f'engineer_{self.engineer.id}')

    def test_auth_unauthorized_comm_data_access(self):
        url = reverse('leoxur_comm_data')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_send_email_and_mark_as_read(self):
        # Authenticate employee
        session = self.client.session
        session['leoxur_user_id'] = f'employee_{self.employee.id}'
        session.save()

        # Send email to engineer
        send_url = reverse('leoxur_send_email')
        payload = {
            'receiver_id': f'engineer_{self.engineer.id}',
            'subject': 'Support Request',
            'body': 'My computer won\'t start.'
        }
        response = self.client.post(send_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

        # Authenticate engineer to read the email
        session['leoxur_user_id'] = f'engineer_{self.engineer.id}'
        session.save()

        # Fetch data
        data_url = reverse('leoxur_comm_data')
        response = self.client.get(data_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['emails']), 1)
        email = data['emails'][0]
        self.assertFalse(email['is_read'])

        # Mark as read
        read_url = reverse('leoxur_read_email')
        read_payload = {'email_id': email['id']}
        response = self.client.post(read_url, json.dumps(read_payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

        # Check update in data API
        response = self.client.get(data_url)
        email = response.json()['emails'][0]
        self.assertTrue(email['is_read'])

    def test_chat_replies_quoting(self):
        session = self.client.session
        session['leoxur_user_id'] = f'employee_{self.employee.id}'
        session.save()

        # Send first message
        send_url = reverse('leoxur_send_chat')
        payload1 = {
            'room_id': 'general',
            'content': 'Hello organization!'
        }
        response1 = self.client.post(send_url, json.dumps(payload1), content_type='application/json')
        self.assertEqual(response1.status_code, 200)
        msg_id1 = response1.json()['message_id']

        # Send reply message quoting the first one
        payload2 = {
            'room_id': 'general',
            'content': 'Hi Alice!',
            'parent_id': msg_id1
        }
        response2 = self.client.post(send_url, json.dumps(payload2), content_type='application/json')
        self.assertEqual(response2.status_code, 200)

        # Retrieve messages and verify reply link and quote payload
        data_url = reverse('leoxur_comm_data')
        response3 = self.client.get(data_url)
        messages = response3.json()['messages']
        self.assertEqual(len(messages), 2)
        
        reply_msg = messages[1]
        self.assertEqual(reply_msg['parent_id'], msg_id1)
        self.assertEqual(reply_msg['parent_sender_name'], 'Alice Smith (Employee - Engineering)')
        self.assertEqual(reply_msg['parent_content'], 'Hello organization!')

    def test_private_managers_channel_security(self):
        # Authenticate employee
        session = self.client.session
        session['leoxur_user_id'] = f'employee_{self.employee.id}'
        session.save()

        # Try to send a message to managers channel - should be blocked
        send_url = reverse('leoxur_send_chat')
        payload = {
            'room_id': 'managers',
            'content': 'Secret admin stuff'
        }
        response = self.client.post(send_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['success'])

        # Authenticate manager
        session['leoxur_user_id'] = f'manager_{self.manager_user.id}'
        session.save()

        # Manager sends to managers channel - should succeed
        response = self.client.post(send_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

    def test_leoxur_workspace_logout_loop_prevention(self):
        # 1. Login Django manager
        self.client.login(username='manager_test', password='managerpassword123')
        
        # 2. Access dashboard - should auto-login workspace
        url = reverse('leoxur_comm_dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session.get('leoxur_user_id'), f'manager_{self.manager_user.id}')
        
        # 3. Explicitly logout from workspace
        logout_url = reverse('leoxur_comm_logout')
        logout_response = self.client.post(logout_url)
        self.assertEqual(logout_response.status_code, 200)
        self.assertNotIn('leoxur_user_id', self.client.session)
        self.assertTrue(self.client.session.get('leoxur_logged_out'))
        
        # 4. Access dashboard again - should NOT auto-login because of manual logout flag
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, 200)
        self.assertNotIn('leoxur_user_id', self.client.session)
        
        # 5. Authenticating again should clear manual logout flag
        auth_url = reverse('leoxur_comm_auth')
        payload = {
            'user_id': f'manager_{self.manager_user.id}',
            'secret': 'managerpassword123'
        }
        auth_response = self.client.post(auth_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(auth_response.status_code, 200)
        self.assertFalse(self.client.session.get('leoxur_logged_out'))
        self.assertEqual(self.client.session.get('leoxur_user_id'), f'manager_{self.manager_user.id}')


class LeoxurWorkspaceTaskTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = DepartmentOption.objects.create(emoji="💻", name="Engineering", order=1)
        self.employee = Employee.objects.create(
            first_name="Alice",
            last_name="Smith",
            department="Engineering",
            avatar_emoji="👤",
            avatar_color="#6B7280"
        )
        self.manager_user = User.objects.create_user(
            username='manager_test',
            email='manager@company.com',
            password='testpassword123'
        )

    def test_task_crud_operations(self):
        # Authenticate manager
        session = self.client.session
        session['leoxur_user_id'] = f'manager_{self.manager_user.id}'
        session.save()

        # Create Task
        create_url = reverse('leoxur_create_task')
        payload = {
            'title': 'Test Task',
            'description': 'Description for test task',
            'priority': 'high',
            'status': 'backlog',
            'assignee_id': f'employee_{self.employee.id}'
        }
        response = self.client.post(create_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        task_id = data['task_id']

        # Verify task is created in DB
        task = LeoxurTask.objects.get(id=task_id)
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.creator_id, f'manager_{self.manager_user.id}')
        self.assertEqual(task.assignee_id, f'employee_{self.employee.id}')

        # Update Task Status and Priority (authenticate as assignee)
        session = self.client.session
        session['leoxur_user_id'] = f'employee_{self.employee.id}'
        session.save()

        update_url = reverse('leoxur_update_task')
        update_payload = {
            'task_id': task_id,
            'status': 'in_progress',
            'priority': 'highest',
            'title': 'Updated Title'
        }
        response = self.client.post(update_url, json.dumps(update_payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

        # Verify task is updated in DB
        task.refresh_from_db()
        self.assertEqual(task.status, 'in_progress')
        self.assertEqual(task.priority, 'highest')
        self.assertEqual(task.title, 'Updated Title')

        # Retrieve tasks via comm data endpoint
        data_url = reverse('leoxur_comm_data')
        response = self.client.get(data_url)
        self.assertEqual(response.status_code, 200)
        comm_data = response.json()
        self.assertTrue(comm_data['success'])
        self.assertEqual(len(comm_data['tasks']), 1)
        self.assertEqual(comm_data['tasks'][0]['title'], 'Updated Title')
        self.assertEqual(comm_data['tasks'][0]['assignee']['name'], 'Alice Smith (Employee - Engineering)')

        # Delete Task
        delete_url = reverse('leoxur_delete_task')
        response = self.client.post(delete_url, json.dumps({'task_id': task_id}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertFalse(LeoxurTask.objects.filter(id=task_id).exists())

    def test_task_transition_permissions(self):
        # 1. Create a task assigned to Alice Smith (Employee)
        task = LeoxurTask.objects.create(
            title='Alice Task',
            status='backlog',
            creator_id=f'manager_{self.manager_user.id}',
            assignee_id=f'employee_{self.employee.id}'
        )

        # Create another employee user
        another_employee = Employee.objects.create(
            first_name="Bob",
            last_name="Jones",
            department="Engineering",
            avatar_emoji="👤",
            avatar_color="#CAFFBF"
        )

        # Login as another employee (Bob)
        session = self.client.session
        session['leoxur_user_id'] = f'employee_{another_employee.id}'
        session.save()

        # Try to move Alice's task to in_progress - should fail
        update_url = reverse('leoxur_update_task')
        response = self.client.post(update_url, json.dumps({
            'task_id': task.id,
            'status': 'in_progress'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['success'])

        # Login as the assignee (Alice)
        session['leoxur_user_id'] = f'employee_{self.employee.id}'
        session.save()

        # Try to move task to in_progress - should succeed
        response = self.client.post(update_url, json.dumps({
            'task_id': task.id,
            'status': 'in_progress'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        task.refresh_from_db()
        self.assertEqual(task.status, 'in_progress')

        # Alice moves the task to in_review - should succeed
        response = self.client.post(update_url, json.dumps({
            'task_id': task.id,
            'status': 'in_review'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        task.refresh_from_db()
        self.assertEqual(task.status, 'in_review')

        # Alice tries to move/approve the task to done (from in_review) - should fail
        response = self.client.post(update_url, json.dumps({
            'task_id': task.id,
            'status': 'done'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['success'])

        # Login as Manager
        session['leoxur_user_id'] = f'manager_{self.manager_user.id}'
        session.save()

        # Manager approves the task to done (from in_review) - should succeed
        response = self.client.post(update_url, json.dumps({
            'task_id': task.id,
            'status': 'done'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        task.refresh_from_db()
        self.assertEqual(task.status, 'done')

        # 2. Test unassigned task movement
        unassigned_task = LeoxurTask.objects.create(
            title='Unassigned Task',
            status='backlog',
            creator_id=f'manager_{self.manager_user.id}'
        )

        # Login as Employee (Alice)
        session['leoxur_user_id'] = f'employee_{self.employee.id}'
        session.save()

        # Alice should be able to move unassigned task
        response = self.client.post(update_url, json.dumps({
            'task_id': unassigned_task.id,
            'status': 'in_progress'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        unassigned_task.refresh_from_db()
        self.assertEqual(unassigned_task.status, 'in_progress')

    def test_portal_login_overrides_workspace_profile(self):
        session = self.client.session
        session['leoxur_user_id'] = 'engineer_99'
        session['engineer_id'] = 99
        session.save()

        response = self.client.post(reverse('teacher_login'), {
            'username': self.manager_user.username,
            'password': 'testpassword123'
        })
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.client.session.get('leoxur_user_id'), f'manager_{self.manager_user.id}')
        self.assertFalse(self.client.session.get('leoxur_logged_out'))
        self.assertNotIn('engineer_id', self.client.session)


class DepartmentOptionTests(TestCase):
    def setUp(self):
        self.manager_user = User.objects.create_superuser(
            username='admin_test',
            email='admin_test@company.com',
            password='testpassword123'
        )

    def test_optional_emoji_in_department_option(self):
        # 1. Create a department without emoji
        dept1 = DepartmentOption.objects.create(name="Sales", order=10)
        self.assertIsNone(dept1.emoji)
        self.assertEqual(str(dept1), "Sales")
        self.assertEqual(dept1.display_value, "Sales")

        # 2. Create another department with empty string emoji
        # clean and save should coerce empty string to None
        dept2 = DepartmentOption.objects.create(name="Marketing", emoji="", order=11)
        self.assertIsNone(dept2.emoji)
        self.assertEqual(str(dept2), "Marketing")
        self.assertEqual(dept2.display_value, "Marketing")

        # 3. Create a third department with an actual emoji
        dept3 = DepartmentOption.objects.create(name="HR", emoji="🤝", order=12)
        self.assertEqual(dept3.emoji, "🤝")
        self.assertEqual(str(dept3), "🤝 HR")
        self.assertEqual(dept3.display_value, "🤝 HR")

    def test_ampersand_department_filtering(self):
        # Create department with &
        dept = DepartmentOption.objects.create(name="Sales & Marketing", emoji="📈", order=1)
        
        # Create an employee in it
        employee = Employee.objects.create(
            first_name="Jane",
            last_name="Doe",
            department="Sales & Marketing",
            avatar_emoji="📈",
            avatar_color="#FFADAD"
        )
        
        # Request grid with url encoded classroom parameter
        response = self.client.get(reverse('student_grid') + '?classroom=Sales%20%26%20Marketing')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jane Doe")
        self.assertEqual(response.context['selected_classroom_name'], "Sales & Marketing")


