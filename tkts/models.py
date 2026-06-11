import sitios.models as sitios
import after_response
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.core.mail import get_connection
from ntfcs.models import Notificacion
from .constants import estados, transiciones_auto, transiciones_permitidas, Notificacion as Ntfc


class Motivo(models.Model):
	nombre = models.CharField(max_length=32, unique=True)
	visible = models.BooleanField()

	class Meta:
		verbose_name_plural = 'Motivos'
		ordering = ('nombre', )

	def __str__(self):
		return self.nombre

class Cliente(models.Model):
	nombre = models.CharField(max_length=32, unique=True)
	visible = models.BooleanField()

	class Meta:
		verbose_name_plural = 'Clientes'
		ordering = ('nombre', )

	def __str__(self):
		return self.nombre

class Usuario(User):
	class Meta:
		proxy = True

	def __str__(self):
		return self.first_name.capitalize()[0] + '. ' + self.last_name.capitalize() if self.first_name and self.last_name else self.username

class Ticket(models.Model):
	id = models.AutoField(primary_key=True, verbose_name='Ticket')
	_estado_id = models.IntegerField(
		choices=[(i, estado.nombre) for i, estado in enumerate(estados)])
	inicio = models.DateTimeField(
		auto_now=False, auto_now_add=False, default=timezone.now, verbose_name='Fecha de Inicio')
	nombre = models.CharField(max_length=64, verbose_name='Nombre Completo')
	email = models.EmailField(max_length=256, verbose_name='Email')
	telefono = models.PositiveIntegerField(verbose_name='Teléfono')
	cliente = models.ForeignKey(
		'Cliente', related_name='tickets', on_delete=models.PROTECT, verbose_name='Cliente')
	sitio = models.ForeignKey(
		sitios.Sitio, on_delete=models.PROTECT, verbose_name='Sitio')
	motivo = models.ForeignKey(
		'Motivo', related_name='tickets', on_delete=models.PROTECT, verbose_name='Motivo')
	prioridad = models.PositiveSmallIntegerField(
		null=True, blank=True, verbose_name='Prioridad')
	problema = models.TextField(verbose_name='Problema')
	link = models.URLField(null=True, blank=True,
						   verbose_name="Link de documentación")
	solucion = models.TextField(null=True, blank=True, verbose_name='Solución')
	programada = models.DateField(
		auto_now=False, auto_now_add=False, null=True, blank=True, verbose_name='Fecha programada')
	cierre = models.DateField(auto_now=False, auto_now_add=False,
							  null=True, blank=True, verbose_name='Fecha de cierre')
	usuario_asignado = models.ForeignKey(
		Usuario, on_delete=models.PROTECT,  related_name='tickets_asignados', null=True, blank=True, verbose_name='Usuario asignado')
	observaciones = models.TextField(
		null=True, blank=True, verbose_name='Observaciones')
	ultima_modificacion = models.DateTimeField(
		auto_now=True, null=True, blank=True, verbose_name='Última modificación')
	acceso = models.OneToOneField(
		'Acceso', blank=True, null=True, on_delete=models.PROTECT, related_name='ticket')
	cambio_de_equipos = models.OneToOneField(
		'CambioDeEquipos', blank=True, null=True, on_delete=models.PROTECT, related_name='ticket')
	oc = models.OneToOneField(
		'OC', blank=True, null=True, on_delete=models.PROTECT, related_name='ticket')

	@property
	def estado(self):
		"""Return the Estado dataclass object for this ticket's estado_id."""
		return estados[self._estado_id]

	@estado.setter
	def estado(self, value):
		"""Set estado from either an integer index or an Estado dataclass object."""
		if isinstance(value, int):
			self._estado_id = value
		else:
			# Assume it's an Estado object, find its index
			try:
				self._estado_id = estados.index(value)
			except ValueError:
				raise ValueError(f"Estado {value} not found in estados list")

	@after_response.enable
	def enviar_notificaciones(ticket, ntfcs: list[Ntfc]):
		emails = []
		if not ntfcs:
			return 0
		for ntfc in ntfcs:
			notificacion = Notificacion.objects.get(nombre__icontains=ntfc.nombre)
			to = []
			if ntfc.para:
				if 'ticket_email' in ntfc.para:
					to += [ticket.email] if ntfc.para['ticket_email'] else []
					print('got through email')
				if 'grupos' in ntfc.para:
					to += [usuario.email for usuario in User.objects.filter(
						groups__name__in=ntfc.para['grupos'])]
				if 'usuarios' in ntfc.para:
					to += [User.objects.get(
						username=username).email for username in ntfc.para['usuarios']]
			cc = []
			if ntfc.cc:
				if 'ticket_email' in ntfc.cc:
					cc += [ticket.email] if ntfc.cc['ticket_email'] else []
				if 'grupos' in ntfc.cc:
					cc += [usuario.email for usuario in User.objects.filter(
						groups__name__in=ntfc.cc['grupos'])]
				if 'usuarios' in ntfc.cc:
					cc += [User.objects.get(
						username=username).email for username in ntfc.cc['usuarios']]
			emails.append(notificacion.crear_mail(ticket, to, cc))
		return get_connection().send_messages(emails)

	def get_public_query(self):
		return '?id={}&email={}'.format(self.pk, self.email)

	def get_absolute_url(self):
		return reverse('detalle', kwargs={'pk': self.pk})

	def __str__(self):
		return 'Tkt N° ' + str(self.pk) + ' - ' + self.sitio.sigla_id + ' - ' + self.motivo.nombre

class OC(models.Model):
	class Monedas(models.TextChoices):
		ARS = 'ARS', '$'
		USD = 'USD', 'u$s'

	class Condiciones(models.TextChoices):
		NETO_7 = 'NETO_7', 'Neto 7d'
		NETO_30 = 'NETO_30', 'Neto 30d'
		ANTICIPO_30 = 'ANTICIPO_30', 'Anticipo 30%'
		ANTICIPO_50 = 'ANTICIPO_50', 'Anticipo 50%'

	class Compradores(models.TextChoices):
		u1 = '1', 'Unidad de negocios 1'
		u2 = '2', 'Unidad de negocios 2'

	numero = models.CharField(null=True, blank=True,
							  max_length=12, verbose_name='N° de OC')
	moneda = models.CharField(null=True, blank=True, max_length=3,
							  choices=Monedas.choices, default=Monedas.ARS, verbose_name='Moneda')
	condicion = models.CharField(null=True, blank=True, max_length=12,
								 choices=Condiciones.choices, default=Condiciones.NETO_30, verbose_name='Condición')
	contratista = models.CharField(
		null=True, blank=True, max_length=32, verbose_name='Contratista')
	costo = models.DecimalField(
		null=True, blank=True, max_digits=9, decimal_places=2, verbose_name='Costo')
	comprador = models.CharField(null=True, blank=True, max_length=2,
								 choices=Compradores.choices, default=Compradores.u1, verbose_name='Comprador')

	def __str__(self):
		return f'OC {self.numero}'

class Acceso(models.Model):
	fecha_desde = models.DateField(verbose_name='Fecha de inicio')
	fecha_hasta = models.DateField(verbose_name='Fecha de fin')
	hora_desde = models.TimeField(verbose_name='Hora desde')
	hora_hasta = models.TimeField(verbose_name='Hora hasta')
	empresa = models.CharField(max_length=128, verbose_name='Empresa')
	afectacion = models.BooleanField(
		verbose_name='¿Hay afectación de servicio?', default=False)
	riesgo_electrico = models.BooleanField(
		verbose_name='¿Hay riesgo eléctrico?', default=False)
	altura = models.BooleanField(
		verbose_name='¿Incluye trabajo en altura?', default=False)
	permiso_generado = models.BooleanField(default=False)

	class Meta:
		verbose_name = 'Acceso'
		verbose_name_plural = 'Accesos'

	@property
	def personal_aprobado(self):
		return self.personal.filter(aprobado=True)
	
	@property
	def personal_no_aprobado(self):
		return self.personal.filter(aprobado=False)

	def __str__(self):
		return f'Acceso {self.pk}'

class Personal(models.Model):
	acceso = models.ForeignKey(Acceso, on_delete=models.CASCADE, related_name='personal')
	nombre = models.CharField(max_length=64)
	apellido = models.CharField(max_length=64)
	dni = models.PositiveIntegerField()
	telefono = models.PositiveBigIntegerField()
	aprobado = models.BooleanField(default = True)

	class Meta:
		verbose_name_plural = 'Personal'

	def __str__(self):
		return f'{self.nombre} {self.apellido}'

	@property
	def nombre_completo(self):
		return f'{self.apellido}, {self.nombre}'

	@property
	def password(self):
		password = "".join(self.apellido.split())[:7].title()
		password += '12345678!'[len(password):]
		return password

class CambioDeEquipos(models.Model):
	antenas_actual = models.TextField(verbose_name='Antenas RF actuales')
	antenas = models.TextField(verbose_name='Antenas RF')
	enlaces_actual = models.TextField(verbose_name='Radioenlaces actuales')
	enlaces = models.TextField(verbose_name='Radioenlaces')
	rru_actual = models.TextField(verbose_name='RRU actual')
	rru = models.TextField(verbose_name='RRU')
	piso = models.TextField(verbose_name='Cota 0')
	energia = models.DecimalField(
		max_digits=5, decimal_places=2, verbose_name='Potencia (kW)')

	class Meta:
		verbose_name = 'Cambio de Equipos'
		verbose_name_plural = 'Cambios de Equipos'

	def __str__(self):
		return f'Cambio {self.pk}'
