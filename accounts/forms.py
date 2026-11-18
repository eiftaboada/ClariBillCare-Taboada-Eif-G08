from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.models import CustomUser


class RegistrationForm(UserCreationForm):
    """Public sign-up form. Every field is required, the email must be valid and
    unique, the username must be unique and both passwords must match."""

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField(max_length=254)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email address already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = CustomUser.Role.PATIENT  
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """Lets a logged-in user update their own profile details."""

    MAX_PHOTO_SIZE = 2 * 1024 * 1024  

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField(max_length=254)

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'contact_number', 'profile_photo')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('An account with this email address already exists.')
        return email

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo and hasattr(photo, 'size') and photo.size > self.MAX_PHOTO_SIZE:
            raise forms.ValidationError('The photo must be 2 MB or smaller.')
        return photo
