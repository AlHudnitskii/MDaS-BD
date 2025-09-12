from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
    UserChangeForm,
)

from .models import User, UserTimezone, UserNote, UserGroup


class UserLoginForm(AuthenticationForm):
    """
    Custom form for user login.
    """
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        """
        Meta class for UserLoginForm.
        """
        model = User
        fields = ["username", "password"]


class UserRegistrationForm(UserCreationForm):
    """
    Custom form for new user registration.
    """
    first_name = forms.CharField()
    last_name = forms.CharField()
    username = forms.CharField()
    email = forms.CharField(widget=forms.EmailInput)

    class Meta:
        """
        Meta class for UserRegistrationForm.
        """
        model = User
        fields = ("first_name", "last_name", "username", "email")


class ProfileForm(UserChangeForm):
    """
    Custom form for editing user profile.
    """
    image = forms.ImageField(required=False)
    first_name = forms.CharField()
    last_name = forms.CharField()
    username = forms.CharField()
    email = forms.CharField(widget=forms.EmailInput)

    class Meta:
        """
        Meta class for ProfileForm.
        """
        model = User
        fields = ("image", "first_name", "last_name", "username", "email")


class UserTimezoneForm(forms.ModelForm):
    """
    Form for selecting user timezone.
    """
    class Meta:
        """
        Meta class for UserTimezoneForm.
        """
        model = UserTimezone
        fields = ["timezone"]


class UserNoteForm(forms.ModelForm):
    """
    Form for creating and editing user notes.
    """
    class Meta:
        """
        Meta class for UserNoteForm.
        """
        model = UserNote
        fields = ["title", "content"]


class UserGroupForm(forms.ModelForm):
    """
    Form for creating and editing user groups.
    """
    class Meta:
        """
        Meta class for UserGroupForm.
        """
        model = UserGroup
        fields = ["name", "description"]