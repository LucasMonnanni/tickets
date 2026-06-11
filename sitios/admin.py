from django.contrib import admin
from import_export.admin import ExportMixin
from django.forms import ModelForm
from sitios.models import Sitio, Suministro, Celda, Cellowner, Locador, Operador, Titular
from .resources import CeldaResource, SuministroResource, SitioResource

class CeldaAdminInlineForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.id:
            self.fields['owner'].queryset = Cellowner.objects.filter(operador = self.instance.operador)
            self.fields['suministro'].queryset = Suministro.objects.filter(sitio = self.instance.sitio)
        else:
            self.fields['suministro'].queryset = Suministro.objects.none()

class CeldaInline(admin.TabularInline):
    model = Celda
    can_delete = False
    extra = 0
    form = CeldaAdminInlineForm

@admin.register(Celda)
class CeldaAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('sitio', 'operador', 'id_operador')
    list_filter = ('operador__nombre', 'owner')
    resource_class = CeldaResource
    form = CeldaAdminInlineForm

@admin.register(Suministro)
class SuministroAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('sitio', 'titular', 'distribuidora', 'cuenta', 'medidor', 'direccion')
    list_filter = ('titular__nombre', 'distribuidora')
    resource_class = SuministroResource
    ordering = ['sitio', 'titular__nombre']

class SuministroInline(admin.TabularInline):
    model = Suministro
    show_change_link = True
    can_delete = False
    extra = 0

class LocadorInline(admin.TabularInline):
    model = Locador.sitios.through
    can_delete = True
    extra = 0

@admin.register(Sitio)
class SitioAdmin(ExportMixin, admin.ModelAdmin):
    list_filter = ('celdas__operador', 'provincia', 'proyecto', 'tipo', 'estado','estructura')
    resource_class = SitioResource
    inlines =  [CeldaInline, SuministroInline, LocadorInline]
    def get_readonly_fields(self, request, obj=None):
        if not obj or request.user.is_superuser:
            return self.readonly_fields
        else:
            return self.readonly_fields + ('sigla_id',)

@admin.register(Cellowner)
class CellownerAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('__str__', 'telefono', 'email')
    list_display_links = ['__str__']
    list_editable = ['telefono', 'email']
    ordering = ['apellido', 'nombre']
    list_filter = ['operador']

@admin.register(Locador)
class LocadorAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('__str__', 'telefono', 'email')
    list_display_links = ['__str__']
    list_editable = ['telefono', 'email']
    list_filter = ['sitios__sigla_id']
    ordering = ['apellido', 'nombre']

@admin.register(Operador)
class OperadorAdmin(admin.ModelAdmin):
    model = Operador

@admin.register(Titular)
class TitularAdmin(admin.ModelAdmin):
    model = Titular
