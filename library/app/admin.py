from django.contrib import admin
from .models import Role, User, Resource, Genre, Borrowing, Fine

admin.site.register(Role)
admin.site.register(User)
admin.site.register(Resource)
admin.site.register(Genre)
admin.site.register(Borrowing)
admin.site.register(Fine)