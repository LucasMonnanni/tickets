import base64
import urllib.parse
import datetime
from django.shortcuts import render, get_object_or_404
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, Http404, QueryDict
from django.http.response import JsonResponse
from django.template.response import TemplateResponse
from django.views import View
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Avg, Min, Max
from django.db.models.query import QuerySet
from django.db import transaction
import folium
from folium.plugins import MarkerCluster

from logger.models import TicketChangeLog
from sitios.models import Sitio
from .constants import transiciones_auto, transiciones_permitidas, estados, Notificacion as Ntfc
from .models import *
from .forms import TicketForm, TicketUpdateForm, AccesoForm, PersonalFormSet, CambioDeEquiposForm, OCForm


from typing import cast


class IndexView(TemplateView):
	template_name = 'tkts/index.html'
	def get_context_data(self, **kwargs):
		kwargs.setdefault("view", self)
		return kwargs

class TicketCreate(CreateView):
	model = Ticket
	form_class = TicketForm
		
	def get(self, request, *args, **kwargs):
		if 'sitio_id' in request.GET:
			sitio_id = int(request.GET['sitio_id'])
			self.initial['sitio'] = Sitio.objects.get(pk=sitio_id)
		return super().get(request, *args, **kwargs)
		
	def get_success_url(self):
		return f'/ticket/?id={self.object.id}&email={self.object.email}'
		
	@transaction.atomic
	def form_valid(self, form):
		motivo = cast(Motivo,\
				form.cleaned_data.get('motivo'))
		if motivo.nombre == 'ACCESO':
			acceso_form = AccesoForm(self.request.POST)
			personal_formset = PersonalFormSet(
				self.request.POST,
				prefix="personal",
				queryset=Personal.objects.none()
			)
			
			if not acceso_form.is_valid():
				return self.form_invalid(form)
			
			valid_personal = 0
			for p_form in personal_formset:
				if p_form.is_valid() and p_form.cleaned_data:
					valid_personal += 1
			
			if valid_personal == 0:
				personal_formset.non_form_errors().append('Debe ingresar al menos una persona')
				return self.form_invalid(form)
			
			
			acceso = acceso_form.save(commit=True)
			for p_form in personal_formset:
				if p_form.is_valid() and p_form.cleaned_data:
					personal = p_form.save(commit=False)
					personal.acceso = acceso
					# Being a boolean value, aprobado defaults to false because it is not present in the form
					personal.aprobado = True
					personal.save()
			ticket = form.save(commit=False)
			ticket.acceso = acceso
		
		elif motivo.nombre == 'CAMBIO DE EQUIPOS':
			cambio_form = CambioDeEquiposForm(self.request.POST)
			
			if not cambio_form.is_valid():
				return self.form_invalid(form)
			
			cambio = cambio_form.save(commit=False)
			cambio.save()
			
			ticket = form.save(commit=False)
			ticket.cambio_de_equipos = cambio
		
		else:
			ticket = form.save(commit=False)

		for transicion in transiciones_auto:
			if transicion.validar(ticket)[0]:
				ticket.estado = transicion.hacia
				changed_data = transicion.aplicar(ticket)
				ticket.save()
				TicketChangeLog.objects.create(user=Usuario.objects.get_or_create(username='Auto')[0], ticket=ticket, changed_data=changed_data).save()
				
				Ticket.enviar_notificaciones.after_response(ticket, transicion.notificaciones)
				self.object = ticket
				return HttpResponseRedirect(self.get_success_url())
		
		return self.form_invalid(form)
				

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		
		if self.request.method == 'POST' and not self.object:
			form = context.get('form')
			if form and hasattr(form, 'cleaned_data') and form.cleaned_data:
				motivo = form.cleaned_data.get('motivo')
				if motivo:
					if motivo.nombre == 'ACCESO':
						context['acceso_form'] = AccesoForm(self.request.POST)
						context['personal_formset'] = PersonalFormSet(
							self.request.POST,
							queryset=Personal.objects.none(),
							prefix="personal"
						)
					elif motivo.nombre == 'CAMBIO DE EQUIPOS':
						context['cambio_form'] = CambioDeEquiposForm(self.request.POST)
		
		return context

def motivo_subform(request):
	motivo = request.GET.get('motivo', '')
	form = TicketForm(initial=request.GET)
	context = {}
	context['form'] = form
	template_name = 'tkts/partials/motivo_default.html'

	if motivo == 'ACCESO':
		template_name = 'tkts/partials/motivo_acceso.html'
		context['acceso_form'] = AccesoForm()
		context['personal_formset'] = PersonalFormSet(
			queryset=Personal.objects.none(),
			initial=[{
				'nombre': '', 'apellido': '', 'dni': '', 'telefono': ''
			}],
			prefix="personal"
		)
	elif motivo == 'CAMBIO DE EQUIPOS':
		template_name = 'tkts/partials/motivo_cambio.html'
		context['cambio_form'] = CambioDeEquiposForm()
	return TemplateResponse(request, template_name, context)

class TicketDetail(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
	model = Ticket
	form_class = TicketUpdateForm
	template_name_suffix = '_detail'
	success_message = 'El Ticket se actualizó con éxito'
	initial = {}

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs['user'] = Usuario.objects.get(pk=self.request.user.pk)
		return kwargs

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		ticket = cast(Ticket, self.object)

		if ticket.acceso:
			context['acceso'] = ticket.acceso
			context['acceso_form'] = AccesoForm(instance=ticket.acceso)
			personal = ticket.acceso.personal.all()
			context['personal_formset'] = PersonalFormSet(queryset=personal, prefix="personal")
		elif ticket.cambio_de_equipos:
			context['cambio_form'] = CambioDeEquiposForm(instance=ticket.cambio_de_equipos)
		elif ticket.oc:
			context['oc_form'] = OCForm(instance=ticket.oc)
		else:
			context['oc_form'] = OCForm()
		return context

	def form_valid(self, form):
		ticket = cast(Ticket, self.object)
		if ticket.acceso:
			acceso_form = AccesoForm(self.request.POST, instance=ticket.acceso)
			personal = ticket.acceso.personal.all()
			personal_formset = PersonalFormSet(self.request.POST, queryset=personal, prefix='personal')
			if personal_formset.has_changed() and personal_formset.is_valid():
				personal_formset.save()
			if acceso_form.has_changed() and acceso_form.is_valid():
				acceso_form.save()
		else:
			acceso_form = None
			personal_formset = None

		if ticket.cambio_de_equipos:
			cambio_form = CambioDeEquiposForm(self.request.POST, instance=ticket.cambio_de_equipos)
		else:
			cambio_form = None

		oc_form = OCForm(self.request.POST, instance=ticket.oc)
		if oc_form.is_valid():
			oc = oc_form.save()
			if not ticket.oc:
				ticket.oc = oc
				ticket.save()
		else:
			if oc_form.cleaned_data['numero'] or oc_form.cleaned_data['contratista'] or oc_form.cleaned_data['costo']:
				return self.render_to_response({
					'form': form,
					'object': ticket,
					'oc_form': oc_form,
					'acceso': ticket.acceso,
					'acceso_form': acceso_form,
					'personal_formset': personal_formset,
					'cambio_form': cambio_form,
				})
			elif ticket.oc:
					oc: OC = ticket.oc
					ticket.oc = None
					ticket.save()
					oc.delete()

		if not form.changed_data:
			return super().form_valid(form)

		if form.fields['estado'].initial == form.cleaned_data['estado']:
			notificaciones = ticket.estado.notificaciones
			fields = ticket.estado.campos_a_notificar
			if not any([field in form.changed_data for field in fields]):
				notificaciones = []
			return self.form_changed_and_valid(form, notificaciones)

		try:
			# Find the transicion in transiciones_permitidas that matches the state change
			permitida = next(
				t for t in transiciones_permitidas 
				if t.desde == form.fields['estado'].initial and t.hacia == form.cleaned_data['estado']
			)
		except StopIteration:
			form.add_error(
				None,
				ValidationError(_('No hay ninguna transición definida hacia ese estado.'), code='prohibida')
			)
			return self.form_invalid(form)

		res, errors = permitida.validar(ticket)
		if res:
			permitida.aplicar(ticket)
			ticket.save()
			return self.form_changed_and_valid(form, permitida.notificaciones)
		else:
			prefix = estados[permitida.desde].nombre + ' -> ' + estados[permitida.hacia].nombre + ': '
			for campo in errors:
				if campo != 'oc':
					form.add_error(
						campo,
						ValidationError(prefix + _(errors[campo]), code='prohibida')
					)
				else:
					oc_form.add_error(
						None,
						ValidationError(prefix + _(errors[campo]), code='prohibida')
					)
		return self.render_to_response({
			'form': form,
			'object': ticket,
			'oc_form': oc_form,
			'acceso': ticket.acceso,
			'acceso_form': acceso_form,
			'personal_formset': personal_formset,
			'cambio_form': cambio_form,
		})

	def form_changed_and_valid(self, form: TicketUpdateForm, notificaciones: list[Ntfc]):
		ticket = cast(Ticket, self.object)
		if notificaciones:
			Ticket.enviar_notificaciones.after_response(ticket, notificaciones)
		TicketChangeLog.log(self.request.user, ticket, form)
		return super().form_valid(form)

from tickets.services import generar_permiso_en_bluetooth
@login_required
@require_GET
def generar_permisos(request: HttpRequest, pk: int):
	ticket = get_object_or_404(Ticket, pk=pk)
	sitio = ticket.sitio

	tiene_bluetooth = sitio.candado_calle == 'BLUETOOTH' or sitio.candado_sitio == 'BLUETOOTH'
	tiene_numerico = sitio.candado_calle == 'NUMÉRICO' or sitio.candado_sitio == 'NUMÉRICO'
	tiene_llave = sitio.candado_calle in ['ACYTRA', 'OTRO'] or sitio.candado_sitio in ['ACYTRA', 'OTRO']
	aviso_propietario = sitio.aviso or sitio.acceso == 'LOCADOR'

	mensaje = datetime.datetime.now().strftime('%d/%m/%y %H:%M') + ' - Auto: '

	acceso = ticket.acceso
	if not acceso:
		raise
	if tiene_bluetooth:
		personal_autorizado = acceso.personal.filter(aprobado=True)
		codigo, error = generar_permiso_en_bluetooth(acceso, personal_autorizado)
 
		if codigo != 200:
			context = {
				'readonly': False,
				'object': ticket,
				'form': TicketUpdateForm(instance=ticket),
				'acceso_form': AccesoForm(instance=acceso),
				'personal_formset': PersonalFormSet(queryset=acceso.personal.all(), prefix="personal"),
				'error': error,
			}
			return render(request, 'tkts/partials/ticket_detail_acceso.html', context)
		mensaje += 'El sitio tiene un candado Bluetooth accionado con la app WiKey, en esta misma página figuran las credenciales.\n'
	if tiene_numerico:
		mensaje += f'El sitio tiene un candado numérico con combinación {sitio.combinacion}.\n'
	if tiene_llave or aviso_propietario:
		mensaje += 'Por favor comuniquese con Alejandro Clavaschino al +549 11 5967-0537 '
		if tiene_llave:
			mensaje += 'para procurar las llaves'
			if aviso_propietario:
				mensaje += ' y coordinar el ingreso'
		elif aviso_propietario:
			mensaje += 'para coordinar el ingreso'
		mensaje += '.\n'
	changed_data = {
		'Solución': { 'Agregado': mensaje[:-1] },
		'Usuario asignado': { 'de': str(ticket.usuario_asignado) },
		'Fecha de cierre': { 'a': timezone.now().strftime("%d/%m/%y") },
		'Estado': { 'de': ticket.estado.nombre, 'a': 'Cerrado' },
	}
	ticket.solucion = (ticket.solucion + '\n' if ticket.solucion else '') + mensaje[:-1] # removing trailing \n.
	ticket.usuario_asignado = None
	ticket.cierre = datetime.date.today()
	ticket._estado_id = 5  # Acc Cerrado (Acceso Cerrado) - index 5 in estados list
	ticket.save()
	acceso.permiso_generado = True
	acceso.save()
	return HttpResponse(headers={'HX-Redirect': reverse('detalle', args=[ticket.pk])})

def historial(request: HttpRequest, pk: int):
	cambios = Ticket.objects.get(pk=pk).cambios.all().order_by('-timestamp').prefetch_related('user')
	paginator = Paginator(cambios, 10)
	page_n = request.GET.get('page', '0')
	page = paginator.get_page(page_n)
	return render(request, 'tkts/partials/ticket_detail_historial.html', {'page': page, 'ticket_pk': pk})

class TicketDetailShort(TemplateView):
	template_name = 'tkts/ticket_detail_short.html'
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		try:
			obj = Ticket.objects.get(pk = self.request.GET['id'], email = self.request.GET['email'])
		except:
			raise Http404('No se encontró el ticket solicitado')
		context['object'] = obj
		return context

def filter_qs_by_getattrs(tkts: 'QuerySet[Ticket]', get: QueryDict) -> 'QuerySet[Ticket]':
		get._mutable = True
		order = get.pop('order', ['-inicio'])[0]
		tkts = tkts.order_by(order)
		filters = {}
		excludes = {}
		for key in get:
			if key == 'page':
				continue
			value = get.getlist(key, ['True'])
			value = [urllib.parse.unquote_plus(v) for v in value]
			# Handle estado filter: convert estado name(s) to _estado_id index(es)
			if key == 'estado':
				key = '_estado_id'
				value = [i for v in value for i, e in enumerate(estados) if e.nombre == v]
			if len(value) == 1:
				value = value[0]
			else:
				key += '__in'
			if key.endswith('isnull'):
				if isinstance(value, str):
					value = value.lower() in ['1', 'true', 't', 'yes', 'on']
				else:
					value = bool(value)
			if key.startswith('not__'):
				excludes[key[5:]] = value
			else:
				filters[key] = value
		return tkts.filter(**filters).exclude(**excludes)

from typing import Literal
FilterSpec = tuple[str, str, Literal['ref', 'string', 'numero']]

def get_unique_values_for_filters(tkts: 'QuerySet[Ticket]', filters: list[FilterSpec]) -> dict:
	unique_values = {}
	for field_name, field_title, field_type in filters:
		unique_values[field_name] = {
			'nombre': field_title,
			'tipo': field_type,
			'valores': list(set(tkts.filter(**{field_name+'__isnull': False}).values_list(field_name, flat=True)))
		}
	return unique_values

class TicketListView(LoginRequiredMixin, ListView):
	model = Ticket
	paginate_by = 100
	paginate_orphans = 10
	def get_queryset(self):
		tkts = Ticket.objects.filter(acceso__isnull = True).select_related('sitio', 'motivo', 'cliente', 'usuario_asignado', 'oc')
		tkts = filter_qs_by_getattrs(tkts, self.request.GET)
		filters: list[FilterSpec] = [
			('sitio__sigla_id', 'Sitio', 'ref'),
			('nombre', 'Nombre', 'string'),
			('cliente__nombre', 'Cliente', 'ref'),
			('motivo__nombre', 'Motivo', 'ref'),
			('programada', 'Fecha programada', 'numero'),
			('cierre', 'Fecha de cierre', 'numero'),
			('oc__costo', 'Costo', 'numero'),
			('oc__numero', 'OC', 'string'),
			('prioridad', 'Prioridad', 'numero'),
			('usuario_asignado__last_name', 'Usuario asignado', 'ref'),
			('sitio__provincia', 'Sitio > Provincia', 'string'),
			('sitio__proyecto', 'Sitio > Proyecto', 'string'),
			('sitio__tipo', 'Sitio > Tipo', 'string'),
			('sitio__estado', 'Sitio > Estado', 'string'),
			('sitio__proyecto', 'Sitio > Proyecto', 'string'),
		]
		unique_values = get_unique_values_for_filters(tkts, filters)		
		unique_values['estado'] = {
			'nombre': 'Estado',
			'tipo': 'ref',
			'valores': [e.nombre for i, e in enumerate(estados) if not e.acceso]
		}
		self.extra_context = {'fields': unique_values}
		return tkts.prefetch_related()

class AccesoListView(LoginRequiredMixin, ListView):
	model = Ticket
	paginate_by = 100
	paginate_orphans = 10
	def get_queryset(self):
		tkts = Ticket.objects.filter(acceso__isnull = False).select_related('sitio', 'motivo', 'cliente', 'usuario_asignado', 'oc')
		tkts = filter_qs_by_getattrs(tkts, self.request.GET)
		filters: list[FilterSpec] = [
			('sitio__sigla_id', 'Sitio', 'ref'),
			('nombre', 'Nombre', 'string'),
			('cliente__nombre', 'Cliente', 'ref'),
			('programada', 'Fecha programada', 'numero'),
			('cierre', 'Fecha de cierre', 'numero'),
			('prioridad', 'Prioridad', 'numero'),
			('usuario_asignado__last_name', 'Usuario asignado', 'ref'),
			('sitio__provincia', 'Sitio > Provincia', 'string'),
			('sitio__proyecto', 'Sitio > Proyecto', 'string'),
			('sitio__tipo', 'Sitio > Tipo', 'string'),
			('sitio__estado', 'Sitio > Estado', 'string'),
			('sitio__proyecto', 'Sitio > Proyecto', 'string'),
			('acceso__personal__apellido', 'Personal > Apellido', 'string'),
			('acceso__personal__dni', 'Personal > DNI', 'numero'),
			('acceso__personal__telefono', 'Personal > Teléfono', 'numero'),
		]
		unique_values = get_unique_values_for_filters(tkts, filters)		
		unique_values['estado'] = {
			'nombre': 'Estado',
			'tipo': 'ref',
			'valores': [e.nombre for i, e in enumerate(estados) if e.acceso]
		}
		self.extra_context = {'fields': unique_values}
		return tkts.prefetch_related()

class TicketMapView(LoginRequiredMixin, TemplateView):
	template_name = 'tkts/ticket_map.html'
	colors = {
		0: 'darkred',
		1: 'orange',
		2: 'darkgreen',
		3: 'darkgreen',
	}
		
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		tkts = TicketListView.get_queryset(self).values_list('id', 'sitio__id', 'sitio__latitud', 'sitio__longitud', 'motivo__nombre', 'prioridad')
		aggregates = tkts.aggregate(avg_lat = Avg('sitio__latitud'), avg_long = Avg('sitio__longitud'),\
				min_lat = Min('sitio__latitud'), min_long = Min('sitio__longitud'),\
				max_lat = Max('sitio__latitud'), max_long = Max('sitio__longitud'))
		figure = folium.Figure()
		
		map = folium.Map(
			location = [aggregates['avg_lat'], aggregates['avg_long']],
			zoom_start = 5,
			min_lat=aggregates['min_lat'],
			max_lat=aggregates['max_lat'],
			min_lon=aggregates['min_long'],
			max_lon=aggregates['max_long'],
			tiles = 'Cartodb Positron',
		)
		
		cluster = MarkerCluster(control=False, options={'maxClusterRadius': 20})
		map.add_child(cluster)

		for tkt in tkts:
			color = self.colors.get(tkt[5], 'darkgreen')
			folium.Marker(
				location=tkt[2:4],
				icon=folium.Icon(color = color, prefix='fa',icon='bullseye'),
				popup=f'<a href="/tickets/{tkt[0]}">Tkt #{tkt[0]}</a>',
				tooltip=f'Ticket N°{tkt[0]} - {tkt[1]} - {tkt[4]}'
			).add_to(cluster)

		map.add_to(figure)
		figure.render()
		context['map'] = figure
		del figure.header._children['bootstrap'] 
		del figure.header._children['bootstrap_css']
		del figure.header._children['glyphicons_css']
		context.update(self.extra_context)
		context['is_map'] = True
		return context	 

class APIView(View):
	def get(self, request):
		user = None
		if 'HTTP_AUTHORIZATION' in request.META:
			auth = request.META['HTTP_AUTHORIZATION'].split()
			if len(auth) == 2:
				if auth[0].lower() == "basic":
					uname, passwd = base64.b64decode(auth[1]).decode('ascii').split(':')
					user = authenticate(username = uname, password = passwd)
		if user is None:
			return HttpResponse(status = 403)
		
		login(request, user)
		request.user = user
		tkts = list(Ticket.objects.values())
		response = JsonResponse(tkts, safe = False)
		return response

class SetThemeView(View):
	def get(self, request):
		theme = request.GET.get('theme')
		if theme:
			request.session['theme'] = theme
			return JsonResponse({'status': 'success'})
		else:
			return JsonResponse({'status': 'error'})
