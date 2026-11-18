from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from accounts.models import CustomUser


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Logged-out visitors are sent to the login page; logged-in users with the
    wrong role get a 403 page. Subclasses set `required_role`."""
    required_role = None

    def test_func(self):
        return self.request.user.role == self.required_role


class PatientRequiredMixin(RoleRequiredMixin):
    required_role = CustomUser.Role.PATIENT


class StaffRequiredMixin(RoleRequiredMixin):
    required_role = CustomUser.Role.BILLING_STAFF
