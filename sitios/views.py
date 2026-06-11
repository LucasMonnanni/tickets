import folium
import base64
import urllib.parse
from datetime import date, datetime, UTC
from folium.plugins import MarkerCluster
from django.http import HttpResponse
from django.views.generic import View, DetailView, FormView, TemplateView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Min, Max, Q
from django.core.cache import cache
from django.template.loader import render_to_string
from sitios.models import Sitio, Celda
from sitios.forms import SearchForm
from django.contrib.auth import authenticate, login
from django.http.response import JsonResponse
from tickets.services import obtener_candados_por_sitio


def get_bluetooth_count_per_sitio(sitios: list):
	"""Calculate count of candados with BLUETOOTH choice using ORM annotate.
	Returns dict of {sitio_pk: count} where count is 0, 1, or 2
	"""
	result = {}
	return result

def fetch_and_cache_all_lock_counts(sitios = None, cache_timeout: int = 3600):
	"""Fetch lock counts from API and cache them.
	Calls obtener_candados_por_sitio which fetches from external API.
	Returns tuple of (dict of {sitio_pk: lock_count}, bool success)
	"""
	if sitios is None:
		sitios = Sitio.objects.all()
	try:
		result = obtener_candados_por_sitio(sitios)
		# Cache the result
		cache.set('sitios_api_locks', result, cache_timeout)
		cache.set('sitios_api_locks_updated', datetime.now(UTC).isoformat(), cache_timeout)
		return result, True
	except Exception as e:
		print(f"Error fetching lock counts: {e}")
		return {}, False

class SitioDetail(LoginRequiredMixin, DetailView):
    model = Sitio
    template_name_suffix = '_detail'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['operadores'] = self.object.celdas.all().select_related('owner', 'operador')
        context['suministros'] = self.object.suministros.all().select_related('titular')
        context['locadores'] = self.object.locadores.all()
        context['mps'] = self.object.mp_set.all().order_by('-fecha_de_plan')
        context['tickets'] = self.object.ticket_set.all().select_related('cliente', 'motivo').order_by('_estado_id', '-inicio')
        return context

class SitioListView(LoginRequiredMixin, ListView):
    model = Sitio
    paginate_by = 100
    paginate_orphans = 10
    def get_queryset(self):
        sitios = Sitio.objects.all()
        get_attrs = self.request.GET

        get_attrs._mutable = True
        order = get_attrs.pop('order', ['sigla_id'])[0]
        sitios = sitios.order_by(order)
        filters = {}
        excludes = {}
        for key in get_attrs:
            if key == 'page':
                continue
            value = get_attrs.getlist(key, True)
            value = [urllib.parse.unquote_plus(v) for v in value]
            if len(value) == 1:
                value = value[0]
            else:
                key += '__in'
            if key.startswith('not__'):
                excludes[key[5:]] = value
            else:
                filters[key] = value
        sitios = sitios.filter(**filters).exclude(**excludes)
        unique_values = {}
        for field_name in ['estado', 'nombre', 'direccion', 'localidad', 'municipio', 'provincia', 'proyecto', 'tipo', 'estructura', 'acceso', 'candado_calle', 'candado_sitio']:
            field = getattr(Sitio, field_name).field
            unique_values[field.name] = {
                'nombre': field.verbose_name,
                'tipo': 'string',
                'valores': list(set(sitios.values_list(field.name, flat=True).distinct()))
            }
        unique_values['conflicto'] = {
            'nombre': 'Conflictivo',
            'tipo': 'bool',
            'valores': ['True', 'False']
        }
        for field_name, field_title, field_type in [
            ('altura', 'Altura', 'numero'),
            ('celdas__id_operador', 'Celda > ID Operador', 'string'),
            ('celdas__operador__nombre', 'Celda > Operador', 'ref'),
            ('suministros__titular__nombre', 'Suminstro > Titular', 'ref'),
            ('suministros__distribuidora', 'Suminstro > Distribuidora', 'string')
        ]:
            unique_values[field_name] = {
                'nombre': field_title,
                'tipo': field_type,
                'valores': list(set(sitios.filter(**{field_name+'__isnull': False}).values_list(field_name, flat=True).distinct()))
            }
        self.extra_context = {'fields': unique_values, 'is_map': False}
        return sitios

class SitioMapView(LoginRequiredMixin, TemplateView):
    template_name = 'sitios/sitio_map.html'
    colors = {
        'Activo': 'darkgreen',
        'Planificado': 'cadetblue',
        'Cancelado': 'gray',
        'Desmontado': 'darkred',
        'Conflictivo': 'red',
    }
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aggregates = Sitio.objects.aggregate(avg_lat = Avg('latitud'), avg_long = Avg('longitud'),\
                min_lat = Min('latitud'), min_long = Min('longitud'),\
                max_lat = Max('latitud'), max_long = Max('longitud'))
        figure = folium.Figure()
        

        # Make the map
        map = folium.Map(
            location = [aggregates['avg_lat'], aggregates['avg_long']],
            zoom_start = 5,
            min_lat=aggregates['min_lat'],
            max_lat=aggregates['max_lat'],
            min_lon=aggregates['min_long'],
            max_lon=aggregates['max_long'],
            tiles = 'Cartodb Positron')
        
        cluster = MarkerCluster(control=False, options={'maxClusterRadius': 50})
        map.add_child(cluster)

        sitios = SitioListView.get_queryset(self).values_list('id', 'estado', 'latitud', 'longitud', 'nombre', 'proyecto', 'estructura', 'altura', 'id', 'conflicto')
        for sitio in sitios:
            estado = 'Conflictivo' if sitio[9] else sitio[1]
            folium.Marker(
                location=sitio[2:4],
                icon=folium.Icon(color = self.colors[estado], prefix='fa',icon='tower-cell'),
                popup=f'<a href="/sitios/{sitio[8]}">{sitio[0]}</a>',
                tooltip=f'{sitio[4]} - {sitio[1]} - {sitio[5]} - {sitio[6]} - {sitio[7]}m'
            ).add_to(cluster)

        estados = self.extra_context['fields']['estado']['valores']
        estados.append('Conflictivo')
        # Define the legend's HTML
        legend_html = '''
        <div class="px-3 py-2 bg-light bg-opacity-75" style="position: fixed; 
            bottom: 50px; left: 50px; width: 200px; height: {}px; 
            border-radius:15px; z-index:9999; font-size:14px;">
            <table class='table table-hover table-borderless table-sm'>
                <thead>
                    <th class="bg-transparent text-black"><b>Leyenda</b></th>
                </thead>
                <tbody>
        '''.format(50+29*len(estados))

        for estado in estados:
            legend_html += '''
            <tr>
                <td class="bg-transparent text-black">{}</td>
                <td class="bg-transparent"><i class="fa fa-circle" style="color:{}; text-align:end;"></i></td>
            </tr>
            '''.format(estado, self.colors[estado])
        legend_html += '''
                </tbody>
            </table>  
        </div>
        ''' 

        # Add the legend to the map
        figure.get_root().html.add_child(folium.Element(legend_html))

        map.add_to(figure)
        figure.render()
        context['map'] = figure
        del figure.header._children['bootstrap'] 
        del figure.header._children['bootstrap_css']
        del figure.header._children['glyphicons_css']
        context.update(self.extra_context)
        context['is_map'] = True
        return context     

class SitioSearchView(FormView):
    form_class = SearchForm
    template_name = 'sitios/search.html'

    def form_valid(self, form):
        algo = False
        celdas = Celda.objects.all()
        if form.cleaned_data['id'] != '':
            algo = True
            letras = ''.join(filter(lambda x : x in 'abcdefghijklmnopqrstuvxyz', form.cleaned_data['id']))     
            numeros = ''.join(filter(lambda x : x in '0123456789', form.cleaned_data['id']))
            celdas = celdas.filter(Q(id_operador__iregex=rf".*{letras}.*{numeros}.*")| Q(id_operador__icontains = form.cleaned_data['id']))
        if form.cleaned_data['direccion'] != '':
            algo = True
            celdas = celdas.filter(sitio__direccion__icontains = form.cleaned_data['direccion'] )
        if algo:
            context = self.get_context_data(form=form)
            context['celdas'] = celdas
            return self.render_to_response(context)
        else:
            return self.form_invalid(form)

class SitioAPIView(View):
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
        tkts = list(Sitio.objects.prefetch_related().values())
        response = JsonResponse(tkts, safe = False)
        return response

class CandadosTableView(LoginRequiredMixin, TemplateView):
    """Display candados dashboard with cache indicator"""
    template_name = 'sitios/candados_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sitios = Sitio.objects.filter(estado='Activo').order_by('id')

        # Get bluetooth count (from DB)
        bluetooth_count = get_bluetooth_count_per_sitio(sitios)

        # Get cached API lock counts
        api_locks = cache.get('sitios_api_locks', {})
        updated_at = cache.get('sitios_api_locks_updated', None)

        # Build table data
        table_data = []
        for sitio in sitios:
            api_count = api_locks.get(sitio.pk, None)
            table_data.append({
                'sitio': sitio,
                'bluetooth_count': bluetooth_count.get(sitio.pk, 0),
                'api_locks': api_count,
            })

        context['table_data'] = table_data
        context['updated_at'] = updated_at
        context['is_loading'] = api_locks == {}

        return context

class CandadosRefreshView(LoginRequiredMixin, View):
    """HTMX endpoint to refresh lock counts from API and return HTML table"""

    def get(self, request):
        sitios = Sitio.objects.all().order_by('id')

        # Fetch fresh data from API and cache it
        api_locks, success = fetch_and_cache_all_lock_counts(sitios)

        if not success:
            return HttpResponse(
                '<tr><td colspan="3" class="text-danger">Error fetching lock data</td></tr>',
                status=500
            )

        # Get bluetooth count (from DB)
        bluetooth_count = get_bluetooth_count_per_sitio(sitios)

        # Build table data
        table_data = []
        for sitio in sitios:
            api_count = api_locks.get(sitio.pk, None)
            table_data.append({
                'sitio': sitio,
                'bluetooth_count': bluetooth_count.get(sitio.pk, 0),
                'api_locks': api_count,
            })

        # Render just the table rows
        html = render_to_string(
            'sitios/candados_table_rows.html',
            {'table_data': table_data}
        )

        return HttpResponse(html)
