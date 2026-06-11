from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.core.mail import send_mail
from tkts.models import Ticket, Usuario
from tkts.constants import estados
from difflib import unified_diff
from django.utils import timezone


types = {	
	'estado': 'const',
	'motivo': 'ref',
	'cliente': 'ref',
	'sitio': 'ref',
	'prioridad': 'number',
	'problema': 'long_text',
	'contratista': 'text',
	'costo': 'number',
	'oc': 'text',
	'programada': 'date',
	'cierre': 'date',
	'usuario_asignado': 'ref',
	'solucion': 'none',
	'observaciones': 'none',
	'solucion_agregar': 'add_text',
	'observaciones_agregar': 'add_text',
}

class TicketChangeLog(models.Model):
	user = models.ForeignKey(Usuario, on_delete= models.PROTECT)
	ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='cambios')
	timestamp = models.DateTimeField(auto_now_add=True)
	changed_data = models.JSONField(encoder=DjangoJSONEncoder)

	@classmethod
	def log(cls, user: Usuario, ticket: Ticket, form):
		changed_fields = form.changed_data
		changed_data = {}
		de = None
		a = None
		for field_name in changed_fields:
			field_type = types.get(field_name, 'not_supported')
			if field_type == 'add_text':
				changed_data[form.fields[field_name.split('_')[0]].label] = {
					'agregado': form.cleaned_data[field_name],
				}
			else:
				field_value = getattr(ticket, field_name)
				if field_name == 'estado':
					de = estados[form['estado'].initial].nombre
					a =  field_value.nombre
				elif field_type == 'ref':
					field = getattr(Ticket, field_name).field
					related_model = field.remote_field.model
					try:
						value = related_model.objects.get(pk = field_value)
					except:
						value = field_value or 'Ninguno'
					de = related_model.objects.get(pk = form.initial[field_name]).__str__() if form.initial[field_name] else None
					a = value.__str__()
				elif field_type == 'long_text':
					prev_value = form.initial[field_name] or ''
					value = field_value or ''
					diff = unified_diff(prev_value.splitlines(), value.splitlines())
					de = ''
					a = ''
					for line in diff:
						if not line.startswith('+++') and not line.startswith('---') and not line.startswith('@@'):
							if line.startswith('-'):
								de += line + '\n'
							elif line.startswith('+'):
								a += line + '\n'
				elif field_type == 'date':
					de = form.initial[field_name].strftime("%d/%m/%y") if form.initial[field_name] else None
					a = field_value.strftime("%d/%m/%y") if field_value else 'Ninguna'
				elif field_type in ['number', 'text']:
					de = form.initial[field_name] or None
					a =  field_value
				elif field_type == 'none':
					de = None
					a = None
				elif field_type == 'not_supported':
					ErrorLog.objects.create(code=0, data=f'Campo no soportado en el log de cambios: {field_name}').save()
				if de or a:
					changed_data[form.fields[field_name].label] = {}
					if de:
						changed_data[form.fields[field_name].label]['de'] = de
					if a:
						changed_data[form.fields[field_name].label]['a'] = a
		cls.objects.create(user = user, ticket = ticket, changed_data = changed_data).save()

class ErrorLog(models.Model):
	timestamp = models.DateTimeField(auto_now_add = True)
	code = models.SmallIntegerField()
	data = models.TextField()

	def save(self, *args, **kwargs):
		admins = [u.email for u in User.objects.filter(is_superuser = True)]
		subject = f'Tickets - Error: {self.code}'
		body = f'{self.timestamp} - {self.code}\n{self.data}'
		send_mail(
			subject,
			body,
			settings.DEFAULT_FROM_EMAIL,
			admins,
			fail_silently=True,
		)
		super().save(*args, **kwargs)

	def __str__(self):
		return "Error " + str(self.code) + " - " +  self.timestamp.astimezone(timezone.get_current_timezone()).strftime('%d/%m/%y-%H:%M:%S')
