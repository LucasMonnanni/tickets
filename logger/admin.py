from django.contrib import admin
from .models import ErrorLog

# Register your models here.
@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    pass