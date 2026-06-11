from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context

class Notificacion(models.Model):
    nombre = models.CharField(max_length=32)
    asunto_template = models.TextField()
    texto_template = models.TextField()
    html_template = CKEditor5Field(config_name='notificacion')

    class Meta:
        verbose_name_plural = 'Notificaciones'

    def crear_mail(self, ticket, to, cc=[]):
        asunto, texto, html = self.render(ticket)
        msg = EmailMultiAlternatives(asunto, texto, None, to, cc=cc)
        msg.attach_alternative(html, "text/html")
        return msg

    def render(self, ticket):
        asunto = Template(self.asunto_template).render(Context({'ticket': ticket, 'sitio': ticket.sitio}))
        texto = Template(self.texto_template).render(Context({'ticket': ticket, 'sitio': ticket.sitio}))
        html = Template(self.html_template).render(Context({'ticket': ticket, 'sitio': ticket.sitio}))
        return asunto, texto, html

    def __str__(self):
        return str(self.pk) + ' - ' + self.nombre