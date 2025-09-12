from django.contrib import admin
from .models import User, UserNote, UserGroup, UserTimezone


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'image')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    readonly_fields = ('date_joined',) 


@admin.register(UserNote)
class UserNoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'updated_at')
    list_filter = ('user', 'created_at', 'updated_at')
    search_fields = ('title', 'content', 'user__username') 
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('members',) 


@admin.register(UserTimezone)
class UserTimezoneAdmin(admin.ModelAdmin):
    list_display = ('user', 'timezone')
    list_filter = ('timezone',)
    search_fields = ('user__username',) 