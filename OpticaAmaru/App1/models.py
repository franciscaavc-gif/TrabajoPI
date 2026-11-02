import os
import uuid
from datetime import timedelta

from django.conf import settings
from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from django.utils import timezone

from .validators import validar_paso_cuarto


def ruta_receta(instance, filename):
    extension = os.path.splitext(filename)[1].lower()
    return f'recetas/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{extension}'


VALIDADORES_ESFERA = [MinValueValidator(-20), MaxValueValidator(20), validar_paso_cuarto]
VALIDADORES_CILINDRO = [MinValueValidator(-10), MaxValueValidator(10), validar_paso_cuarto]
VALIDADORES_EJE = [MinValueValidator(0), MaxValueValidator(180)]


class Receta(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    archivo = models.FileField(
        'archivo de la receta',
        upload_to=ruta_receta,
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png', 'webp'])],
    )
    fecha_emision = models.DateField('fecha de emisión')
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creada_en']
        verbose_name = 'receta'
        verbose_name_plural = 'recetas'

    def __str__(self):
        return f'Receta {str(self.id)[:8]} ({self.fecha_emision:%d-%m-%Y})'

    @property
    def fecha_vencimiento(self):
        return self.fecha_emision + timedelta(days=settings.RECETA_VIGENCIA_DIAS)

    @property
    def vigente(self):
        return timezone.localdate() <= self.fecha_vencimiento


class EspecificacionLente(models.Model):

    class TipoMontura(models.TextChoices):
        COMPLETA = 'completa', 'Completa (Seguridad DS 594)'
        AL_AIRE = 'al_aire', 'Al aire / Transparente'
        SEMI_AL_AIRE = 'semi_al_aire', 'Semi-al aire / 3 Piezas'
        DEPORTIVA = 'deportiva', 'Deportiva Ergonómica'

    class ColorArmazon(models.TextChoices):
        NEGRO_MATE = 'negro_mate', 'Negro Mate'
        GRIS_TITANIO = 'gris_titanio', 'Gris Titanio'
        AZUL_INDUSTRIAL = 'azul_industrial', 'Azul Industrial'
        HABANO_CAREY = 'habano_carey', 'Habano / Carey'

    class TratamientoCristal(models.TextChoices):
        ANTIRREFLEJO = 'antirreflejo', 'Antirreflejo Standard'
        BLUE_BLOCK = 'blue_block', 'Filtro Blue Block (UV)'
        FOTOCROMATICO = 'fotocromatico', 'Fotocromático (Transitions)'

    receta = models.OneToOneField(
        Receta, on_delete=models.CASCADE, related_name='especificacion'
    )

    # Ojo derecho (OD) y ojo izquierdo (OI)
    esfera_od = models.DecimalField(
        'Esfera Ojo Derecho (OD)', max_digits=4, decimal_places=2,
        validators=VALIDADORES_ESFERA,
    )
    esfera_oi = models.DecimalField(
        'Esfera Ojo Izquierdo (OI)', max_digits=4, decimal_places=2,
        validators=VALIDADORES_ESFERA,
    )
    cilindro_od = models.DecimalField(
        'Cilindro (OD)', max_digits=4, decimal_places=2, null=True, blank=True,
        validators=VALIDADORES_CILINDRO,
    )
    cilindro_oi = models.DecimalField(
        'Cilindro (OI)', max_digits=4, decimal_places=2, null=True, blank=True,
        validators=VALIDADORES_CILINDRO,
    )
    eje_od = models.PositiveSmallIntegerField(
        'Eje (OD)', null=True, blank=True, validators=VALIDADORES_EJE
    )
    eje_oi = models.PositiveSmallIntegerField(
        'Eje (OI)', null=True, blank=True, validators=VALIDADORES_EJE
    )

    tipo_montura = models.CharField(
        'Tipo de Montura / Lente', max_length=20,
        choices=TipoMontura.choices, default=TipoMontura.COMPLETA,
    )
    color_armazon = models.CharField(
        'Color de Armazón', max_length=20,
        choices=ColorArmazon.choices, default=ColorArmazon.NEGRO_MATE,
    )
    tratamiento_cristal = models.CharField(
        'Tratamiento de Cristal', max_length=20,
        choices=TratamientoCristal.choices, default=TratamientoCristal.ANTIRREFLEJO,
    )
    notas = models.CharField(
        'Notas Adicionales / Referencia del Oftalmólogo', max_length=255, blank=True
    )

    class Meta:
        verbose_name = 'especificación de lente'
        verbose_name_plural = 'especificaciones de lente'

    def __str__(self):
        return f'Especificación de {self.receta}'
