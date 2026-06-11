from sitios.models import Sitio
from tkts.constants import estados

class NavContextMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		response = self.get_response(request)
		return response

	def process_template_response(self, request, response):
		tkts_estados = [(i, e) for i, e in enumerate(estados) if not e.acceso]
		accesos_estados = [(i, e) for i, e in enumerate(estados) if e.acceso]
		sitios_estados = Sitio.objects.order_by('estado').values_list('estado', flat=True).distinct()
		sitios_proyectos = Sitio.objects.order_by('proyecto').values_list('proyecto', flat=True).distinct()
		response.context_data['tkts_estados'] = tkts_estados
		response.context_data['accesos_estados'] = accesos_estados
		response.context_data['sitios_estados'] = sitios_estados
		response.context_data['sitios_proyectos'] = sitios_proyectos
		try:
			theme = request.session['theme']
		except:
			theme = 'light'
		response.context_data['theme'] = theme
		return response


from django.contrib.auth import get_user_model, login

class AutoLoginMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		if not request.user.is_authenticated:
			User = get_user_model()
			try:
				# Grab the first user (e.g., your admin) for the demo
				user = User.objects.filter(is_superuser=True).first()
				if user:
					# Manually set the backend and log the user in
					user.backend = 'django.contrib.auth.backends.ModelBackend'
					login(request, user)
			except Exception:
				pass