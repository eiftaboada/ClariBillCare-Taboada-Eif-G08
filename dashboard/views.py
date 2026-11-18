from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.generic import TemplateView

from accounts.mixins import PatientRequiredMixin, StaffRequiredMixin
from accounts.models import CustomUser


def home(request):
    """Root URL: send visitors to their dashboard (guests go to the login page)."""
    return redirect('dashboard')


@login_required
def dashboard_redirect(request):
    """After login, each user goes to the dashboard of their own role."""
    if request.user.role == CustomUser.Role.BILLING_STAFF:
        return redirect('staff_dashboard')
    return redirect('patient_dashboard')


class PatientDashboardView(PatientRequiredMixin, TemplateView):
    template_name = 'dashboard/patient_dashboard.html'


class StaffDashboardView(StaffRequiredMixin, TemplateView):
    template_name = 'dashboard/staff_dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        patients = CustomUser.objects.filter(role=CustomUser.Role.PATIENT)
        ctx['patient_count'] = patients.count()
        ctx['staff_count'] = CustomUser.objects.filter(role=CustomUser.Role.BILLING_STAFF).count()
        ctx['recent_patients'] = patients.order_by('-date_joined')[:5]
        return ctx
