from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db import migrations


def seed_sitios_demo_data(apps, schema_editor):
    Sitio = apps.get_model('sitios', 'Sitio')
    Operador = apps.get_model('sitios', 'Operador')
    Titular = apps.get_model('sitios', 'Titular')
    Celda = apps.get_model('sitios', 'Celda')
    Cellowner = apps.get_model('sitios', 'Cellowner')
    Locador = apps.get_model('sitios', 'Locador')
    Suministro = apps.get_model('sitios', 'Suministro')
    MP = apps.get_model('sitios', 'MP')

    operadores = [
        'Operador Norte Telecom S.A.',
        'Operador Sur Conectado S.A.',
        'Operador Centro Energizado S.A.',
    ]
    operador_objs = {}
    for nombre in operadores:
        obj, _ = Operador.objects.get_or_create(nombre=nombre)
        operador_objs[nombre] = obj

    titulares = [
        'Empresa Distribuidora Central',
        'Cooperativa Eléctrica Río',
        'Fideicomiso Energía Sur',
    ]
    titular_objs = {}
    for nombre in titulares:
        obj, _ = Titular.objects.get_or_create(nombre=nombre)
        titular_objs[nombre] = obj

    sitios_data = [
        {
            'id': 'SIT-BA-001',
            'nombre': 'Sitio Palermo',
            'direccion': 'Av. Santa Fe 1234',
            'localidad': 'CABA',
            'municipio': 'Comuna 14',
            'provincia': 'CABA',
            'latitud': '34.587346',
            'longitud': '-58.433480',
            'proyecto': 'Proyecto Alfa',
            'tipo': 'Torre Urbana',
            'estructura': 'Acero galvanizado',
            'altura': 42,
            'acceso': 'INDEPENDIENTE',
            'candado_calle': 'PROPIO',
            'candado_sitio': 'PROPIO',
            'combinacion': '123-45',
            'conflicto': False,
            'procedimiento': 'Acceso con autorización previa y verificación de candados.',
            'estado': 'Activo',
        },
        {
            'id': 'SIT-BA-002',
            'nombre': 'Sitio Quilmes',
            'direccion': 'Ruta 36 km 18',
            'localidad': 'Quilmes',
            'municipio': 'Quilmes',
            'provincia': 'Buenos Aires',
            'latitud': '-34.718300',
            'longitud': '-58.251200',
            'proyecto': 'Proyecto Beta',
            'tipo': 'Cisterna y antenas',
            'estructura': 'Estructura modular',
            'altura': 18,
            'acceso': 'LOCADOR',
            'candado_calle': 'NUMÉRICO',
            'candado_sitio': 'NUMÉRICO',
            'combinacion': '902-118',
            'conflicto': False,
            'procedimiento': 'Coordinación con locador, registro de ingreso y verificación de seguridad.',
            'estado': 'Planificado',
        },
        {
            'id': 'SIT-CBA-003',
            'nombre': 'Sitio Colonia Lola',
            'direccion': 'Calle Los Sauces 77',
            'localidad': 'Córdoba',
            'municipio': 'Río Segundo',
            'provincia': 'Córdoba',
            'latitud': '-31.413700',
            'longitud': '-64.187900',
            'proyecto': 'Proyecto Gamma',
            'tipo': 'Torre Rural',
            'estructura': 'Hormigón armado',
            'altura': 30,
            'acceso': 'INDEPENDIENTE',
            'candado_calle': 'BLUETOOTH',
            'candado_sitio': 'PROPIO',
            'combinacion': '0001',
            'conflicto': True,
            'procedimiento': 'Considerar acceso conflictivo: verificar permisos y estado de obra.',
            'estado': 'Activo',
        },
    ]

    for data in sitios_data:
        Sitio.objects.get_or_create(
            sigla_id=data['id'],
            defaults={
                'nombre': data['nombre'],
                'direccion': data['direccion'],
                'localidad': data['localidad'],
                'municipio': data['municipio'],
                'provincia': data['provincia'],
                'latitud': Decimal(data['latitud']),
                'longitud': Decimal(data['longitud']),
                'proyecto': data['proyecto'],
                'tipo': data['tipo'],
                'estructura': data['estructura'],
                'altura': data['altura'],
                'acceso': data['acceso'],
                'candado_calle': data['candado_calle'],
                'candado_sitio': data['candado_sitio'],
                'combinacion': data['combinacion'],
                'conflicto': data['conflicto'],
                'procedimiento': data['procedimiento'],
                'estado': data['estado'],
            },
        )

    # Titulares y suministros por sitio
    suministros = [
        {
            'sitio_id': 'SIT-BA-001',
            'titular_nombre': 'Empresa Distribuidora Central',
            'distribuidora': 'EDEA Central',
            'cuenta': '0001234567',
            'medidor': 'MED-001',
            'direccion': 'Av. Siempreviva 10',
        },
        {
            'sitio_id': 'SIT-BA-002',
            'titular_nombre': 'Cooperativa Eléctrica Río',
            'distribuidora': 'Coop Río',
            'cuenta': '0007654321',
            'medidor': 'MED-118',
            'direccion': 'Calle 9 de Julio 200',
        },
        {
            'sitio_id': 'SIT-CBA-003',
            'titular_nombre': 'Fideicomiso Energía Sur',
            'distribuidora': 'ENERGYSUR',
            'cuenta': '0002223334',
            'medidor': 'MED-203',
            'direccion': 'Camino del Parque s/n',
        },
    ]

    suministro_objs = []
    for data in suministros:
        sitio = Sitio.objects.get(sigla_id=data['sitio_id'])
        titular = Titular.objects.get(nombre=data['titular_nombre'])
        obj = (
            Suministro.objects.filter(sitio=sitio, titular=titular).first()
        )
        if not obj:
            obj = Suministro.objects.create(
                sitio=sitio,
                titular=titular,
                distribuidora=data['distribuidora'],
                cuenta=data['cuenta'],
                medidor=data['medidor'],
                direccion=data['direccion'],
            )
        suministro_objs.append(obj)

    # Cellowners (dueños de celdas) y celdas
    cellowners_data = [
        {
            'operador_nombre': 'Operador Norte Telecom S.A.',
            'nombre': 'Laura',
            'apellido': 'Pereyra',
            'telefono': 1144556677,
            'email': 'laura.pereyra@correo.com',
        },
        {
            'operador_nombre': 'Operador Sur Conectado S.A.',
            'nombre': 'Martín',
            'apellido': 'Salas',
            'telefono': 1144002200,
            'email': 'martin.salas@correo.com',
        },
        {
            'operador_nombre': 'Operador Centro Energizado S.A.',
            'nombre': 'Sofía',
            'apellido': 'Molina',
            'telefono': 3515551122,
            'email': 'sofia.molina@correo.com',
        },
    ]
    cellowner_objs = []
    for data in cellowners_data:
        operador = operador_objs[data['operador_nombre']]
        obj, _ = Cellowner.objects.get_or_create(
            apellido=data['apellido'],
            nombre=data['nombre'],
            operador=operador,
            defaults={
                'telefono': data['telefono'],
                'email': data['email'],
            },
        )
        cellowner_objs.append(obj)

    celdas_data = [
        {
            'id_operador': 'CEL-OPN-001',
            'sitio_id': 'SIT-BA-001',
            'operador_nombre': 'Operador Norte Telecom S.A.',
            'owner_idx': 0,
            'suministro_idx': 0,
        },
        {
            'id_operador': 'CEL-OPS-002',
            'sitio_id': 'SIT-BA-002',
            'operador_nombre': 'Operador Sur Conectado S.A.',
            'owner_idx': 1,
            'suministro_idx': 1,
        },
        {
            'id_operador': 'CEL-OPC-003',
            'sitio_id': 'SIT-CBA-003',
            'operador_nombre': 'Operador Centro Energizado S.A.',
            'owner_idx': 2,
            'suministro_idx': 2,
        },
    ]
    for data in celdas_data:
        sitio = Sitio.objects.get(sigla_id=data['sitio_id'])
        operador = operador_objs[data['operador_nombre']]
        owner = cellowner_objs[data['owner_idx']]
        suministro = suministro_objs[data['suministro_idx']]
        exists = Celda.objects.filter(
            id_operador=data['id_operador'], sitio=sitio, operador=operador
        ).exists()
        if not exists:
            Celda.objects.create(
                id_operador=data['id_operador'],
                sitio=sitio,
                operador=operador,
                owner=owner,
                suministro=suministro,
            )

    # Locadores (conexión M2M hacia Sitio)
    locadores_data = [
        {
            'nombre': 'Carlos',
            'apellido': 'Domínguez',
            'relacion': 'Mantenimiento integral',
            'sitios': ['SIT-BA-001', 'SIT-BA-002'],
        },
        {
            'nombre': 'Valentina',
            'apellido': 'Ruiz',
            'relacion': 'Coordinación de accesos',
            'sitios': ['SIT-CBA-003'],
        },
    ]

    for data in locadores_data:
        obj, _ = Locador.objects.get_or_create(
            apellido=data['apellido'],
            nombre=data['nombre'],
            defaults={'relacion': data['relacion']},
        )
        sitios_to_set = [Sitio.objects.get(sigla_id=sid) for sid in data['sitios']]
        obj.sitios.set(sitios_to_set)

    # MP (Mantenimiento Preventivo)
    mp_data = [
        {
            'id': 'MP-0000001',
            'sitio_id': 'SIT-BA-001',
            'fecha_de_plan': date.today(),
            'estado': 'Planificado',
            'alcance': 'Revisión general y verificación de energía',
            'enlace': 'https://example.com/mp/0000001',
        },
        {
            'id': 'MP-0000002',
            'sitio_id': 'SIT-BA-002',
            'fecha_de_plan': date.today(),
            'estado': 'En proceso',
            'alcance': 'Limpieza de contactos y control de accesorios',
            'enlace': 'https://example.com/mp/0000002',
        },
        {
            'id': 'MP-0000003',
            'sitio_id': 'SIT-CBA-003',
            'fecha_de_plan': date.today(),
            'estado': 'Aprobado',
            'alcance': 'Inspección final y liberación de sitio',
            'enlace': 'https://example.com/mp/0000003',
        },
    ]
    for data in mp_data:
        sitio = Sitio.objects.get(sigla_id=data['sitio_id'])
        obj = MP.objects.filter(id=data['id']).first()
        if not obj:
            MP.objects.create(
                id=data['id'],
                sitio=sitio,
                fecha_de_plan=data['fecha_de_plan'],
                estado=data['estado'],
                alcance=data['alcance'],
                enlace=data['enlace'],
            )


class Migration(migrations.Migration):
    dependencies = [
        ('sitios', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_sitios_demo_data, migrations.RunPython.noop),
    ]
