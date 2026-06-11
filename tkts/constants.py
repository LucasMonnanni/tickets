from dataclasses import dataclass, field
from django.contrib.auth.models import User
from typing import Literal, Any, TypedDict, cast, TYPE_CHECKING
from collections.abc import Callable
if TYPE_CHECKING:
	from tkts.models import Ticket

class Destinatarios(TypedDict, total=False):  
	ticket_email: bool
	grupos: list[Literal['Staff', 'Accesos', 'Supervisor Accesos', 'Mantenimiento', 'Supervisor Mantenimiento', 'Ingenieria']]
	usuarios: list[Literal['mantenimiento_auto', 'ingresos_auto']]

@dataclass
class Notificacion:
	nombre: str #used to lookup ntfc body in DB
	para: Destinatarios
	cc: Destinatarios | None = None

@dataclass
class Estado():
	nombre: str
	nombre_plural: str
	orden: int
	acceso: bool
	_nombre_publico: str|None = None
	campos_a_notificar: list[str] = field(default_factory=list)
	notificaciones: list[Notificacion] = field(default_factory=list)
	def __str__(self):
		return self.nombre
		
	@property
	def nombre_publico(self):
		return self._nombre_publico or self.nombre 

# DO NOT CHANGE ORDER: the indices of this list are hardcoded in the DB
estados: list[Estado] = [
	# 0 Abierto
	Estado(
		nombre='Abierto',
		nombre_plural='Abiertos',
		orden=1,
		acceso=False,
		notificaciones= [
			Notificacion(
				nombre = "Actualizado",
				para = {'ticket_email': True},
				cc = {'usuarios': ['mantenimiento_auto']}
			)
		],
		campos_a_notificar = ['programada', 'solucion']
	),
	# 1 En facturacion
	Estado(
		nombre='En facturación',
		nombre_plural='En facturación',
		_nombre_publico = 'Cerrado',
		orden=2,
		acceso=False
	),
	# 2 Cerrado
	Estado(
		nombre='Cerrado',
		nombre_plural='Cerrados',
		orden=3,
		acceso=False
	),
	# 3	Rechazado
	Estado(
		nombre='Rechazado',
		nombre_plural='Rechazados',
		orden=4,
		acceso=False
	),
	# 4 Acc Abierto
	Estado(
		nombre='Abierto',
		nombre_plural='Abiertos',
		orden=1,
		acceso=True,
		notificaciones= [
			Notificacion(
				nombre = 'Actualizado',
				para = {'ticket_email': True},
				cc = {'usuarios': ['ingresos_auto']}
			)
		],
		campos_a_notificar = ['programada', 'solucion']
	),
	# 5 Acc Cerrado
	Estado(
		nombre='Cerrado',
		nombre_plural='Cerrados',
		orden=2,
		acceso=True
	),
	# 6 Acc Rechazado
	Estado(
		nombre='Rechazado',
		nombre_plural='Rechazados',
		orden=3,
		acceso=True
	)
]

Criterio = Literal['isnull', 'is', 'isnot', 'ref_nombre_is', 'ref_nombre_isnot', 'ref_iscomplete']

criterio_funcs: dict[Criterio, Callable[[Any, Any], bool]] = {
	'isnull': lambda value, cond : (not bool(value) and value != False) == cond,
	'is': lambda value, cond : value == cond,
	'isnot': lambda value, cond : value != cond,
	'ref_nombre_is': lambda value, cond : getattr(value, 'nombre') == cond,
	'ref_nombre_isnot': lambda value, cond : getattr(value, 'nombre') != cond,
	'ref_iscomplete': lambda value, cond : (hasattr(value, 'is_complete') and callable(value.is_complete) and value.is_complete()) == cond
}

@dataclass
class Condicion:
	campo: str
	criterio: Criterio
	valor: bool | int | str

Errors_Criterio = dict[Criterio, Callable[[Any], str]]

errors: dict[str, Errors_Criterio] = {
	'oc': {
		'isnull': lambda x: f'El ticket {"no puede" if x else "debe"} tener una OC asociada para esta transición de estado.',
		'ref_iscomplete': lambda x: f'Los datos de la OC {"deben" if x else "no pueden"} estar completos para esta transición de estado.'
	},
	'cierre': {
		'isnull': lambda x: f'El ticket {"no puede" if x else "debe"} tener una fecha de cierre.'
	}
}

class Transicion:
	nombre: str
	desde: int
	hacia: int
	condiciones: list[Condicion]
	notificaciones: list[Notificacion]
	consecuencias: dict[
		Literal['prioridad', 'usuario_asignado', 'acceso__permiso_generado'],
		int|str|bool
	]
	def __init__(
			self,
			nombre: str,
			desde: int,
			hacia: int,
			condiciones: list[Condicion] | None = None,
			notificaciones: list[Notificacion] | None = None,
			consecuencias: dict[
				Literal['prioridad', 'usuario_asignado', 'acceso__permiso_generado'],
				int|str]| None = None
			):
		self.nombre = nombre
		self.desde = desde
		self.hacia = hacia
		self.condiciones = condiciones if condiciones is not None else []
		self.notificaciones = notificaciones if notificaciones is not None else []
		self.consecuencias = consecuencias if consecuencias is not None else {}

	def validar(self, ticket) -> tuple[bool, dict]:
		ticket = cast('Ticket', ticket)
		valid = True
		error_messages = {}
		for condicion in self.condiciones:
			cond_valid = criterio_funcs[condicion.criterio](
				getattr(ticket, condicion.campo),
				condicion.valor
			)
			if not cond_valid:
				error_message = errors\
						.get(condicion.campo, {})\
						.get(condicion.criterio,\
						lambda x: 'La transición de estado no permite este valor')
				error_messages.update({condicion.campo: error_message(condicion.valor)})
			valid = valid and cond_valid
		return valid, error_messages

	def aplicar(self, ticket) -> dict:
		from tkts.models import Usuario

		ticket = cast('Ticket', ticket)
		changed_data = {}
		for campo, valor in self.consecuencias.items():
			if campo == 'prioridad':
				changed_data['Prioridad'] = {'a': valor}
				ticket.prioridad = int(valor)
			elif campo == 'usuario_asignado':
				try:
					usuario = Usuario.objects.get(group = valor)
					ticket.usuario_asignado = usuario
					changed_data['Usuario Asignado'] = {'a': str(usuario)}
				except Usuario.DoesNotExist:
					ticket.usuario_asignado = None
			elif campo == 'acceso__permiso_generado':
				assert(ticket.acceso)
				ticket.acceso.permiso_generado = valor
		return changed_data

transiciones_permitidas: list[Transicion] = [
	# 0 a 1 A facturacion
	Transicion(
		'A facturacion', 0, 1,
		[
			Condicion('oc', 'isnull', False),
			Condicion('cierre', 'isnull', False),
		],
		[
			Notificacion('Cerrado', {'ticket_email': True}, {'usuarios': ['mantenimiento_auto']})
		]
	),
	# 0 a 2 Cerrar
	Transicion(
		'Cerrar', 0, 2,
		[
			Condicion('oc', 'isnull', True),
			Condicion('cierre', 'isnull', False),
		],
		[
			Notificacion('Cerrado', {'ticket_email': True}, {'usuarios': ['mantenimiento_auto']})
		]
	),
	# 1 a 2 OK a facturar
	Transicion(
		'Ok a facturar', 1, 2,
		[
			Condicion('oc', 'ref_iscomplete', True)
		],
		[
			Notificacion('Ok a facturar', {'grupos': ['Supervisor Mantenimiento']}, {'usuarios': ['mantenimiento_auto']})
		]
	),
	# 0 a 3 Rechazar
	Transicion(
		'Rechazar', 0, 3,
		[
			Condicion('oc', 'isnull', True),
			Condicion('cierre', 'isnull', False),
		],
		[
			Notificacion('Rechazado', {'ticket_email': True}, {'usuarios': ['mantenimiento_auto']})
		]
	),
	# 4 a 5 Cerrar acceso
	Transicion(
		'Cerrar acceso', 4, 5,
		[
			Condicion('cierre', 'isnull', False)
		],
		[
			Notificacion('Cerrado', {'ticket_email': True}, {'usuarios': ['ingresos_auto']})
		]
	),
	# 4 a 6 Rechazar acceso
	Transicion(
		'Rechazar acceso', 4, 6,
		[
			Condicion('cierre', 'isnull', False)
		],
		[
			Notificacion('Rechazado', {'ticket_email': True}, {'usuarios': ['ingresos_auto']})
		],
		{
			'acceso__permiso_generado': True,
		},
	),
]

transiciones_auto: list[Transicion] = [
	# A 5 Mantenimiento
	Transicion(
		'Acceso Mantenimiento',
		0,
		5,
		[
			Condicion('acceso', 'isnull', False),
			Condicion('cliente', 'ref_nombre_is', 'Mantenimiento'),
		],
		[
			Notificacion('Generado', {'ticket_email': True}),
		],
	),
	# A 4 Acceso
	Transicion(
		'Acceso',
		0,
		4,
		[
			Condicion('acceso', 'isnull', False)
		],
		[
			Notificacion('Generado', {'ticket_email': True}),
			Notificacion('Acceso para legales', {'grupos': ['Accesos']}, {'usuarios': ['ingresos_auto'], 'grupos': ['Supervisor Accesos']})
		],
		{
			'prioridad': 2,
			'usuario_asignado': 'Accesos'
		},
	),
	# A 0 Cambio de equipos		acceso_isnull = True at this point
	Transicion(
		'Cambio de equipos',
		0,
		0,
		[
			Condicion('cambio_de_equipos', 'isnull', False)
		],
		[
			Notificacion('Generado', {'ticket_email': True}),
			Notificacion('Ingeniería', {'grupos': ['Ingenieria']}, {'usuarios': ['mantenimiento_auto']}),
		],
		{
			'prioridad': 2,
			'usuario_asignado': 'Mantenimiento'
		},
	),
	# A 0 Energia
	Transicion(
		'Energia',
		0,
		0,
		[
			Condicion('motivo', 'ref_nombre_is', 'FALTA DE ENERGÍA'),
		],
		[
			Notificacion('Generado', {'ticket_email': True}),
			Notificacion('Genérico', {'usuarios': ['mantenimiento_auto']}),
		],
		consecuencias = {
			'prioridad': 0,
		},
	),
	# A 1 Default
	Transicion(
		'Generico',
		0,
		0,
		notificaciones = [
			Notificacion('Generado', {'ticket_email': True}),
			Notificacion('Genérico', {'usuarios': ['mantenimiento_auto']}),
		],
	),
]
