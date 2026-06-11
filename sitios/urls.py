from django.urls import path
from sitios.views import *

urlpatterns = [
    path('sitios/', SitioListView.as_view(), name = 'sitio_lista'),
    path('sitios/mapa/', SitioMapView.as_view(), name = 'sitio_mapa'),
    path('sitios/candados/', CandadosTableView.as_view(), name='candados_dashboard'),
    path('sitios/candados/refresh/', CandadosRefreshView.as_view(), name='candados_refresh'),
    path('sitio/buscar/', SitioSearchView.as_view(), name = 'buscar'),
    path('sitios/<int:pk>/', SitioDetail.as_view(), name = 'sitio_detalle'),
    path('sitios/api/', SitioAPIView.as_view(), name = 'sitio_api'),
]