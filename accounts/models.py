from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import RegexValidator
from django.db import models


class CustomUserManager(UserManager):
    """Superusers created with `createsuperuser` are billing staff."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'BILLING_STAFF')
        return super().create_superuser(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Login account for both patients and billing staff."""

    class Role(models.TextChoices):
        PATIENT = 'PATIENT', 'Patient'
        BILLING_STAFF = 'BILLING_STAFF', 'Billing Staff'

    email = models.EmailField('email address', unique=True)
    role = models.CharField(max_length=15, choices=Role.choices, default=Role.PATIENT)
    contact_number = models.CharField(
        max_length=20, blank=True,
        validators=[RegexValidator(r'^\+?[0-9\s\-]{7,20}$', 'Enter a valid contact number (digits, spaces, dashes, optional leading +).')],
    )
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT

    @property
    def is_billing_staff(self):
        return self.role == self.Role.BILLING_STAFF
