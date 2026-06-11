from django.contrib import admin
from ntfcs.models import Notificacion

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    class Media:
        pass
        # js = ('js/notificacion_admin.js',)
