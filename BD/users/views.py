import logging

from django.shortcuts import render, redirect
from django.contrib import auth, messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch

from orders.models import Order, OrderItem
from .forms import (
    UserLoginForm,
    UserRegistrationForm,
    ProfileForm,
    UserTimezoneForm,
    UserNoteForm,
    UserGroupForm,
)
from .models import UserNote, UserGroup, UserTimezone

logger = logging.getLogger(__name__)


def login(request):
    """Handles user login."""

    logger.info(f"Processing login request from IP: {request.META.get('REMOTE_ADDR')}")
    if request.method == "POST":
        form = UserLoginForm(data=request.POST)
        logger.debug(f"Login form submitted with data: {request.POST}")
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = auth.authenticate(username=username, password=password)
            if user:
                auth.login(request, user)
                logger.info(f"User '{username}' logged in successfully.")
                return HttpResponseRedirect(reverse("main:product_list"))
            else:
                logger.warning(
                    f"Authentication failed for user '{username}' from IP: {request.META.get('REMOTE_ADDR')}"
                )
                messages.error(request, "Invalid username or password")
        else:
            logger.warning(
                f"Invalid login form data from IP: {request.META.get('REMOTE_ADDR')}. Errors: {form.errors}"
            )
            messages.error(request, "Invalid username or password")
    else:
        form = UserLoginForm()
    return render(request, "users/login.html", {"form": form})


def registration(request):
    """Handles user registration."""

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth.login(request, user)
            logger.info(f"User '{user.username}' registered and logged in.")
            return redirect("main:product_list")
        else:
            logger.warning(f"Invalid registration form data. Errors: {form.errors}")
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegistrationForm()
    return render(request, "users/registration.html", {"form": form})


@login_required
def profile(request):
    """Displays and handles user profile updates."""

    if request.method == "POST":
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user)
        timezone_form = UserTimezoneForm(request.POST, instance=request.user.timezone_info)
        note_form = UserNoteForm(request.POST)
        group_form = UserGroupForm(request.POST)

        if profile_form.is_valid() and timezone_form.is_valid():
            profile_form.save()
            timezone_form.save()
            logger.info(f"User '{request.user.username}' updated their profile.")
            messages.success(request, "Profile updated successfully.")
            return redirect("user:profile")


        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.user = request.user
            note.save()
            logger.info(f"User '{request.user.username}' created a new note.")
            messages.success(request, "Note added")
            return redirect(reverse("user:profile"))


        if group_form.is_valid():
            group = group_form.save()
            group.members.add(request.user)
            logger.info(f"User '{request.user.username}' created a new group.")
            messages.success(request, "Group created")
            return redirect(reverse("user:profile"))

    else:
        profile_form = ProfileForm(instance=request.user)
        timezone_form = UserTimezoneForm(instance=request.user.timezone_info)
        note_form = UserNoteForm()
        group_form = UserGroupForm()

    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related(
            Prefetch("items", queryset=OrderItem.objects.select_related("product"))
        )
        .order_by("-id")
    )
    logger.debug(f"Fetched {orders.count()} orders for user '{request.user.username}'.")

    notes = request.user.notes.all().order_by("-created_at")
    logger.debug(f"Fetched {notes.count()} notes for user '{request.user.username}'.")

    groups = request.user.user_groups.all().order_by("name")
    logger.debug(f"Fetched {groups.count()} groups for user '{request.user.username}'.")

    return render(
        request,
        "users/profile.html",
        {
            "form": profile_form,
            "orders": orders,
            "notes": notes,
            "groups": groups,
            "timezone_form": timezone_form,
            "note_form": note_form,
            "group_form": group_form,
        },
    )


def logout(request):
    """Handles user logout."""

    username = request.user.username
    logger.info(f"User '{username}' logged out.")
    auth.logout(request)
    return redirect("main:product_list")