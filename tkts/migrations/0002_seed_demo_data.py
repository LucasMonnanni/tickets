from __future__ import annotations

import datetime
from decimal import Decimal

from django.db import migrations
from django.utils import timezone


def seed_tkts_demo_data(apps, schema_editor):
    Motivo = apps.get_model('tkts', 'Motivo')
    Cliente = apps.get_model('tkts', 'Cliente')
    Ticket = apps.get_model('tkts', 'Ticket')
    OC = apps.get_model('tkts', 'OC')
    Acceso = apps.get_model('tkts', 'Acceso')
    CambioDeEquipos = apps.get_model('tkts', 'CambioDeEquipos')
    Personal = apps.get_model('tkts', 'Personal')

    Sitio = apps.get_model('sitios', 'Sitio')

    # IDs hardcoded by order in tkts.constants.estados
    ESTADO_ABIERTO_NO_ACCESO = 0
    ESTADO_EN_FACTURACION = 1
    ESTADO_CERRADO_NO_ACCESO = 2
    ESTADO_RECHAZADO_NO_ACCESO = 3
    ESTADO_ABIERTO_ACCESO = 4
    ESTADO_CERRADO_ACCESO = 5
    ESTADO_RECHAZADO_ACCESO = 6

    motivos = [
        'ACCESO',
        'CAMBIO DE EQUIPOS',
        'AVERÍA',
        'FALTA DE ENERGÍA',
        'INTERFERENCIA',
    ]
    motivo_objs = {}
    for nombre in motivos:
        obj, _ = Motivo.objects.get_or_create(nombre=nombre, defaults={'visible': True})
        motivo_objs[nombre] = obj

    clientes = [
        'Mantenimiento',
        'Operaciones Internas',
        'Cliente PyME Sur',
        'Cliente Residencial Centro',
    ]
    cliente_objs = {}
    for nombre in clientes:
        obj, _ = Cliente.objects.get_or_create(nombre=nombre, defaults={'visible': True})
        cliente_objs[nombre] = obj

    sitios = {
        'SIT-BA-001': Sitio.objects.get(sigla_id='SIT-BA-001'),
        'SIT-BA-002': Sitio.objects.get(sigla_id='SIT-BA-002'),
        'SIT-CBA-003': Sitio.objects.get(sigla_id='SIT-CBA-003'),
    }

    today = datetime.date.today()
    t0 = timezone.now()
    hora1 = datetime.time(8, 0)
    hora2 = datetime.time(17, 30)

    ticket_plans = [
        # 0 Abierto (no acceso)
        {
            'estado': ESTADO_ABIERTO_NO_ACCESO,
            'link': 'https://demo.local/tickets/0001',
            'nombre': 'María González',
            'email': 'maria.gonzalez@demo.com',
            'telefono': 1123456789,
            'cliente': 'Operaciones Internas',
            'sitio': 'SIT-BA-001',
            'motivo': 'CAMBIO DE EQUIPOS',
            'problema': 'El radioenlace presenta caídas intermitentes y requiere reemplazo de equipos.',
            'cambio': True,
        },
        {
            'estado': ESTADO_ABIERTO_NO_ACCESO,
            'link': 'https://demo.local/tickets/0002',
            'nombre': 'Carlos Pérez',
            'email': 'carlos.perez@demo.com',
            'telefono': 1125567890,
            'cliente': 'Operaciones Internas',
            'sitio': 'SIT-BA-002',
            'motivo': 'CAMBIO DE EQUIPOS',
            'problema': 'Se detectó degradación de señal; se solicita cambio de antenas y verificación de enlaces.',
            'cambio': True,
        },
        {
            'estado': ESTADO_ABIERTO_NO_ACCESO,
            'link': 'https://demo.local/tickets/0003',
            'nombre': 'Sofía Martínez',
            'email': 'sofia.martinez@demo.com',
            'telefono': 3512234567,
            'cliente': 'Cliente PyME Sur',
            'sitio': 'SIT-CBA-003',
            'motivo': 'FALTA DE ENERGÍA',
            'problema': 'Cortes de energía en horarios pico; se requiere diagnóstico del suministro y del sistema de respaldo.',
            'cambio': False,
        },

        # 1 En facturación
        {
            'estado': ESTADO_EN_FACTURACION,
            'link': 'https://demo.local/tickets/0101',
            'nombre': 'Laura Pereyra',
            'email': 'laura.pereyra@demo.com',
            'telefono': 1145566778,
            'cliente': 'Cliente Residencial Centro',
            'sitio': 'SIT-BA-001',
            'motivo': 'AVERÍA',
            'problema': 'Avería en módulo de potencia: el equipo entra en protección.',
            'cierre': today - datetime.timedelta(days=7),
            'solucion': 'Se reemplazó el módulo de potencia y se verificó estabilidad del suministro.',
            'oc': {'numero': 'OC-000101', 'costo': Decimal('125000.00'), 'contratista': 'Taller Eléctrico Norte'},
        },
        {
            'estado': ESTADO_EN_FACTURACION,
            'link': 'https://demo.local/tickets/0102',
            'nombre': 'Martín Salas',
            'email': 'martin.salas@demo.com',
            'telefono': 1140022001,
            'cliente': 'Operaciones Internas',
            'sitio': 'SIT-BA-002',
            'motivo': 'FALTA DE ENERGÍA',
            'problema': 'Fallas repetitivas en el sistema de alimentación durante la noche.',
            'cierre': today - datetime.timedelta(days=9),
            'solucion': 'Se ajustaron parámetros del controlador y se revisaron conexiones del tablero.',
            'oc': {'numero': 'OC-000102', 'costo': Decimal('86000.00'), 'contratista': 'Electromecánica Quilmes'},
        },
        {
            'estado': ESTADO_EN_FACTURACION,
            'link': 'https://demo.local/tickets/0103',
            'nombre': 'Sofía Molina',
            'email': 'sofia.molina@demo.com',
            'telefono': 3515551122,
            'cliente': 'Cliente PyME Sur',
            'sitio': 'SIT-CBA-003',
            'motivo': 'INTERFERENCIA',
            'problema': 'Interferencia en el enlace: aumento de errores de transmisión.',
            'cierre': today - datetime.timedelta(days=8),
            'solucion': 'Se reorientaron antenas y se optimizaron canales de operación.',
            'oc': {'numero': 'OC-000103', 'costo': Decimal('104500.00'), 'contratista': 'Ingeniería Radio Sur'},
        },

        # 2 Cerrado (no acceso)
        {
            'estado': ESTADO_CERRADO_NO_ACCESO,
            'link': 'https://demo.local/tickets/0201',
            'nombre': 'Federico Ríos',
            'email': 'federico.rios@demo.com',
            'telefono': 1122334455,
            'cliente': 'Operaciones Internas',
            'sitio': 'SIT-BA-002',
            'motivo': 'AVERÍA',
            'problema': 'Falla en el sistema de comunicación: no responde el gateway.',
            'cierre': today - datetime.timedelta(days=3),
            'solucion': 'Se restableció configuración del gateway y se actualizó firmware.',
        },
        {
            'estado': ESTADO_CERRADO_NO_ACCESO,
            'link': 'https://demo.local/tickets/0202',
            'nombre': 'Ana Cabrera',
            'email': 'ana.cabrera@demo.com',
            'telefono': 3513334455,
            'cliente': 'Cliente PyME Sur',
            'sitio': 'SIT-CBA-003',
            'motivo': 'FALTA DE ENERGÍA',
            'problema': 'Variaciones de voltaje; se observa reinicio automático del equipo.',
            'cierre': today - datetime.timedelta(days=5),
            'solucion': 'Se ajustó protecciones y se verificó voltaje dentro de rango operativo.',
        },
        {
            'estado': ESTADO_CERRADO_NO_ACCESO,
            'link': 'https://demo.local/tickets/0203',
            'nombre': 'Diego Sosa',
            'email': 'diego.sosa@demo.com',
            'telefono': 1124445566,
            'cliente': 'Cliente Residencial Centro',
            'sitio': 'SIT-BA-001',
            'motivo': 'INTERFERENCIA',
            'problema': 'Se detectaron interferencias por equipos cercanos.',
            'cierre': today - datetime.timedelta(days=4),
            'solucion': 'Se cambiaron parámetros y se redujo potencia de transmisión conforme al plan.',
        },

        # 3 Rechazado (no acceso)
        {
            'estado': ESTADO_RECHAZADO_NO_ACCESO,
            'link': 'https://demo.local/tickets/0301',
            'nombre': 'Paula Fernández',
            'email': 'paula.fernandez@demo.com',
            'telefono': 1125566778,
            'cliente': 'Operaciones Internas',
            'sitio': 'SIT-BA-001',
            'motivo': 'AVERÍA',
            'problema': 'Solicitan reparación sin evidencia suficiente del fallo reportado.',
            'cierre': today - datetime.timedelta(days=2),
            'observaciones': 'Se rechazó por falta de verificación en campo y datos de medición.',
        },
        {
            'estado': ESTADO_RECHAZADO_NO_ACCESO,
            'link': 'https://demo.local/tickets/0302',
            'nombre': 'Romina Torres',
            'email': 'romina.torres@demo.com',
            'telefono': 1146665588,
            'cliente': 'Cliente Residencial Centro',
            'sitio': 'SIT-BA-002',
            'motivo': 'FALTA DE ENERGÍA',
            'problema': 'Se reportan cortes pero no se logró confirmar la causa durante la visita.',
            'cierre': today - datetime.timedelta(days=6),
            'observaciones': 'Se rechazó por imposibilidad de diagnóstico definitivo.',
        },
        {
            'estado': ESTADO_RECHAZADO_NO_ACCESO,
            'link': 'https://demo.local/tickets/0303',
            'nombre': 'Miguel Herrera',
            'email': 'miguel.herrera@demo.com',
            'telefono': 3516664455,
            'cliente': 'Cliente PyME Sur',
            'sitio': 'SIT-CBA-003',
            'motivo': 'INTERFERENCIA',
            'problema': 'Se informa interferencia sin parámetros ni espectro adjunto.',
            'cierre': today - datetime.timedelta(days=1),
            'observaciones': 'Rechazado por documentación incompleta para análisis.',
        },

        # 4 Abierto (acceso)
        {
            'estado': ESTADO_ABIERTO_ACCESO,
            'link': 'https://demo.local/tickets/0401',
            'nombre': 'Carolina Vázquez',
            'email': 'carolina.vazquez@demo.com',
            'telefono': 1127778889,
            'cliente': 'Mantenimiento',
            'sitio': 'SIT-BA-002',
            'motivo': 'ACCESO',
            'problema': 'Requiere ingreso a sitio para tareas de mantenimiento preventivo.',
            'programada': today + datetime.timedelta(days=2),
            'acceso': {'permiso_generado': False, 'empresa': 'Operaciones de Campo'},
        },
        {
            'estado': ESTADO_ABIERTO_ACCESO,
            'link': 'https://demo.local/tickets/0402',
            'nombre': 'Javier Romero',
            'email': 'javier.romero@demo.com',
            'telefono': 3518887766,
            'cliente': 'Mantenimiento',
            'sitio': 'SIT-CBA-003',
            'motivo': 'ACCESO',
            'problema': 'Solicitud de acceso para inspección y mediciones de energía.',
            'programada': today + datetime.timedelta(days=3),
            'acceso': {'permiso_generado': False, 'empresa': 'Equipo Técnico Energía'},
        },
        {
            'estado': ESTADO_ABIERTO_ACCESO,
            'link': 'https://demo.local/tickets/0403',
            'nombre': 'Valeria Núñez',
            'email': 'valeria.nunez@demo.com',
            'telefono': 1129993344,
            'cliente': 'Mantenimiento',
            'sitio': 'SIT-BA-001',
            'motivo': 'ACCESO',
            'problema': 'Necesidad de acceso por trabajo en altura y verificación de condiciones.',
            'programada': today + datetime.timedelta(days=1),
            'acceso': {'permiso_generado': False, 'empresa': 'Mantenimiento Telecom'},
        },

        # 5 Cerrado (acceso)
        {
            'estado': ESTADO_CERRADO_ACCESO,
            'link': 'https://demo.local/tickets/0501',
            'nombre': 'Lucía Gómez',
            'email': 'lucia.gomez@demo.com',
            'telefono': 1121011121,
            'cliente': 'Mantenimiento',
            'sitio': 'SIT-BA-001',
            'motivo': 'ACCESO',
            'problema': 'Acceso cerrado con verificación completa de condiciones de trabajo.',
            'programada': today - datetime.timedelta(days=1),
            'cierre': today - datetime.timedelta(days=1),
            'solucion': 'Se realizó la inspección y se liberó el sitio conforme a procedimiento.',
            'acceso': {'permiso_generado': True, 'empresa': 'Mantenimiento Telecom'},
        },
        {
            'estado': ESTADO_CERRADO_ACCESO,
            'link': 'https://demo.local/tickets/0502',
            'nombre': 'Héctor Vidal',
            'email': 'hector.vidal@demo.com',
            'telefono': 1141213141,
            'cliente': 'Mantenimiento',
            'sitio': 'SIT-BA-002',
            'motivo': 'ACCESO',
            'problema': 'Tarea completada y permiso generado para ingreso de cuadrilla.',
            'programada': today - datetime.timedelta(days=2),
            'cierre': today - datetime.timedelta(days=2),
            'solucion': 'Permiso generado; tareas ejecutadas y registro fotográfico adjunto.',
            'acceso': {'permiso_generado': True, 'empresa': 'Operaciones de Campo'},
        },
        {
            'estado': ESTADO_CERRADO_ACCESO,
            'link': 'https://demo.local/tickets/0503',
            'nombre': 'Nicolás Medina',
            'email': 'nicolas.medina@demo.com',
            'telefono': 3511516171,
            'cliente': 'Mantenimiento',
            'sitio': 'SIT-CBA-003',
            'motivo': 'ACCESO',
            'problema': 'Acceso para trabajo correctivo menor; cierre operativo realizado.',
            'programada': today - datetime.timedelta(days=3),
            'cierre': today - datetime.timedelta(days=3),
            'solucion': 'Se ejecutó ajuste menor y se confirmó estabilidad del sitio.',
            'acceso': {'permiso_generado': True, 'empresa': 'Equipo Técnico Energía'},
        },

        # 6 Rechazado (acceso)
        {
            'estado': ESTADO_RECHAZADO_ACCESO,
            'link': 'https://demo.local/tickets/0601',
            'nombre': 'Mónica Salazar',
            'email': 'monica.salazar@demo.com',
            'telefono': 1121718191,
            'cliente': 'Mantenimiento',
            'sitio': 'SIT-BA-002',
            'motivo': 'ACCESO',
            'problema': 'Solicitud de acceso rechazada por falta de coordinación previa.',
            'programada': today + datetime.timedelta(days=4),
            'cierre': today - datetime.timedelta(days=1),
            'observaciones': 'Se rechazó debido a no contar con permiso de trabajo y ventana de ingreso confirmada.',
            'acceso': {'permiso_generado': False, 'empresa': 'Operaciones de Campo'},
        },
        {
            'estado': ESTADO_RECHAZADO_ACCESO,
            'link': 'https://demo.local/tickets/0602',
            'nombre': 'Tomás Rojas',
            'email': 'tomas.rojas@demo.com',
            'telefono': 3512122232,
            'cliente': 'Mantenimiento',
            'sitio': 'SIT-CBA-003',
            'motivo': 'ACCESO',
            'problema': 'Rechazo por documentación incompleta del equipo y alcance.',
            'programada': today + datetime.timedelta(days=2),
            'cierre': today - datetime.timedelta(days=2),
            'observaciones': 'Faltan datos de alcance y responsables del trabajo.',
            'acceso': {'permiso_generado': False, 'empresa': 'Equipo Técnico Energía'},
        },
        {
            'estado': ESTADO_RECHAZADO_ACCESO,
            'link': 'https://demo.local/tickets/0603',
            'nombre': 'Verónica Paredes',
            'email': 'veronica.paredes@demo.com',
            'telefono': 1122526272,
            'cliente': 'Mantenimiento',
            'sitio': 'SIT-BA-001',
            'motivo': 'ACCESO',
            'problema': 'Ingreso rechazado por evaluación de riesgo no favorable.',
            'programada': today + datetime.timedelta(days=5),
            'cierre': today - datetime.timedelta(days=3),
            'observaciones': 'Se rechazó por condiciones de seguridad no cumplidas al momento de la gestión.',
            'acceso': {'permiso_generado': False, 'empresa': 'Mantenimiento Telecom'},
        },
    ]

    for plan in ticket_plans:
        if Ticket.objects.filter(link=plan['link']).exists():
            continue

        sitio = sitios[plan['sitio']]
        cliente = cliente_objs[plan['cliente']]
        motivo = motivo_objs[plan['motivo']]

        oc_obj = None
        if 'oc' in plan:
            oc_cfg = plan['oc']
            if len(oc_cfg['contratista']) > 32:
                print(plan['link'])
            oc_obj = OC.objects.create(
                numero=oc_cfg['numero'],
                costo=oc_cfg['costo'],
                contratista=oc_cfg['contratista'],
            )

        acceso_obj = None
        if 'acceso' in plan:
            acceso_cfg = plan['acceso']
            acceso_obj = Acceso.objects.create(
                fecha_desde=today,
                fecha_hasta=today + datetime.timedelta(days=1),
                hora_desde=hora1,
                hora_hasta=hora2,
                empresa=acceso_cfg['empresa'],
                afectacion=True,
                riesgo_electrico=False,
                altura=('altura' in plan and plan['altura']) if isinstance(plan.get('altura'), bool) else True,
                permiso_generado=acceso_cfg['permiso_generado'],
            )

            # Personal asignado al acceso (lo que suele mostrar/aprobar la UI)
            personal_seed = [
                {'nombre': 'Martín', 'apellido': 'Gómez', 'dni': 32100111, 'telefono': 1122334456, 'aprobado': True},
                {'nombre': 'Silvia', 'apellido': 'Benítez', 'dni': 29400222, 'telefono': 1145566778, 'aprobado': acceso_cfg['permiso_generado']},
            ]
            for p in personal_seed:
                if not Personal.objects.filter(acceso=acceso_obj, dni=p['dni']).exists():
                    Personal.objects.create(
                        acceso=acceso_obj,
                        nombre=p['nombre'],
                        apellido=p['apellido'],
                        dni=p['dni'],
                        telefono=p['telefono'],
                        aprobado=p['aprobado'],
                    )

        cambio_obj = None
        if plan.get('cambio'):
            cambio_obj = CambioDeEquipos.objects.create(
                antenas_actual='Antena panel 2x2, versión A',
                antenas='Antena panel 2x2, versión B (mejor ganancia)',
                enlaces_actual='Radioenlace 15GHz, canal saturado',
                enlaces='Radioenlace 15GHz, reconfigurado con canal optimizado',
                rru_actual='RRU 2-Chain, firmware antiguo',
                rru='RRU 2-Chain, firmware actualizado',
                piso='Cota 0',
                energia=Decimal('3.50'),
            )

        programada = plan.get('programada')
        cierre = plan.get('cierre')

        Ticket.objects.create(
            _estado_id=plan['estado'],
            inicio=t0,
            nombre=plan['nombre'],
            email=plan['email'],
            telefono=plan['telefono'],
            cliente=cliente,
            sitio=sitio,
            motivo=motivo,
            prioridad=2,
            problema=plan['problema'],
            link=plan['link'],
            solucion=plan.get('solucion'),
            programada=programada,
            cierre=cierre,
            observaciones=plan.get('observaciones'),
            oc=oc_obj,
            acceso=acceso_obj,
            cambio_de_equipos=cambio_obj,
        )


class Migration(migrations.Migration):
    dependencies = [
        ('sitios', '0001_initial'),
        ('tkts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_tkts_demo_data, migrations.RunPython.noop),
    ]
