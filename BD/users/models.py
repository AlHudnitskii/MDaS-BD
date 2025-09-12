import pytz

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings



class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "role"
        
    def __str__(self):
        return self.name    
    
class User(AbstractUser):   
    image = models.ImageField(upload_to="users_image", blank=True, null=True)
    roles = models.ManyToManyField(Role, through="UserRole", related_name="users", blank=True, through_fields=("user", "role"))

    class Meta:
        db_table = "user"

    def __str__(self):
        return self.username
    
    def has_role(self, role_name):
        return self.roles.filter(name=role_name).exists()


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_roles")

    class Meta:
        db_table = "user_role"
        unique_together = ("user", "role")
        
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"


class UserNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notes")
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_note"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class UserTimezone(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="timezone_info")
    timezone = models.CharField(max_length=32, choices=zip(pytz.all_timezones, pytz.all_timezones), default="UTC")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "user_timezone"
    
    def __str__(self):
        return f"{self.user.username} - {self.timezone}"    
    

class LogEntry(models.Model):
    ACTION_CHOICES = [
        ('USER_LOGIN', 'Login'),
        ('USER_LOGOUT', 'Logout'),
        ('USER_REGISTER', 'Registration'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('PROFILE_UPDATE', 'Profile Update'),
        ('ORDER_CREATE', 'Order Creation'),
        ('ORDER_UPDATE', 'Order Update'),
        ('PRODUCT_CREATE', 'Product Creation'),
        ('PRODUCT_UPDATE', 'Product Update'),
        ('PRODUCT_DELETE', 'Product Deletion'),
        ('CATEGORY_CREATE', 'Category Creation'),
        ('CATEGORY_UPDATE', 'Category Update'),
        ('CATEGORY_DELETE', 'Category Deletion'),
        ('USER_MANAGEMENT', 'User Management'),
        ('ROLE_ASSIGNMENT', 'Role Assignment'),
    ]

    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
        ('WARNING', 'Warning'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='log_entries',
    )
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='SUCCESS')
    timestamp = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'log_entry'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['action']),
            models.Index(fields=['status']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.timestamp} - {self.get_action_display()} - {self.user if self.user else 'Anonymous'}"