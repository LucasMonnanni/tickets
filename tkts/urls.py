from django.urls import path
from django.contrib.auth import views as auth_views
from tkts.views import *

urlpatterns = [
    path('',  IndexView.as_view(), name = 'index'),
    path('login/', auth_views.LoginView.as_view(template_name='tkts/login.html', redirect_field_name = 'next', redirect_authenticated_user = True), name = 'login'),
    path('logout/', auth_views.LogoutView.as_view(next_page = 'index'), name = 'logout'),
    path('success/', TemplateView.as_view(template_name = 'tkts/success.html'), name = 'success'),
    path('ticket/nuevo/', TicketCreate.as_view(), name = 'ticket_nuevo'),
    path('ticket/motivo/', motivo_subform, name='ticket_motivo_subform'),
    path('ticket/', TicketDetailShort.as_view(), name = 'detalle_publico'),
    path('tickets/<int:pk>/', TicketDetail.as_view(), name = 'detalle'),
    path('tickets/<int:pk>/generar-permisos/', generar_permisos, name='generar_permisos'),
    path('tickets/<int:pk>/historial/', historial, name='historial'),
    path('tickets/', TicketListView.as_view(), name = 'ticket_lista'),
    path('accesos/', AccesoListView.as_view(), name = 'acceso_lista'),
    path('tickets/mapa/', TicketMapView.as_view(), name = 'ticket_mapa'),
    path('api/', APIView.as_view(), name = 'api'),
    path('settheme/', SetThemeView.as_view(), name = 'theme'),
    path('politica/', TemplateView.as_view(template_name = 'tkts/politica.html'), name = 'politica')
]



