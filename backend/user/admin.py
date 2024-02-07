from django.contrib import admin
from .models import User


class UserAdmin(admin.ModelAdmin):
    """Регистрация модели `Recipe` для админки."""
    list_display = (
        'email',
        'username',
        'first_name',
        'last_name',
    )
    list_filter = ('email', 'username')


admin.site.register(User, UserAdmin)
