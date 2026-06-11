from django.contrib import admin
from django.contrib.auth.models import Group
from django_reverse_admin import ReverseModelAdmin
from tkts.models import Ticket, Cliente, Motivo, OC, Acceso, CambioDeEquipos
from .forms import GroupAdminForm
from .resources import *
from import_export.admin import ImportExportMixin, ExportMixin


@admin.register(Ticket)
class TicketAdmin(ExportMixin, ReverseModelAdmin):
	resource_class = TicketResource
	readonly_fields = ['inicio']
	list_filter = ('_estado_id', 'motivo', 'cliente', 'oc__contratista', 'usuario_asignado', 'inicio')
	fields = (('nombre', 'email', 'telefono'), '_estado_id', 'sitio', 'inicio', ('cliente', 'motivo'), 'problema', 'solucion', ('programada', 'cierre'), 'observaciones')
	inline_type = 'stacked'
	inline_reverse = ['oc', 'acceso', 'cambio_de_equipos']

# Unregister the original Group admin.
admin.site.unregister(Group)

# Create a new Group admin.
class GroupAdmin(admin.ModelAdmin):
	# Use our custom form.
	form = GroupAdminForm
	# Filter permissions horizontal as well.
	filter_horizontal = ['permissions']

# Register the new Group ModelAdmin.
admin.site.register(Group, GroupAdmin)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
	model = Cliente
	list_display = ('nombre', 'visible')
	list_editable = ('visible',)

@admin.register(Motivo)
class MotivoAdmin(admin.ModelAdmin):
	model = Motivo
	list_display = ('nombre', 'visible')
	list_editable = ('visible',)
