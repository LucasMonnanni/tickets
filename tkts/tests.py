import base64
import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth.models import Group, User
from django.http import QueryDict
from django.test import TestCase
from django.urls import reverse

from ntfcs.models import Notificacion as NotificacionModel
from sitios.models import Sitio
from tkts.constants import Notificacion as NotificationSpec, estados
from tkts.models import Acceso, Cliente, Motivo, OC, Personal, Ticket, Usuario
from tkts.views import filter_qs_by_getattrs, get_unique_values_for_filters


class TktsBaseTestCase(TestCase):
	def create_group(self, name='Staff'):
		group, _ = Group.objects.get_or_create(name=name)
		return group

	def create_user(self, username='tester', password='secret', groups=None, **kwargs):
		defaults = {
			'email': f'{username}@example.com',
			'first_name': kwargs.pop('first_name', 'Test'),
			'last_name': kwargs.pop('last_name', 'User'),
		}
		defaults.update(kwargs)
		user = User.objects.create_user(username=username, password=password, **defaults)
		for group in groups or []:
			if isinstance(group, Group):
				user.groups.add(group)
			else:
				user.groups.add(self.create_group(group))
		return user

	def create_sitio(self, **kwargs):
		index = Sitio.objects.count() + 1
		defaults = {
			'id': f'ARG-{index:05d}',
			'nombre': f'Sitio {index}',
			'direccion': 'Calle 123',
			'localidad': 'Ciudad',
			'municipio': 'Municipio',
			'provincia': Sitio.Provincias.CABA,
			'latitud': Decimal('-34.603722'),
			'longitud': Decimal('-58.381592'),
			'proyecto': 'Proyecto',
			'tipo': 'Macro',
			'estructura': 'Torre',
			'altura': 30,
			'acceso': Sitio.Accesos.INDEPENDIENTE,
			'aviso': False,
			'candado_calle': Sitio.Candados.NA,
			'candado_sitio': Sitio.Candados.NA,
			'combinacion': None,
			'conflicto': False,
			'procedimiento': '',
			'estado': Sitio.Estados.ACTIVO,
		}
		defaults.update(kwargs)
		return Sitio.objects.create(**defaults)

	def create_cliente(self, nombre=None, **kwargs):
		index = Cliente.objects.count() + 1
		defaults = {
			'nombre': nombre or f'Cliente {index}',
			'visible': True,
		}
		defaults.update(kwargs)
		return Cliente.objects.create(**defaults)

	def create_motivo(self, nombre=None, **kwargs):
		index = Motivo.objects.count() + 1
		defaults = {
			'nombre': nombre or f'Motivo {index}',
			'visible': True,
		}
		defaults.update(kwargs)
		return Motivo.objects.create(**defaults)

	def create_acceso(self, **kwargs):
		defaults = {
			'fecha_desde': datetime.date.today(),
			'fecha_hasta': datetime.date.today() + datetime.timedelta(days=1),
			'hora_desde': datetime.time(8, 0),
			'hora_hasta': datetime.time(18, 0),
			'empresa': 'Acme',
			'afectacion': False,
			'riesgo_electrico': False,
			'altura': False,
			'permiso_generado': False,
		}
		defaults.update(kwargs)
		return Acceso.objects.create(**defaults)

	def create_ticket(self, **kwargs):
		defaults = {
			'nombre': 'Juan Perez',
			'email': 'ticket@example.com',
			'telefono': 1234567890,
			'cliente': kwargs.pop('cliente', None) or self.create_cliente(),
			'sitio': kwargs.pop('sitio', None) or self.create_sitio(),
			'motivo': kwargs.pop('motivo', None) or self.create_motivo(),
			'prioridad': None,
			'problema': 'Detalle inicial',
			'link': '',
			'solucion': '',
			'programada': None,
			'cierre': None,
			'usuario_asignado': None,
			'observaciones': '',
			'_estado_id': 0,
		}
		defaults.update(kwargs)
		return Ticket.objects.create(**defaults)

	def build_update_payload(self, ticket, **overrides):
		payload = {
			'estado': ticket._estado_id,
			'cliente': ticket.cliente_id,
			'sitio': ticket.sitio_id,
			'motivo': ticket.motivo_id,
			'prioridad': ticket.prioridad if ticket.prioridad is not None else '',
			'problema': ticket.problema,
			'solucion': ticket.solucion or '',
			'programada': ticket.programada.isoformat() if ticket.programada else '',
			'cierre': ticket.cierre.isoformat() if ticket.cierre else '',
			'usuario_asignado': ticket.usuario_asignado_id or '',
			'observaciones': ticket.observaciones or '',
			'solucion_agregar': '',
			'observaciones_agregar': '',
			'numero': ticket.oc.numero if ticket.oc else '',
			'moneda': ticket.oc.moneda if ticket.oc else OC.Monedas.ARS,
			'condicion': ticket.oc.condicion if ticket.oc else OC.Condiciones.NETO_30,
			'contratista': ticket.oc.contratista if ticket.oc else '',
			'costo': str(ticket.oc.costo) if ticket.oc and ticket.oc.costo is not None else '',
		}
		payload.update(overrides)
		return payload


class TicketModelTests(TktsBaseTestCase):
	def test_ticket_estado_property_round_trip_with_index_and_estado_object(self):
		ticket = self.create_ticket()

		self.assertEqual(ticket.estado, estados[0])

		ticket.estado = 2
		self.assertEqual(ticket._estado_id, 2)

		ticket.estado = estados[3]
		self.assertEqual(ticket._estado_id, 3)

	def test_ticket_estado_setter_rejects_unknown_estado(self):
		ticket = self.create_ticket()

		with self.assertRaisesMessage(ValueError, 'not found in estados list'):
			ticket.estado = SimpleNamespace(nombre='Inventado')

	def test_usuario_str_prefers_initial_and_last_name(self):
		user = self.create_user(username='jperez', first_name='juan', last_name='perez')

		self.assertEqual(str(Usuario.objects.get(pk=user.pk)), 'J. Perez')

	def test_usuario_str_falls_back_to_username(self):
		user = self.create_user(username='sin_nombre', first_name='', last_name='')

		self.assertEqual(str(Usuario.objects.get(pk=user.pk)), 'sin_nombre')

	def test_acceso_personal_properties_split_by_aprobado(self):
		acceso = self.create_acceso()
		approved = Personal.objects.create(acceso=acceso, nombre='Ana', apellido='Lopez', dni=12345678, telefono=1111111111, aprobado=True)
		pending = Personal.objects.create(acceso=acceso, nombre='Beto', apellido='Perez', dni=23456789, telefono=1222222222, aprobado=False)

		self.assertQuerySetEqual(acceso.personal_aprobado.order_by('pk'), [approved], transform=lambda obj: obj)
		self.assertQuerySetEqual(acceso.personal_no_aprobado.order_by('pk'), [pending], transform=lambda obj: obj)

	def test_personal_password_strips_spaces_title_cases_and_pads(self):
		acceso = self.create_acceso()
		personal = Personal.objects.create(
			acceso=acceso,
			nombre='Ana',
			apellido='de la   cruz',
			dni=12345678,
			telefono=1111111111,
		)

		self.assertEqual(personal.password, 'Delacru8!')

	def test_ticket_get_public_query_includes_id_and_email(self):
		ticket = self.create_ticket(email='publico@example.com')

		self.assertEqual(ticket.get_public_query(), f'?id={ticket.pk}&email=publico@example.com')

	def test_enviar_notificaciones_returns_zero_when_list_is_empty(self):
		ticket = self.create_ticket()

		self.assertEqual(Ticket.enviar_notificaciones(ticket, []), 0)

	def test_enviar_notificaciones_collects_ticket_group_and_user_recipients(self):
		ticket = self.create_ticket(email='ticket@example.com')
		group = self.create_group('Supervisor Mantenimiento')
		self.create_user(username='supervisor', email='supervisor@example.com', groups=[group])
		self.create_user(username='ingresos_auto', email='ingresos@example.com')
		NotificacionModel.objects.create(
			nombre='Actualizado',
			asunto_template='Asunto',
			texto_template='Texto',
			html_template='<p>Html</p>',
		)
		connection = Mock()
		connection.send_messages.return_value = 1

		with patch('tkts.models.get_connection', return_value=connection), \
				patch('ntfcs.models.Notificacion.crear_mail', autospec=True, side_effect=lambda _self, _ticket, to, cc: SimpleNamespace(to=to, cc=cc)) as crear_mail:
			result = Ticket.enviar_notificaciones(
				ticket,
				[
					NotificationSpec(
						nombre='Actualizado',
						para={'ticket_email': True, 'grupos': ['Mantenimiento', 'Supervisor Mantenimiento'], 'usuarios': ['ingresos_auto']},
						cc={'usuarios': ['ingresos_auto']},
					)
				],
			)

		self.assertEqual(result, 1)
		self.assertEqual(crear_mail.call_count, 1)
		_, _, to, cc = crear_mail.call_args.args
		self.assertCountEqual(to, ['ticket@example.com', 'supervisor@example.com', 'ingresos@example.com'])
		self.assertEqual(cc, ['ingresos@example.com'])
		connection.send_messages.assert_called_once()


class TicketQueryHelperTests(TktsBaseTestCase):
	def test_filter_qs_by_getattrs_maps_estado_name_to_estado_id(self):
		open_ticket = self.create_ticket(_estado_id=0)
		closed_ticket = self.create_ticket(_estado_id=2, email='closed@example.com')
		query = QueryDict('estado=Cerrado')

		result = filter_qs_by_getattrs(Ticket.objects.all(), query)

		self.assertQuerySetEqual(result.order_by('pk'), [closed_ticket], transform=lambda obj: obj)
		self.assertNotIn(open_ticket, result)

	def test_filter_qs_by_getattrs_supports_not_prefix_and_ignores_page(self):
		cliente_a = self.create_cliente(nombre='Cliente A')
		cliente_b = self.create_cliente(nombre='Cliente B')
		ticket_a = self.create_ticket(cliente=cliente_a)
		ticket_b = self.create_ticket(cliente=cliente_b, email='b@example.com')
		query = QueryDict('not__cliente__nombre=Cliente+A&page=2')

		result = filter_qs_by_getattrs(Ticket.objects.all(), query)

		self.assertQuerySetEqual(result.order_by('pk'), [ticket_b], transform=lambda obj: obj)
		self.assertNotIn(ticket_a, result)

	def test_filter_qs_by_getattrs_parses_isnull_false_correctly(self):
		with_oc = self.create_ticket(oc=OC.objects.create(numero='OC-1', contratista='Acme', costo=Decimal('1000.00')))
		without_oc = self.create_ticket(email='sinoc@example.com')
		query = QueryDict('oc__isnull=False')

		result = filter_qs_by_getattrs(Ticket.objects.all(), query)

		self.assertIn(with_oc, result)
		self.assertNotIn(without_oc, result)

	def test_get_unique_values_for_filters_excludes_nulls_and_deduplicates(self):
		cliente = self.create_cliente(nombre='Cliente Unico')
		self.create_ticket(cliente=cliente)
		self.create_ticket(cliente=cliente, email='otro@example.com')
		filters = [('cliente__nombre', 'Cliente', 'ref'), ('programada', 'Programada', 'numero')]

		result = get_unique_values_for_filters(Ticket.objects.all(), filters)

		self.assertEqual(result['cliente__nombre']['nombre'], 'Cliente')
		self.assertEqual(result['cliente__nombre']['tipo'], 'ref')
		self.assertEqual(result['cliente__nombre']['valores'], ['Cliente Unico'])
		self.assertEqual(result['programada']['valores'], [])


class PublicViewTests(TktsBaseTestCase):
	def test_motivo_subform_returns_acceso_partial_and_forms(self):
		response = self.client.get(reverse('ticket_motivo_subform'), {'motivo': 'ACCESO'})

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'tkts/partials/motivo_acceso.html')
		self.assertIn('acceso_form', response.context)
		self.assertIn('personal_formset', response.context)

	def test_motivo_subform_returns_cambio_partial(self):
		response = self.client.get(reverse('ticket_motivo_subform'), {'motivo': 'CAMBIO DE EQUIPOS'})

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'tkts/partials/motivo_cambio.html')
		self.assertIn('cambio_form', response.context)

	def test_ticket_detail_short_returns_404_for_wrong_email(self):
		ticket = self.create_ticket(email='correcto@example.com')

		response = self.client.get(reverse('detalle_publico'), {'id': ticket.pk, 'email': 'incorrecto@example.com'})

		self.assertEqual(response.status_code, 404)

	def test_api_view_returns_403_without_basic_auth(self):
		response = self.client.get(reverse('api'))

		self.assertEqual(response.status_code, 403)

	def test_api_view_returns_ticket_json_with_valid_basic_auth(self):
		self.create_ticket()
		self.create_user(username='apiuser', password='secret')
		credentials = base64.b64encode(b'apiuser:secret').decode('ascii')

		response = self.client.get(reverse('api'), HTTP_AUTHORIZATION=f'Basic {credentials}')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.json()), 1)
		self.assertEqual(response.json()[0]['email'], 'ticket@example.com')

	def test_set_theme_view_stores_theme_in_session(self):
		response = self.client.get(reverse('theme'), {'theme': 'dark'})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json(), {'status': 'success'})
		self.assertEqual(self.client.session['theme'], 'dark')


class TicketDetailViewTests(TktsBaseTestCase):
	def setUp(self):
		super().setUp()
		self.user = self.create_user(username='detalle', groups=['Staff'])
		self.client.force_login(self.user)

	def test_same_state_with_notifiable_change_triggers_notifications(self):
		ticket = self.create_ticket()
		payload = self.build_update_payload(ticket, programada='2026-06-15')

		with patch('tkts.views.TicketChangeLog.log') as change_log, \
				patch('tkts.views.Ticket.enviar_notificaciones.after_response') as notify:
			response = self.client.post(reverse('detalle', args=[ticket.pk]), payload)

		ticket.refresh_from_db()
		self.assertEqual(response.status_code, 302)
		self.assertEqual(ticket.programada, datetime.date(2026, 6, 15))
		change_log.assert_called_once()
		notify.assert_called_once()
		self.assertEqual(notify.call_args.args[0].pk, ticket.pk)
		self.assertEqual(notify.call_args.args[1], estados[0].notificaciones)

	def test_same_state_with_non_notifiable_change_skips_notifications(self):
		ticket = self.create_ticket()
		payload = self.build_update_payload(ticket, problema='Detalle actualizado')

		with patch('tkts.views.TicketChangeLog.log') as change_log, \
				patch('tkts.views.Ticket.enviar_notificaciones.after_response') as notify:
			response = self.client.post(reverse('detalle', args=[ticket.pk]), payload)

		ticket.refresh_from_db()
		self.assertEqual(response.status_code, 302)
		self.assertEqual(ticket.problema, 'Detalle actualizado')
		change_log.assert_called_once()
		notify.assert_not_called()

	def test_invalid_transition_rerenders_with_field_and_oc_errors(self):
		ticket = self.create_ticket()
		payload = self.build_update_payload(ticket, estado=1)

		with patch('tkts.views.TicketChangeLog.log') as change_log, \
				patch('tkts.views.Ticket.enviar_notificaciones.after_response') as notify:
			response = self.client.post(reverse('detalle', args=[ticket.pk]), payload)

		ticket.refresh_from_db()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(ticket._estado_id, 0)
		self.assertIn('cierre', response.context['form'].errors)
		self.assertIn('OC asociada', response.context['oc_form'].non_field_errors()[1])
		change_log.assert_not_called()
		notify.assert_not_called()

	def test_blank_oc_payload_removes_existing_oc(self):
		oc = OC.objects.create(numero='OC-1', contratista='Acme', costo=Decimal('1000.00'))
		ticket = self.create_ticket(oc=oc)
		payload = self.build_update_payload(ticket, numero='', contratista='', costo='')

		response = self.client.post(reverse('detalle', args=[ticket.pk]), payload)

		ticket.refresh_from_db()
		self.assertEqual(response.status_code, 302)
		self.assertIsNone(ticket.oc)
		self.assertFalse(OC.objects.filter(pk=oc.pk).exists())


class GenerarPermisosViewTests(TktsBaseTestCase):
	def setUp(self):
		super().setUp()
		self.user = self.create_user(username='permiso', groups=['Staff'])
		self.client.force_login(self.user)

	def test_generar_permisos_success_closes_ticket_and_marks_access(self):
		sitio = self.create_sitio(candado_calle=Sitio.Candados.NUMERICO, combinacion='1234')
		acceso = self.create_acceso()
		assigned = Usuario.objects.get(pk=self.user.pk)
		ticket = self.create_ticket(sitio=sitio, acceso=acceso, _estado_id=4, usuario_asignado=assigned)

		response = self.client.get(reverse('generar_permisos', args=[ticket.pk]))

		ticket.refresh_from_db()
		acceso.refresh_from_db()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.headers['HX-Redirect'], reverse('detalle', args=[ticket.pk]))
		self.assertEqual(ticket._estado_id, 5)
		self.assertIsNone(ticket.usuario_asignado)
		self.assertEqual(ticket.cierre, datetime.date.today())
		self.assertTrue(acceso.permiso_generado)
		self.assertIn('candado numérico con combinación 1234', ticket.solucion)

	def test_generar_permisos_bluetooth_error_renders_partial_with_error(self):
		sitio = self.create_sitio(candado_calle=Sitio.Candados.BLUETOOTH)
		acceso = self.create_acceso()
		Personal.objects.create(acceso=acceso, nombre='Ana', apellido='Lopez', dni=12345678, telefono=1111111111, aprobado=True)
		ticket = self.create_ticket(sitio=sitio, acceso=acceso, _estado_id=4)

		with patch('tkts.views.generar_permiso_en_bluetooth', return_value=(500, 'fallo api')):
			response = self.client.get(reverse('generar_permisos', args=[ticket.pk]))

		ticket.refresh_from_db()
		acceso.refresh_from_db()
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'tkts/partials/ticket_detail_acceso.html')
		self.assertContains(response, 'fallo api')
		self.assertEqual(ticket._estado_id, 4)
		self.assertFalse(acceso.permiso_generado)
