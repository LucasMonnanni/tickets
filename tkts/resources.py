from tkts.models import *
from sitios.models import Sitio
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget, DateTimeWidget, DateWidget, CharWidget, DecimalWidget, IntegerWidget


class TicketResource(resources.ModelResource):
    id = fields.Field(
        column_name = 'Id',
        attribute = 'id',
    )
    estado = fields.Field(
        column_name = 'Estado',
        attribute = 'estado',
        widget = CharWidget(),
    )
    inicio = fields.Field(
        column_name = 'Inicio',
        attribute = 'inicio',
        widget = DateTimeWidget(format='%d/%m/%Y %H:%M:%S'),
    )
    cliente = fields.Field(
        column_name = 'Cliente',
        attribute = 'cliente',
        widget = ForeignKeyWidget(Cliente, 'nombre', coerce_to_string=True),
    )
    sitio = fields.Field(
        column_name = 'Sitio',
        attribute = 'sitio',
        widget = ForeignKeyWidget(Sitio, 'sigla_id', coerce_to_string=True),
    )
    motivo = fields.Field(
        column_name = 'Motivo',
        attribute = 'motivo',
        widget = ForeignKeyWidget(Motivo, 'nombre', coerce_to_string=True),
    )
    prioridad = fields.Field(
        column_name = 'Prioridad',
        attribute = 'prioridad',
        widget = IntegerWidget(coerce_to_string=True),
    )
    problema = fields.Field(
        column_name = 'Problema',
        attribute = 'problema',
        widget = CharWidget(),
    )
    solucion = fields.Field(
        column_name = 'Solucion',
        attribute = 'solucion',
        widget = CharWidget(),
    )
    contratista = fields.Field(
        column_name = 'Contratista',
        attribute = 'contratista',
        widget = CharWidget(),
    )
    costo = fields.Field(
        column_name = 'Costo',
        attribute = 'costo',
        widget = DecimalWidget(),
    )
    oc = fields.Field(
        column_name = 'Oc',
        attribute = 'oc',
        widget = CharWidget(),
    )
    programada = fields.Field(
        column_name = 'Programada',
        attribute = 'programada',
        widget = DateWidget(format='%d/%m/%Y'),
    )
    cierre = fields.Field(
        column_name = 'Cierre',
        attribute = 'cierre',
        widget = DateTimeWidget(format='%d/%m/%Y'),
    )
    usuario_asignado = fields.Field(
        column_name = 'Usuario Asignado',
        attribute = 'usuario_asignado',
        widget = ForeignKeyWidget(Usuario, 'apellido', coerce_to_string=True),
    )
    observaciones = fields.Field(
        column_name = 'Observaciones',
        attribute = 'observaciones',
        widget = CharWidget(),
    )

    class Meta:
        __name__ = 'Tickets'
        model = Ticket
        exclude = ('nombre', 'email', 'telefono', 'ultima_modificacion',)
