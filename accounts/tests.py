import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

User = get_user_model()
PASSWORD = 'Str0ngPass!77'


def make_user(username='juan', role=User.Role.PATIENT, email=None, **extra):
    return User.objects.create_user(
        username=username, email=email or f'{username}@example.com',
        password=PASSWORD, role=role, **extra,
    )


def image_file(name='me.png', size=(20, 20)):
    buf = io.BytesIO()
    Image.new('RGB', size, 'teal').save(buf, format='PNG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')


class RegistrationTests(TestCase):
    data = {
        'username': 'maria', 'first_name': 'Maria', 'last_name': 'Santos',
        'email': 'maria@example.com', 'password1': PASSWORD, 'password2': PASSWORD,
    }

    def test_successful_registration_hashes_password_and_sets_patient_role(self):
        response = self.client.post(reverse('register'), self.data, follow=True)
        self.assertRedirects(response, reverse('login'))
        self.assertContains(response, 'Your account was created successfully')
        user = User.objects.get(username='maria')
        self.assertEqual(user.role, User.Role.PATIENT)
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.password.startswith('pbkdf2_'))
        self.assertTrue(user.check_password(PASSWORD))

    def test_role_cannot_be_chosen_by_the_visitor(self):
        self.client.post(reverse('register'), {**self.data, 'role': 'BILLING_STAFF'})
        self.assertEqual(User.objects.get(username='maria').role, User.Role.PATIENT)

    def test_required_fields(self):
        response = self.client.post(reverse('register'), {})
        for field in ('username', 'first_name', 'last_name', 'email', 'password1', 'password2'):
            self.assertFormError(response.context['form'], field, 'This field is required.')
        self.assertContains(response, 'Registration failed')

    def test_invalid_email_format(self):
        response = self.client.post(reverse('register'), {**self.data, 'email': 'not-an-email'})
        self.assertFormError(response.context['form'], 'email', 'Enter a valid email address.')
        self.assertFalse(User.objects.filter(username='maria').exists())

    def test_username_must_be_unique(self):
        make_user('maria', email='other@example.com')
        response = self.client.post(reverse('register'), self.data)
        self.assertIn('username', response.context['form'].errors)

    def test_email_must_be_unique_ignoring_case(self):
        make_user('someone', email='maria@example.com')
        response = self.client.post(reverse('register'), {**self.data, 'email': 'MARIA@example.com'})
        self.assertFormError(response.context['form'], 'email', 'An account with this email address already exists.')

    def test_passwords_must_match(self):
        response = self.client.post(reverse('register'), {**self.data, 'password2': 'Different123!'})
        self.assertIn('password2', response.context['form'].errors)
        self.assertFalse(User.objects.filter(username='maria').exists())

    def test_logged_in_user_is_redirected_away_from_register(self):
        self.client.force_login(make_user())
        self.assertRedirects(self.client.get(reverse('register')), reverse('dashboard'),
                             fetch_redirect_response=False)


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_login_with_valid_credentials_goes_to_role_dashboard(self):
        response = self.client.post(reverse('login'), {'username': 'juan', 'password': PASSWORD}, follow=True)
        self.assertRedirects(response, reverse('patient_dashboard'))
        self.assertContains(response, 'Welcome back')

    def test_login_with_invalid_credentials_shows_error(self):
        response = self.client.post(reverse('login'), {'username': 'juan', 'password': 'wrong'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login failed')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_ends_session(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('logout'), follow=True)
        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertContains(response, 'You have been logged out')

    def test_protected_pages_redirect_logged_out_users_to_login(self):
        for name in ('dashboard', 'patient_dashboard', 'staff_dashboard', 'profile', 'profile_edit'):
            url = reverse(name)
            response = self.client.get(url)
            self.assertRedirects(response, f"{reverse('login')}?next={url}", msg_prefix=name)


class RoleDashboardTests(TestCase):
    def setUp(self):
        self.patient = make_user('juan')
        self.staff = make_user('ana', role=User.Role.BILLING_STAFF)

    def test_patient_is_sent_to_patient_dashboard(self):
        self.client.force_login(self.patient)
        self.assertRedirects(self.client.get(reverse('dashboard')), reverse('patient_dashboard'))

    def test_staff_is_sent_to_staff_dashboard(self):
        self.client.force_login(self.staff)
        self.assertRedirects(self.client.get(reverse('dashboard')), reverse('staff_dashboard'))

    def test_each_dashboard_shows_role_specific_content(self):
        self.client.force_login(self.patient)
        self.assertContains(self.client.get(reverse('patient_dashboard')), 'Patient Dashboard')
        self.client.force_login(self.staff)
        response = self.client.get(reverse('staff_dashboard'))
        self.assertContains(response, 'Billing Staff Dashboard')
        self.assertContains(response, 'Patient accounts')

    def test_navigation_matches_role(self):
        self.client.force_login(self.patient)
        self.assertContains(self.client.get(reverse('patient_dashboard')), reverse('patient_dashboard'))
        self.assertNotContains(self.client.get(reverse('patient_dashboard')), reverse('staff_dashboard'))
        self.client.force_login(self.staff)
        self.assertNotContains(self.client.get(reverse('staff_dashboard')), reverse('patient_dashboard'))

    def test_patient_cannot_open_staff_dashboard(self):
        self.client.force_login(self.patient)
        self.assertEqual(self.client.get(reverse('staff_dashboard')).status_code, 403)

    def test_staff_cannot_open_patient_dashboard(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse('patient_dashboard')).status_code, 403)


class ProfileTests(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, True)
        self.user = make_user('juan', first_name='Juan', last_name='Cruz')
        self.other = make_user('maria', first_name='Maria', last_name='Santos')
        self.client.force_login(self.user)

    def post_edit(self, **overrides):
        data = {'first_name': 'Juan', 'last_name': 'Cruz', 'email': 'juan@example.com', 'contact_number': ''}
        data.update(overrides)
        return self.client.post(reverse('profile_edit'), data)

    def test_profile_shows_own_information(self):
        response = self.client.get(reverse('profile'))
        self.assertContains(response, 'juan@example.com')
        self.assertNotContains(response, 'maria@example.com')

    def test_update_profile_details(self):
        response = self.post_edit(first_name='Juanito', email='new@example.com', contact_number='+63 912 345 6789')
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertEqual((self.user.first_name, self.user.email, self.user.contact_number),
                         ('Juanito', 'new@example.com', '+63 912 345 6789'))

    def test_success_message_is_shown(self):
        response = self.client.post(reverse('profile_edit'), {
            'first_name': 'Juan', 'last_name': 'Cruz', 'email': 'juan@example.com'}, follow=True)
        self.assertContains(response, 'Your profile was updated successfully')

    def test_email_cannot_duplicate_another_users_email(self):
        response = self.post_edit(email='maria@example.com')
        self.assertFormError(response.context['form'], 'email', 'An account with this email address already exists.')
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'juan@example.com')

    def test_invalid_contact_number_rejected(self):
        response = self.post_edit(contact_number='abc')
        self.assertIn('contact_number', response.context['form'].errors)

    def test_required_name_fields(self):
        response = self.post_edit(first_name='', last_name='')
        self.assertIn('first_name', response.context['form'].errors)
        self.assertIn('last_name', response.context['form'].errors)

    def test_edit_only_changes_own_account(self):
        self.post_edit(first_name='Changed')
        self.other.refresh_from_db()
        self.assertEqual(self.other.first_name, 'Maria')

    def test_role_cannot_be_changed_through_profile_form(self):
        self.post_edit(role='BILLING_STAFF')
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, User.Role.PATIENT)

    def test_upload_profile_photo(self):
        with override_settings(MEDIA_ROOT=self.media):
            response = self.client.post(reverse('profile_edit'), {
                'first_name': 'Juan', 'last_name': 'Cruz', 'email': 'juan@example.com',
                'contact_number': '', 'profile_photo': image_file(),
            })
            self.assertRedirects(response, reverse('profile'))
            self.user.refresh_from_db()
            self.assertTrue(self.user.profile_photo.name.startswith('profile_photos/'))

    def test_non_image_upload_rejected(self):
        bad = SimpleUploadedFile('x.txt', b'not an image', content_type='text/plain')
        with override_settings(MEDIA_ROOT=self.media):
            response = self.client.post(reverse('profile_edit'), {
                'first_name': 'Juan', 'last_name': 'Cruz', 'email': 'juan@example.com',
                'contact_number': '', 'profile_photo': bad,
            })
        self.assertIn('profile_photo', response.context['form'].errors)

    def test_no_url_exposes_another_users_profile(self):
        # Profile URLs take no user id; /profile/ always shows the logged-in user.
        self.client.force_login(self.other)
        self.assertContains(self.client.get(reverse('profile')), 'maria@example.com')
        self.assertNotContains(self.client.get(reverse('profile')), 'juan@example.com')
