from django.db import models


class Sitio(models.Model):
    internal_id = models.BigAutoField(primary_key=True)
    sigla_id = models.CharField(max_length=64, unique=True)
    nombre = models.CharField(max_length=64, verbose_name='Nombre')
    direccion = models.CharField(max_length=120, verbose_name='Dirección')
    localidad = models.CharField(max_length=50, verbose_name='Localidad')
    municipio = models.CharField(max_length=50, verbose_name='Municipio')
    
    class Provincias(models.TextChoices):
        BS_AS = 'Buenos Aires', 'Buenos Aires'
        CABA = 'CABA', 'CABA'
        CATAMARCA = 'Catamarca', 'Catamarca'
        CHACO = 'Chaco', 'Chaco'
        CHUBUT = 'Chubut', 'Chubut'
        CORDOBA = 'Córdoba', 'Córdoba'
        CORRIENTES = 'Corrientes', 'Corrientes'
        ENTRE_RIOS = 'Entre Ríos', 'Entre Ríos'
        FORMOSA = 'Formosa', 'Formosa'
        JUJUY = 'Jujuy', 'Jujuy'
        LA_PAMPA = 'La Pampa', 'La Pampa'
        LA_RIOJA = 'La Rioja', 'La Rioja'
        MENDOZA = 'Mendoza', 'Mendoza'
        MISIONES = 'Misiones', 'Misiones'
        NEUQUEN = 'Neuquen', 'Neuquen'
        RIO_NEGRO = 'Río Negro', 'Río Negro'
        SALTA = 'Salta', 'Salta'
        SAN_JUAN = 'San Juan', 'San Juan'
        SAN_LUIS = 'San Luis', 'San Luis'
        SANTA_CRUZ = 'Santa Cruz', 'Santa Cruz'
        SANTA_FE = 'Santa Fe', 'Santa Fe'
        SANTIAGO = 'Santiago del Estero', 'Santiago del Estero'
        TIERRA_DEL_FUEGO = 'Tierra del Fuego', 'Tierra del Fuego'
        TUCUMAN = 'Tucumán', 'Tucumán'
    provincia = models.CharField(
        max_length=19, verbose_name='Provincia', choices=Provincias.choices)
    latitud = models.DecimalField(
        max_digits=9, decimal_places=6, verbose_name='Latitud')
    longitud = models.DecimalField(
        max_digits=9, decimal_places=6, verbose_name='Longitud')
    proyecto = models.CharField(max_length=64, verbose_name='Proyecto')
    tipo = models.CharField(max_length=64, verbose_name='Tipo')
    estructura = models.CharField(max_length=64, verbose_name='Estructura')
    altura = models.PositiveSmallIntegerField(verbose_name='Altura')

    class Accesos(models.TextChoices):
        INDEPENDIENTE = 'INDEPENDIENTE', 'INDEPENDIENTE'
        LOCADOR = 'LOCADOR', 'LOCADOR'
    acceso = models.CharField(
        max_length=14, choices=Accesos.choices, verbose_name='Acceso')
    aviso = models.BooleanField(verbose_name="Requiere aviso al locador", default=False)
    class Candados(models.TextChoices):
        BLUETOOTH = 'BLUETOOTH', 'BLUETOOTH'
        PROPIO = 'PROPIO', 'PROPIO'
        NUMERICO = 'NUMÉRICO', 'NUMÉRICO'
        OTRO = 'OTRO', 'OTRO'
        NA = 'N/A', 'N/A'
    candado_calle = models.CharField(
        max_length=9, choices=Candados.choices, verbose_name='Candado Calle')
    candado_sitio = models.CharField(
        max_length=9, choices=Candados.choices, verbose_name='Candado Sitio')
    combinacion = models.CharField(max_length=11, blank=True, null=True, verbose_name='Combinación')
    conflicto = models.BooleanField(verbose_name="Acceso conflictivo", default=False)
    procedimiento = models.TextField(verbose_name='Procedimiento', blank=True, null=True)

    class Estados(models.TextChoices):
        ACTIVO = 'Activo', 'Activo'
        PLANIFICADO = 'Planificado', 'Planificado'
        CANCELADO = 'Cancelado', 'Cancelado'
        DESMONTADO = 'Desmontado', 'Desmontado'
    estado = models.CharField(
        max_length=14, choices=Estados.choices, verbose_name='Estado')

    def operadores(self):
        return len(self.celdas.all())
    
    def __str__(self):
        return self.sigla_id
    
    def __repr__(self):
        return self.sigla_id

class Celda(models.Model):
    id_operador = models.CharField(max_length=64)
    sitio = models.ForeignKey(
        Sitio, on_delete=models.PROTECT, related_name='celdas')
    operador = models.ForeignKey(
        'Operador', on_delete=models.PROTECT, related_name='celdas')
    owner = models.ForeignKey(
        'Cellowner', on_delete=models.PROTECT, related_name='celdas', null=True, blank=True)
    suministro = models.ForeignKey(
        'Suministro', on_delete=models.PROTECT, related_name='celdas', null=True, blank=True)

    def __str__(self):
        return self.id_operador + ' - ' + self.sitio.sigla_id

class Contacto(models.Model):
    class Meta:
        ordering = ['apellido']

    nombre = models.CharField(max_length=32)
    apellido = models.CharField(max_length=32)
    telefono = models.PositiveBigIntegerField(null=True, blank=True)
    email = models.EmailField(max_length=128, null=True, blank=True)

    def __str__(self):
        return self.apellido + ', ' + self.nombre

class Cellowner(Contacto):
    operador = models.ForeignKey(
        'Operador', on_delete=models.PROTECT, related_name='cellowners')

    def __str__(self):
        return 'Cellowner de ' + str(self.operador) + ': ' + self.apellido + ', ' + self.nombre

class Locador(Contacto):
    relacion = models.CharField(max_length=24, null=True, blank=True)
    sitios = models.ManyToManyField('Sitio', related_name='locadores')

    class Meta:
        verbose_name_plural = 'Locadores'

    def __str__(self):
        return 'Locador ' + self.apellido + ', ' + self.nombre

class Suministro(models.Model):
    sitio = models.ForeignKey(
        Sitio, on_delete=models.PROTECT, related_name='suministros')
    titular = models.ForeignKey(
        'Titular', on_delete=models.PROTECT, related_name='suministros')
    distribuidora = models.CharField(max_length=32, null=True, blank=True)
    cuenta = models.CharField(max_length=18, null=True, blank=True)
    medidor = models.CharField(max_length=18, null=True, blank=True)
    direccion = models.CharField(max_length=64, null=True, blank=True)

    def operadores(self):
        return len(self.celdas.all())

    def __str__(self):
        return self.sitio.sigla_id + ' - Suministro ' + self.titular.nombre.title()

    class Meta:
        ordering = ['titular']

class Operador(models.Model):
    nombre = models.CharField(max_length=32, unique=True)

    class Meta:
        verbose_name_plural = 'Operadores'
        ordering = ('nombre', )

    def __str__(self):
        return self.nombre

class Titular(models.Model):
    nombre = models.CharField(max_length=32, unique=True)

    class Meta:
        verbose_name_plural = 'Titulares'
        ordering = ('nombre', )

    def __str__(self):
        return self.nombre

class MP(models.Model):
    id = models.CharField(max_length=11, primary_key=True)
    sitio = models.ForeignKey(Sitio, on_delete=models.PROTECT)
    fecha_de_plan = models.DateField()
    estado = models.CharField(max_length=32)
    alcance = models.CharField(max_length=64)
    enlace = models.URLField()
    
    def __str__(self):
        return 'MP ' + self.alcance + ' - ' + self.fecha_de_plan.strftime('%d/%m/%Y')