import requests
from urllib.parse import urlencode
from datetime import datetime, UTC
from django.core.cache import cache
from django.conf import settings
from django.db.models import QuerySet
from sitios.models import Sitio
from tkts.models import Acceso, Personal

class BluetoothError(Exception):
	code: int
	message: str
	def __init__(self, code = 400, message = 'Algo salió mal'):
		self.code = code
		self.message = message

def get_bluetooth_token(base_url: str) -> str:
	token = cache.get('bluetooth_token', None)
	if not token:
		token_response = requests.post(base_url+'identity/tokens', json={'username': settings.BLUETOOTH_API['USER'], 'password': settings.BLUETOOTH_API['PASSWORD']})
		if token_response.status_code != 200:
			raise BluetoothError()
		token = token_response.json()['token']['id']
		expiration_secs = (datetime.fromisoformat(token_response.json()['token']['expiresAt'])-datetime.now(UTC)).seconds
		expiration_secs -= 120
		cache.set(
			'token',
			token,
			expiration_secs
		)
	return token

def call_bluetooth_api(path: str, method: str, payload: dict = {}) -> tuple[int, dict]:
	base_url = settings.BLUETOOTH_API['URL'] + '/'
	token = get_bluetooth_token(base_url)
	headers = {
		'Authorization': 'Bearer ' + token
	}
	url = base_url + path
	if method=='POST':
		r = requests.post(url, json=payload, headers=headers)
	if method=='PATCH':
		r = requests.patch(url, json=payload, headers=headers)
	if method=='PUT':
		r = requests.put(url, json=payload, headers=headers)
	elif method=='GET':
		if payload:
			url += '?' + urlencode(payload)
		r = requests.get(url, headers=headers)
	if settings.DEBUG:
		import pprint
		print(f'Bluetooth {method} to {path} took: {r.elapsed.total_seconds()}s')
		print(f'\t\tand returned: {r.status_code}')
		print('Payload:')
		pprint.pprint(payload)
		print('Response:')
		pprint.pprint(r.json())
	return r.status_code, r.json()

def get_sitio_lock_count(sitio: str):
	code, data = call_bluetooth_api(
		'sites/get?timeZone=America/Argentina/Buenos_Aires',
		'POST',
		{'siteName': sitio}
	)
	if code == 404:
		raise BluetoothError(code, 'El sitio no existe en la base de datos de Bluetooth.')
	if code != 200:
		raise BluetoothError()
	try:
		locks = data['sites'][0]['locks']
	except KeyError:
		raise BluetoothError()
	return len(locks)

def is_mobile_taken(mobile: str) -> tuple[bool, str]:
	code, data = call_bluetooth_api(
		f'users/search?PHONE_NUMBER={mobile}',
		'GET'
	)
	if code != 200:
		raise BluetoothError()
	taken = len(data['users']) > 0
	user = data['users'][0]['fullName'] if taken else ''
	return taken, user

def create_user(acceso: Acceso, persona: Personal):
	user_data = {
		'username': persona.dni,
		'password': persona.password,
		'mobileNumber': '+549' + str(persona.telefono),
		'fullName': persona.apellido + ', ' + persona.nombre,
		'remarks': acceso.empresa,
		'mobileNumberEnabled': True,
		'accountEnabled': True
	}
	code, data = call_bluetooth_api('users', 'POST', user_data)
	if code != 200:
		if 'Invalid parameter: MobileNumber' in data.get('Message', ''):
			taken, user = is_mobile_taken(str(persona.telefono))
			if taken:
				raise BluetoothError(400, f'El teléfono indicado para {persona.apellido}, {persona.nombre} está siendo usado por {user}')
			else:
				raise BluetoothError(400, 'El número de teléfono indicado para {persona.apellido}, {persona.nombre} es inválido')
		else:
			raise BluetoothError(400, 'No se pudo crear el usuario ' + persona.apellido + ', ' + persona.nombre)

def update_user(persona: Personal, user_data: dict):
	if user_data['mobileNumber'][-10:] != str(persona.telefono):
		code, response = call_bluetooth_api('users/' + str(persona.dni), 'PATCH', {'mobileNumber': '+549' + str(persona.telefono)})
		message: str = response.get('Message', '')
		if code == 400 and message.startswith('Invalid parameter: MobileNumber'):
			taken, user = is_mobile_taken(str(persona.telefono))
			if taken:
				raise BluetoothError(400, f'El teléfono indicado para {persona.apellido}, {persona.nombre} está siendo usado por {user}')
			else:
				raise BluetoothError(400, 'El número de teléfono indicado para {persona.apellido}, {persona.nombre} es inválido')

	put_data = {
  		'newPassword': persona.password
	}
	code, response = call_bluetooth_api(
		f'users/{persona.dni}/resetPassword',
		'PUT',
		put_data
	)
	
def create_or_update_user(acceso: Acceso, persona: Personal):
	code, user_data = call_bluetooth_api('users/' + str(persona.dni), 'GET')
	if code == 404: 
		create_user(acceso, persona)
	elif code == 200:
		update_user(persona, user_data)
	else:
		raise BluetoothError()

def create_and_link_work_order(acceso: Acceso, personal: list[Personal], sitio: str) -> str:
	wo_data = {
		'name': f'{acceso.empresa.title()} TKT {acceso.ticket.pk}',
		'keyValidity': 'OneHour',
		'startDate': acceso.fecha_desde.isoformat(),
		'endDate': acceso.fecha_hasta.isoformat(),
		'weekDays': ['allWeek'],
		'startTimeInDay': acceso.hora_desde.isoformat('minutes'),
		'endTimeInDay': acceso.hora_hasta.isoformat('minutes'),
		'oneTimeUse': False,
		'numberOfUnlocks': 0,
	}
	code, data = call_bluetooth_api('workOrders', 'POST', wo_data)
	if code != 200:
		raise BluetoothError()
	
	code, data = call_bluetooth_api(
		f'workOrders/{data["name"]}/links/sites',
		'PUT',
		{'identifiers': [sitio]}
	)
	if code != 200:
		raise BluetoothError()
	
	code, data = call_bluetooth_api(
		f'workOrders/{data["name"]}/links/users',
		'PUT',
		{'identifiers': [str(persona.dni) for persona in personal]}
	)
	if code != 200:
		raise BluetoothError()

def generar_permiso_en_bluetooth(acceso: Acceso, personal_autorizado: QuerySet[Personal]) -> tuple[int, str]:
	try:
		sitio = acceso.ticket.sitio
		lock_count = get_sitio_lock_count(sitio.ta)
		if lock_count == 0:
			raise BluetoothError(400, 'El sitio no tiene candados asociados en la base de datos de Bluetooth.')

		personal = list(personal_autorizado)
		for persona in personal:
			create_or_update_user(acceso, persona)
		
		create_and_link_work_order(acceso, personal, sitio.ta)

		return 200, 'Permiso generado'

	except requests.ConnectionError as error:
		return 500, 'Error de conexión'

	except requests.Timeout as error:
		return 500, 'Sin respuesta del servidor de bluetooth'

	except BluetoothError as error:
		return error.code, error.message

def obtener_candados_por_sitio(sitios: QuerySet):
	result = {}
	for sitio in sitios:
		locks = get_sitio_lock_count(sitio)
		result[sitio.pk] = locks
	return result