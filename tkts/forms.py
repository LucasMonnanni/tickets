import datetime
from django.forms import (
	ModelForm, 
	ModelChoiceField, 
	ModelMultipleChoiceField, 
	CharField,
	ChoiceField, 
	Select,
	Textarea, 
	TextInput,
	CheckboxInput,
	modelformset_factory
)
from django.forms.widgets import URLInput
from django.core.exceptions import ValidationError
from tkts.models import Ticket, Motivo, Cliente, Usuario, Acceso, Personal, CambioDeEquipos, OC
from tkts.constants import estados
from sitios.models import Sitio
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.models import User, Group
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Invisible


def resizable_textarea(rows = 3):
	return Textarea(attrs=  {
		'class': 'form-control', 
		'style': 'resize:none;',
		'rows': str(rows),
		'oninput': 'this.style.height = ""; this.style.height = (this.scrollHeight + 2) + "px";',
		'onfocus': 'this.style.height = ""; this.style.height = (this.scrollHeight + 2) + "px";',
	})

class SitioField(ModelChoiceField):
	def __init__(self, *args, **kwargs):
		kwargs.update({
			'queryset': Sitio.objects.all(),
			'to_field_name': 'sigla_id',
			'label': 'Sitio',
		})
		super().__init__(*args, **kwargs)

class MotivoField(ModelChoiceField):
	def __init__(self, *args, **kwargs):
		kwargs.update({
		'queryset': Motivo.objects.filter(visible = True),
		'required': True,
		'to_field_name': 'nombre',
		'widget': Select(
			attrs = {
				'class': 'form-control motivo',
				'hx-get': '/ticket/motivo/' ,
				'hx-target': '#motivo-subform',
				'hx-swap': 'innerHTML',
			}
		)})
		super().__init__(*args, **kwargs)

class ClienteField(ModelChoiceField):
	def __init__(self, *args, **kwargs):
		kwargs.update({
			'queryset': Cliente.objects.filter(visible = True),
			'required': True,
			'label': 'Cliente'
		})
		super().__init__(*args, **kwargs)

class PrioridadWidget(Select):
	#template_name = 'tkts/partials/prioridad_select.html'

	def __init__(self):
		super().__init__(
			choices=[
				(None, ''),
				(0, '0 - Riesgo para las personas - 6hs'),
				(1, '1 - Afectación de servicio - 24hs'),
				(2, '2 - Correctivo urgente - 48/72hs'),
				(3, '3 - Correctivo programado'),
			],
			attrs= {
				'class': 'form-control'
			}
		)

class TicketForm(ModelForm):
	captcha = ReCaptchaField(
		widget=ReCaptchaV2Invisible(
			attrs={
				'data-theme': 'dark',
			}
		)
	)

	class Meta:
		model = Ticket
		fields = ['nombre', 'email', 'telefono', 'sitio', 'cliente', 'motivo', 'problema', 'link']
		field_classes = {
			'motivo': MotivoField,
			'cliente': ClienteField,
		}
		labels = {
			'email': 'Correo electrónico',
			'problema': 'Detalle',
			'link': 'Link de documentación',
		}
		widgets = {
			'problema': resizable_textarea(),
			'link': URLInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
		}
		help_texts = {
			'link': 'Inserte link a una carpeta virtual (Dropbox, SharePoint, etc.) con la documentación o fotos pertinentes',
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['sitio'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'off'})
		self.fields['cliente'].widget.attrs.update({'class': 'form-control'})
		self.fields['problema'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'off'})
		
	def clean_link(self):
		link = self.cleaned_data.get('link')
		motivo = self.cleaned_data.get('motivo')
		if motivo and motivo.nombre in ['ACCESO', 'CAMBIO DE EQUIPOS']:
			if not link:
				raise ValidationError('Este campo es requerido para este tipo de ticket')
		return link

class TicketUpdateForm(ModelForm):
	estado = ChoiceField(choices = [], label = 'Estado', required = True)
	motivo = ModelChoiceField(queryset = Motivo.objects.filter(visible = True), label = 'Motivo',empty_label=None, required = True)
	usuario_asignado = ModelChoiceField(queryset = Usuario.objects.filter(groups__name = 'Staff'), label = 'Usuario Asignado', required=False)
	solucion_agregar = CharField(required = False, widget = resizable_textarea(1))
	observaciones_agregar = CharField(required = False, widget = resizable_textarea(1))

	class Meta:
		model = Ticket
		fields = [
			'estado',
			'cliente',
			'sitio',
			'motivo',
			'prioridad',
			'problema',
			'solucion',
			'programada',
			'cierre',
			'usuario_asignado',
			'observaciones'
		]
		field_classes = {
			'cliente': ClienteField,
			'sitio': SitioField,
		}
		labels = {
			'problema': 'Detalle',
			'solucion': 'Solución',
			'programada': 'Fecha programada de cierre',
			'cierre': 'Fecha efectiva de cierre',
		}
		widgets = {
			'prioridad': PrioridadWidget(),
			'problema': resizable_textarea(),
			'solucion': Textarea(attrs={
				'class': 'form-control-plaintext',
				'rows': 1,
				'readonly': True,
				'style': "resize: none;"
			}),
			'programada': TextInput(attrs={'class': 'form-control', 'type': 'date'}),
			'cierre': TextInput(attrs={'class': 'form-control', 'type': 'date'}),
			'observaciones': Textarea(attrs={
				'class': 'form-control-plaintext',
				'rows': 1,
				'readonly': True,
				'style': "resize: none;"
			}),
		}

	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop('user', None)
		super().__init__(*args, **kwargs)
		# Set the initial value for estado from the model's _estado_id field
		if self.instance and hasattr(self.instance, '_estado_id'):
			self.fields['estado'].initial = self.instance._estado_id
		self.fields['estado'].choices = [(i, estado.nombre)  for i, estado in enumerate(estados) if estado.orden > 0 and estado.acceso == (self.instance.acceso != None)]
		self.fields['estado'].widget.attrs.update({'class': 'form-control'})
		self.fields['cliente'].empty_label = None
		self.fields['cliente'].widget.attrs.update({'class': 'form-control'})
		self.fields['sitio'].empty_label = None
		self.fields['sitio'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'off'})
		self.fields['motivo'].widget.attrs.update({'class': 'form-control'})
		self.fields['usuario_asignado'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'off'})

	def clean_estado(self):
		return int(self.cleaned_data['estado'])

	def clean(self):
		cleaned_data = super().clean()
		if cleaned_data['solucion_agregar']:
			cleaned_data['solucion'] += ('\n' if cleaned_data['solucion'] != '' else '') + datetime.datetime.now().strftime('%d/%m/%y %H:%M') + ' - ' + self.user.__str__() + ': ' + cleaned_data['solucion_agregar']
			self.changed_data.append('solucion')
		if cleaned_data['observaciones_agregar']:
			cleaned_data['observaciones'] += ('\n' if cleaned_data['observaciones'] != '' else '') + datetime.datetime.now().strftime('%d/%m/%y %H:%M') + ' - ' + self.user.__str__() + ': ' + cleaned_data['observaciones_agregar']
			self.changed_data.append('observaciones')

	def save(self, commit=True):
		instance = super().save(commit=False)
		# Map the form's 'estado' field to the model's '_estado_id' attribute
		if 'estado' in self.cleaned_data:
			instance._estado_id = int(self.cleaned_data['estado'])
		if commit:
			instance.save()
		return instance

class GroupAdminForm(ModelForm):
	class Meta:
		model = Group
		exclude = []

	# Add the users field.
	users = ModelMultipleChoiceField(
		 queryset=User.objects.all(), 
		 required=False,
		 # Use the pretty 'filter_horizontal widget'.
		 widget=FilteredSelectMultiple('users', False)
	)

	def __init__(self, *args, **kwargs):
		# Do the normal form initialisation.
		super(GroupAdminForm, self).__init__(*args, **kwargs)
		# If it is an existing group (saved objects have a pk).
		if self.instance.pk:
			# Populate the users field with the current Group users.
			self.fields['users'].initial = self.instance.user_set.all()

	def save_m2m(self):
		# Add the users to the Group.
		self.instance.user_set.set(self.cleaned_data['users'])

	def save(self, *args, **kwargs):
		# Default save
		instance = super(GroupAdminForm, self).save()
		# Save many-to-many data
		self.save_m2m()
		return instance

def get_default_dates():
	today = datetime.date.today()
	return (
		(today + datetime.timedelta(days=2)).strftime("%Y-%m-%d"),
		(today + datetime.timedelta(days=3)).strftime("%Y-%m-%d"),
		today.strftime("%Y-%m-%d"),
		(today + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
	)

class AccesoForm(ModelForm):
	class Meta:
		model = Acceso
		fields = ['fecha_desde', 'fecha_hasta', 'hora_desde', 'hora_hasta', 'empresa', 'afectacion', 'riesgo_electrico', 'altura']
		widgets = {
			'fecha_desde': TextInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': ''}),
			'fecha_hasta': TextInput(attrs={'class': 'form-control', 'type': 'date'}),
			'hora_desde': TextInput(attrs={'class': 'form-control', 'type': 'time', 'step': '1800'}),
			'hora_hasta': TextInput(attrs={'class': 'form-control', 'type': 'time', 'step': '1800'}),
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		default_from, default_to, default_min, default_max = get_default_dates()
		self.fields['fecha_desde'].initial = default_from
		self.fields['fecha_desde'].widget.attrs.update({'min': default_min, 'max': default_max})
		self.fields['fecha_hasta'].initial = default_to
		self.fields['fecha_hasta'].widget.attrs.update({'min': default_min, 'max': default_max})
		self.fields['hora_desde'].initial = '08:00'
		self.fields['hora_hasta'].initial = '18:00'
		self.fields['afectacion'].widget.attrs.update({'class': 'form-check-input'})
		self.fields['riesgo_electrico'].widget.attrs.update({'class': 'form-check-input'})
		self.fields['altura'].widget.attrs.update({'class': 'form-check-input'})
		self.fields['empresa'].widget.attrs.update({'class': 'form-control'})
		if self.instance and self.instance.permiso_generado:
			self.fields['fecha_desde'].widget.attrs.update({'readonly': True})
			self.fields['fecha_hasta'].widget.attrs.update({'readonly': True})
			self.fields['hora_desde'].widget.attrs.update({'readonly': True})
			self.fields['hora_hasta'].widget.attrs.update({'readonly': True})

	def clean(self):
		cleaned_data = super().clean()
		fecha_desde = cleaned_data.get('fecha_desde')
		fecha_hasta = cleaned_data.get('fecha_hasta')
		if fecha_desde and fecha_hasta and fecha_hasta < fecha_desde:
			raise ValidationError({'fecha_hasta': 'La fecha de fin debe ser igual o posterior a la fecha de inicio'})
		
		hora_desde = cleaned_data.get('hora_desde')
		hora_hasta = cleaned_data.get('hora_hasta')
		if hora_desde and hora_hasta and hora_hasta <= hora_desde:
			raise ValidationError({'hora_hasta': 'La hora de fin debe ser posterior a la hora de inicio'})
		
		return cleaned_data

	def clean_empresa(self):
		empresa = self.cleaned_data.get('empresa')
		if empresa:
			return empresa.title()
		return empresa

class PersonalForm(ModelForm):
	class Meta:
		model = Personal
		fields = ['nombre', 'apellido', 'dni', 'telefono', 'aprobado']
		labels = {
			'nombre': 'Nombre',
			'apellido': 'Apellido',
			'dni': 'DNI',
			'telefono': 'Teléfono',
			'aprobado': 'Aprobado?'
		}
		widgets = {
			'nombre': TextInput(attrs={'class': 'form-control form-control-sm', 'maxlength': '64', 'autocomplete': 'off', 'required': True}),
			'apellido': TextInput(attrs={'class': 'form-control form-control-sm', 'maxlength': '64', 'autocomplete': 'off', 'required': True}),
			'dni': TextInput(attrs={'class': 'form-control form-control-sm', 'type': 'number', 'min': '10000000', 'max': '99999999', 'autocomplete': 'off', 'required': True}),
			'telefono': TextInput(attrs={'class': 'form-control form-control-sm', 'type': 'number', 'min': '1100000000', 'max': '9999999999', 'autocomplete': 'off', 'required': True}),
			'aprobado': CheckboxInput(attrs={'class': 'form-check-input', 'value': 'true'})
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.instance.pk and self.instance.acceso.permiso_generado:
			self.fields['nombre'].widget.attrs.update({'readonly': True})
			self.fields['apellido'].widget.attrs.update({'readonly': True})
			self.fields['dni'].widget.attrs.update({'readonly': True})
			self.fields['telefono'].widget.attrs.update({'readonly': True})

	def clean_nombre(self):
		nombre = self.cleaned_data.get('nombre')
		if nombre:
			return " ".join(nombre.split()).title()
		return nombre

	def clean_apellido(self):
		apellido = self.cleaned_data.get('apellido')
		if apellido:
			return " ".join(apellido.split()).title()
		return apellido

PersonalFormSet = modelformset_factory(
	Personal,
	form=PersonalForm,
	extra=0,
	min_num=1,
	validate_min=True,
)

class CambioDeEquiposForm(ModelForm):
	class Meta:
		model = CambioDeEquipos
		fields = ['antenas_actual', 'antenas', 'enlaces_actual', 'enlaces', 'rru_actual', 'rru', 'piso', 'energia']
		labels = {
			'antenas': 'Antenas RF',
			'enlaces': 'Radioenlaces',
			'rru': 'RRU',
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		placeholders = {
			'antenas_actual': 'Detalle cantidad y dimensiones de antenas',
			'antenas': 'Detalle cantidad y dimensiones de antenas',
			'enlaces_actual': 'Detalle cantidad y dimensiones de radioenlaces',
			'enlaces': 'Detalle cantidad y dimensiones de radioenlaces',
			'rru_actual': 'Detalle cantidad y dimensiones de RRU',
			'rru': 'Detalle cantidad y dimensiones de RRU',
			'piso': 'Detalle superficie total a ocupar luego de la instalación',
		}
		for field in ['antenas_actual', 'antenas', 'enlaces_actual', 'enlaces', 'rru_actual', 'rru', 'piso']:
			self.fields[field].widget = resizable_textarea(2)
			self.fields[field].required = True
			self.fields[field].help_text = placeholders.get(field, '')
		self.fields['energia'].widget.attrs.update({
			'class': 'form-control',
			'placeholder': 'Potencia máxima que consumirá el sitio, en kW',
			'autocomplete': 'off',
			'min': '1',
			'max': '50',
		})
		self.fields['energia'].required = True

class OCForm(ModelForm):
	class Meta:
		model = OC
		fields = ['numero', 'moneda', 'condicion', 'contratista', 'costo']
		labels = {
			'numero': 'N° de OC',
			'moneda': 'Moneda',
			'condicion': 'Condición',
			'contratista': 'Contratista',
			'costo': 'Costo',
		}
		widgets = {
			'numero': TextInput(attrs={'class': 'form-control'}),
			'moneda': Select(attrs={'class': "form-control", 'style': "max-width: fit-content;"}),
			'condicion': Select(attrs={'class': 'form-control'}),
			'contratista': TextInput(attrs={'class': 'form-control'}),
			'costo': TextInput(attrs={
				'class': 'form-control',
				'autocomplete': 'off',
				'min': '0.00',
				'step': '1000.00',
				'inputMode': 'decimal',
				'placeholder': '0',
			}),
		}

	def clean(self):
		cleaned_data = super().clean()
		if not cleaned_data['numero'] and not cleaned_data['contratista'] and not cleaned_data['costo']:
			raise ValidationError('')