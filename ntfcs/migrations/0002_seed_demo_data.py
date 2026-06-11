from __future__ import annotations

from django.db import migrations


def seed_ntfcs_demo_data(apps, schema_editor):
    Notificacion = apps.get_model('ntfcs', 'Notificacion')

    notifications = [
        {
            'nombre': 'Actualizado',
            'asunto': 'Actualización del ticket {{ ticket.pk }} en {{ sitio.id }}',
            'texto': (
                'Hola {{ ticket.nombre }},\n\n'
                'Te informamos que el ticket {{ ticket.pk }} del sitio {{ sitio.id }} ha sido actualizado.\n'
                'Estado actual: {{ ticket.estado.nombre_publico }}.\n\n'
                'Problema: {{ ticket.problema }}\n'
                'Solución: {{ ticket.solucion }}\n\n'
                'Saludos,'
            ),
            'html': (
                '<p>Hola <strong>{{ ticket.nombre }}</strong>,</p>'
                '<p>Te informamos que el ticket <strong>{{ ticket.pk }}</strong> del sitio <strong>{{ sitio.id }}</strong> ha sido actualizado.</p>'
                '<p><strong>Estado actual:</strong> {{ ticket.estado.nombre_publico }}</p>'
                '<p><strong>Problema:</strong><br>{{ ticket.problema }}</p>'
                '<p><strong>Solución:</strong><br>{{ ticket.solucion }}</p>'
                '<p>Saludos,</p>'
            ),
        },
        {
            'nombre': 'Cerrado',
            'asunto': 'Ticket {{ ticket.pk }} cerrado - {{ sitio.id }}',
            'texto': (
                'Hola {{ ticket.nombre }},\n\n'
                'El ticket {{ ticket.pk }} correspondiente al sitio {{ sitio.id }} fue cerrado.\n'
                'Fecha de cierre: {{ ticket.cierre }}.\n\n'
                'Solución registrada: {{ ticket.solucion }}\n\n'
                'Si tenés nuevas novedades, creá un nuevo ticket.\n'
                'Saludos,'
            ),
            'html': (
                '<p>Hola <strong>{{ ticket.nombre }}</strong>,</p>'
                '<p>El ticket <strong>{{ ticket.pk }}</strong> correspondiente al sitio <strong>{{ sitio.id }}</strong> fue cerrado.</p>'
                '<p><strong>Fecha de cierre:</strong> {{ ticket.cierre }}</p>'
                '<p><strong>Solución:</strong><br>{{ ticket.solucion }}</p>'
                '<p>Saludos,</p>'
            ),
        },
        {
            'nombre': 'Ok a facturar',
            'asunto': 'Ok para facturación - Ticket {{ ticket.pk }}',
            'texto': (
                'Hola,\n\n'
                'Se confirmó el cumplimiento de la información para facturación del ticket {{ ticket.pk }}.\n'
                'Cliente: {{ ticket.cliente.nombre }}\n'
                'Sitio: {{ sitio.id }}\n\n'
                'Saludos,'
            ),
            'html': (
                '<p>Hola,</p>'
                '<p>Se confirmó el cumplimiento de la información para facturación del ticket <strong>{{ ticket.pk }}</strong>.</p>'
                '<p><strong>Cliente:</strong> {{ ticket.cliente.nombre }}<br>'
                '<strong>Sitio:</strong> {{ sitio.id }}</p>'
                '<p>Saludos,</p>'
            ),
        },
        {
            'nombre': 'Rechazado',
            'asunto': 'Ticket {{ ticket.pk }} rechazado - {{ sitio.id }}',
            'texto': (
                'Hola {{ ticket.nombre }},\n\n'
                'Lamentamos informarte que el ticket {{ ticket.pk }} del sitio {{ sitio.id }} fue rechazado.\n'
                'Motivo: {{ ticket.observaciones }}\n\n'
                'Para avanzar, te recomendamos revisar la información y crear una nueva solicitud.\n'
                'Saludos,'
            ),
            'html': (
                '<p>Hola <strong>{{ ticket.nombre }}</strong>,</p>'
                '<p>El ticket <strong>{{ ticket.pk }}</strong> del sitio <strong>{{ sitio.id }}</strong> fue rechazado.</p>'
                '<p><strong>Motivo:</strong><br>{{ ticket.observaciones }}</p>'
                '<p>Saludos,</p>'
            ),
        },
        {
            'nombre': 'Generado',
            'asunto': 'Ticket generado - {{ sitio.id }}',
            'texto': (
                'Hola {{ ticket.nombre }},\n\n'
                'Se generó el ticket {{ ticket.pk }} para el sitio {{ sitio.id }}.\n'
                'Estado inicial: {{ ticket.estado.nombre_publico }}.\n\n'
                'Problema informado: {{ ticket.problema }}\n\n'
                'Saludos,'
            ),
            'html': (
                '<p>Hola <strong>{{ ticket.nombre }}</strong>,</p>'
                '<p>Se generó el ticket <strong>{{ ticket.pk }}</strong> para el sitio <strong>{{ sitio.id }}</strong>.</p>'
                '<p><strong>Estado inicial:</strong> {{ ticket.estado.nombre_publico }}</p>'
                '<p><strong>Problema:</strong><br>{{ ticket.problema }}</p>'
                '<p>Saludos,</p>'
            ),
        },
        {
            'nombre': 'Acceso para legales',
            'asunto': 'Solicitud de acceso para legales - Ticket {{ ticket.pk }}',
            'texto': (
                'Hola,\n\n'
                'Se requiere validación legal para el ticket {{ ticket.pk }} del sitio {{ sitio.id }}.\n'
                'Cliente: {{ ticket.cliente.nombre }}\n\n'
                'Problema: {{ ticket.problema }}\n\n'
                'Saludos,'
            ),
            'html': (
                '<p>Hola,</p>'
                '<p>Se requiere validación legal para el ticket <strong>{{ ticket.pk }}</strong> del sitio <strong>{{ sitio.id }}</strong>.</p>'
                '<p><strong>Cliente:</strong> {{ ticket.cliente.nombre }}</p>'
                '<p><strong>Problema:</strong><br>{{ ticket.problema }}</p>'
                '<p>Saludos,</p>'
            ),
        },
        {
            'nombre': 'Ingeniería',
            'asunto': 'Derivación a Ingeniería - Ticket {{ ticket.pk }}',
            'texto': (
                'Hola,\n\n'
                'Se derivó a Ingeniería el ticket {{ ticket.pk }} del sitio {{ sitio.id }}.\n'
                'Motivo: {{ ticket.motivo.nombre }}\n\n'
                'Problema: {{ ticket.problema }}\n\n'
                'Saludos,'
            ),
            'html': (
                '<p>Hola,</p>'
                '<p>Se derivó a Ingeniería el ticket <strong>{{ ticket.pk }}</strong> del sitio <strong>{{ sitio.id }}</strong>.</p>'
                '<p><strong>Motivo:</strong> {{ ticket.motivo.nombre }}</p>'
                '<p><strong>Problema:</strong><br>{{ ticket.problema }}</p>'
                '<p>Saludos,</p>'
            ),
        },
        {
            'nombre': 'Genérico',
            'asunto': 'Notificación de ticket - {{ sitio.id }}',
            'texto': (
                'Hola {{ ticket.nombre }},\n\n'
                'Te compartimos una actualización del ticket {{ ticket.pk }} del sitio {{ sitio.id }}.\n'
                'Estado: {{ ticket.estado.nombre_publico }}\n\n'
                'Saludos,'
            ),
            'html': (
                '<p>Hola <strong>{{ ticket.nombre }}</strong>,</p>'
                '<p>Te compartimos una actualización del ticket <strong>{{ ticket.pk }}</strong> del sitio <strong>{{ sitio.id }}</strong>.</p>'
                '<p><strong>Estado:</strong> {{ ticket.estado.nombre_publico }}</p>'
                '<p>Saludos,</p>'
            ),
        },
    ]

    for n in notifications:
        if Notificacion.objects.filter(nombre=n['nombre']).exists():
            continue
        Notificacion.objects.create(
            nombre=n['nombre'],
            asunto_template=n['asunto'],
            texto_template=n['texto'],
            html_template=n['html'],
        )


class Migration(migrations.Migration):
    dependencies = [
        ('ntfcs', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_ntfcs_demo_data, migrations.RunPython.noop),
    ]
