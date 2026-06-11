from tkts.tests import TktsBaseTestCase 
from tkts.constants import estados
from tkts.models import Usuario
from tkts.forms import TicketUpdateForm
from logger.models import TicketChangeLog as TicketChangeLogModel
import datetime
import typing


# Create your tests here.
class TicketChangeLogTests(TktsBaseTestCase):
	def test_log(self):
		# Create a Usuario (test user)
		user = Usuario.objects.create_user(username='tester', password='secret')
		ticket = self.create_ticket()
		
		# Create new instances for ref fields
		new_motivo = self.create_motivo(nombre='Motivo Nuevo')
		new_cliente = self.create_cliente(nombre='Cliente Nuevo')
		group = self.create_group('Staff')
		new_usuario = Usuario.objects.create_user(username='assigned', password='secret')
		new_usuario.groups.add(group)
		
		# Build update payload with changes for each field type
		programada_date = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
		data = self.build_update_payload(
			ticket,
			# const field (estado)
			estado=2,
			# ref fields
			motivo=new_motivo.pk,
			cliente=new_cliente.pk,
			usuario_asignado=new_usuario.pk,
			# number field (prioridad)
			prioridad=1,
			# long_text field (problema)
			problema='Problema actualizado con más detalles',
			# date field (programada)
			programada=programada_date,
			# add_text fields
			solucion_agregar='Sol agregada 1',
			observaciones_agregar='Obs agregada 1',
		)
		
		# Create and validate the form
		form = TicketUpdateForm(data, instance=ticket, user=user)
		self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
		
		# Save the form to update the ticket
		form.save()
		
		# Reload the ticket to get updated values
		ticket.refresh_from_db(from_queryset=None)
		
		# Log the changes
		TicketChangeLogModel.log(user, ticket, form)
		
		# Verify the log was created
		logs = TicketChangeLogModel.objects.filter(user=user, ticket=ticket)
		self.assertEqual(logs.count(), 1)
		
		# Get the log  
		log = logs.first()
		log = typing.cast(TicketChangeLogModel, log)
		self.assertIsNotNone(log.changed_data)
		self.assertTrue(len(log.changed_data) > 0, "No changes were logged")
		
		# Assert each field type was logged correctly
		
		# 1. const field (estado) - should have 'de' and 'a' with estado names
		self.assertIn('Estado', log.changed_data)
		self.assertIn('de', log.changed_data['Estado'])
		self.assertIn('a', log.changed_data['Estado'])
		self.assertEqual(log.changed_data['Estado']['a'], estados[2].nombre)
		
		# 2. ref field (motivo) - should reference the new motivo
		self.assertIn('Motivo', log.changed_data)
		self.assertIn('de', log.changed_data['Motivo'])
		self.assertIn('a', log.changed_data['Motivo'])
		self.assertEqual(log.changed_data['Motivo']['a'], new_motivo.__str__())
		
		# 3. ref field (cliente) - should reference the new cliente
		self.assertIn('Cliente', log.changed_data)
		self.assertEqual(log.changed_data['Cliente']['a'], new_cliente.__str__())
		
		# 4. ref field (usuario_asignado) - should reference the new usuario
		self.assertIn('Usuario Asignado', log.changed_data)
		self.assertEqual(log.changed_data['Usuario Asignado']['a'], new_usuario.__str__())
		
		# 5. number field (prioridad) - should have the new value
		self.assertIn('Prioridad', log.changed_data)
		self.assertEqual(log.changed_data['Prioridad']['a'], 1)
		
		# 6. long_text field (problema) - should show unified diff
		self.assertIn('Detalle', log.changed_data)
		self.assertIn('de', log.changed_data['Detalle'])
		self.assertIn('a', log.changed_data['Detalle'])
		
		# 7. date field (programada) - should show formatted dates
		self.assertIn('Fecha programada de cierre', log.changed_data)
		self.assertIn('a', log.changed_data['Fecha programada de cierre'])
		
		# 8. add_text fields (solucion_agregar, observaciones_agregar)
		self.assertIn('Solución', log.changed_data)
		self.assertIn('agregado', log.changed_data['Solución'])
		self.assertEqual(log.changed_data['Solución']['agregado'], 'Sol agregada 1')
		
		self.assertIn('Observaciones', log.changed_data)
		self.assertIn('agregado', log.changed_data['Observaciones'])
		self.assertEqual(log.changed_data['Observaciones']['agregado'], 'Obs agregada 1')