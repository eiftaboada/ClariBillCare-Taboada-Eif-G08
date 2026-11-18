from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView

from accounts.forms import ProfileForm, RegistrationForm


class RegisterView(CreateView):
    """Account registration."""
    form_class = RegistrationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Your account was created successfully. You can now log in.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Registration failed. Please fix the errors below.')
        return super().form_invalid(form)


class LoginView(auth_views.LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Welcome back, {self.request.user.get_short_name() or self.request.user.username}!')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Login failed. Invalid username or password.')
        return super().form_invalid(form)


class LogoutView(auth_views.LogoutView):
    """Ends the session (POST only) and sends the user back to the login page."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, 'You have been logged out.')
        return response


class ProfileView(LoginRequiredMixin, TemplateView):
    """Shows the logged-in user's own profile (there is no user id in the URL,
    so nobody can open another user's profile)."""
    template_name = 'accounts/profile.html'


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Edits the logged-in user's own profile only."""
    form_class = ProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Your profile was updated successfully.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Profile not saved. Please fix the errors below.')
        return super().form_invalid(form)
