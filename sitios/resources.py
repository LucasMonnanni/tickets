from .models import Sitio, Suministro, Celda, Cellowner, Locador, Operador, Titular
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget, IntegerWidget, DateWidget, DecimalWidget

class SuministroWidget(ForeignKeyWidget):
    def get_queryset(self, value, row, *args, **kwargs):
        return self.model.objects.filter(
            sitio__id = row['sitio']
        )

    def render(self, value, obj = None):
        if value:
            return value.titular.nombre
        else:
            return ''
        
class OwnerWidget(ForeignKeyWidget):
    def clean(self, value, row=None, **kwargs):
        if value:
            try:
                apellido, nombre = value.split(', ')
                obj = self.model.objects.get(nombre__iexact = nombre, apellido__iexact = apellido)
                return obj
            except:
                raise Exception('Nombre no encontrado, agregue el contacto antes de asignarlo')
        else:
            return None

    def render(self, value, obj = None):
        if value:
            return value.apellido + ', ' + value.nombre
        else:
            return ''

class CeldaResource(resources.ModelResource):
    sitio = fields.Field(
        attribute='sitio',
        column_name='Sitio',
        widget= ForeignKeyWidget(Sitio, 'id')
    )
    operador = fields.Field(
        attribute='operador',
        column_name='Operador',
        widget= ForeignKeyWidget(Operador, 'nombre')
    )
    id_operador = fields.Field(
        attribute='id_operador',
        column_name='ID'
    )
    suministro = fields.Field(
        attribute='suministro',
        column_name='Suministro',
        widget= SuministroWidget(Suministro, 'titular__nombre')
    )
    owner = fields.Field(
        attribute='owner',
        column_name='Cellowner',
        widget=OwnerWidget(Cellowner)
    )
    class Meta:
        model = Celda
        skip_unchanged = True
        fields = ('sitio', 'operador', 'id_operador', 'suministro', 'owner')
        export_order = ('sitio', 'operador', 'id_operador', 'suministro', 'owner')

class SuministroResource(resources.ModelResource):
    sitio = fields.Field(
        attribute='sitio',
        column_name='Sitio',
        widget= ForeignKeyWidget(Sitio, 'id')
    )
    titular = fields.Field(
        attribute='titular',
        column_name='Titular',
        widget= ForeignKeyWidget(Titular, 'nombre')
    )
    distribuidora = fields.Field(
        attribute='distribuidora',
        column_name='Distribuidora'
    )
    cuenta = fields.Field(
        attribute='cuenta',
        column_name='N° de Cuenta'
    )
    medidor = fields.Field(
        attribute='medidor',
        column_name='N° de Medidor'
    )
    direccion = fields.Field(
        attribute='direccion',
        column_name='Dirección'
    )
    operadores = fields.Field(
        attribute='operadores',
        column_name='Operadores',
        widget=IntegerWidget()
    )
    class Meta:
        model = Suministro
        skip_unchanged = True
        fields = ('id', 'sitio', 'titular', 'distribuidora', 'cuenta', 'medidor', 'direccion', 'operadores')
        export_order = ('id', 'sitio', 'titular', 'distribuidora', 'cuenta', 'medidor', 'direccion', 'operadores')

class LocadorResource(resources.ModelResource):
    class Meta:
        model = Locador
        skip_unchanged = True

class CellownerResource(resources.ModelResource):
    operador = fields.Field(
        attribute='operador',
        column_name='operador',
        widget= ForeignKeyWidget(Operador, 'nombre')
    )
    class Meta:
        model = Cellowner
        skip_unchanged = True

class SitioResource(resources.ModelResource):
    id = fields.Field(
        attribute='id',
        column_name='ID'
    )
    nombre = fields.Field(
        attribute='nombre',
        column_name='Nombre'
    )
    direccion = fields.Field(
        attribute='direccion',
        column_name='Dirección'
    )
    localidad  = fields.Field(
        attribute='localidad',
        column_name='Localidad'
    )
    municipio = fields.Field(
        attribute='municipio',
        column_name='Municipio'
    )
    provincia  = fields.Field(
        attribute='provincia',
        column_name='Provincia'
    )
    latitud  = fields.Field(
        attribute='latitud',
        column_name='Latitud',
        widget= DecimalWidget()
    )
    longitud = fields.Field(
        attribute='longitud',
        column_name='Longitud',
        widget= DecimalWidget()
    )
    proyecto = fields.Field(
        attribute='proyecto',
        column_name='Proyecto'
    )
    tipo = fields.Field(
        attribute='tipo',
        column_name='Tipo de Sitio'
    )
    estructura  = fields.Field(
        attribute='estructura',
        column_name='Tipo de Estructura'
    )
    altura = fields.Field(
        attribute='altura',
        column_name='Altura Total'
    )
    acceso = fields.Field(
        attribute='acceso',
        column_name='Acceso'
    )
    candado_calle = fields.Field(
        attribute='candado_calle',
        column_name='Candado desde Calle'
    )
    candado_sitio = fields.Field(
        attribute='candado_sitio',
        column_name='Candado de Sitio'
    )
    conflicto = fields.Field(
        attribute='conflicto',
        column_name='Acceso conflictivo'
    )
    procedimiento  = fields.Field(
        attribute='procedimiento',
        column_name='Procedimiento'
    )
    estado = fields.Field(
        attribute='estado',
        column_name='Estado'
    )
    operadores  = fields.Field(
        attribute='operadores',
        column_name='Operadores'
    )
    class Meta:
        model = Sitio
        skip_unchanged = True
        fields = (
            'id',
            'nombre',
            'direccion',
            'localidad',
            'municipio',
            'provincia',
            'latitud',
            'longitud',
            'proyecto',
            'tipo',
            'estructura',
            'altura',
            'acceso',
            'candado_calle',
            'candado_sitio',
            'conflicto',
            'procedimiento',
            'estado',
            'operadores',
        )
        export_order = (
            'id',
            'nombre',
            'direccion',
            'localidad',
            'municipio',
            'provincia',
            'latitud',
            'longitud',
            'proyecto',
            'tipo',
            'estructura',
            'altura',
            'acceso',
            'candado_calle',
            'candado_sitio',
            'conflicto',
            'procedimiento',
            'estado',
            'operadores',
        )
        import_id_fields = ['id']