from datetime import timedelta

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import EspecificacionLente, Receta
from .validators import validar_firma_archivo


class RecetaForm(forms.ModelForm):
    class Meta:
        model = Receta
        fields = ['archivo', 'fecha_emision']
        widgets = {
            'archivo': forms.FileInput(attrs={'accept': 'image/*,application/pdf', 'hidden': True}),
            'fecha_emision': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }
        labels = {'fecha_emision': 'Fecha de emisión indicada en la receta:'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hoy = timezone.localdate()
        attrs = self.fields['fecha_emision'].widget.attrs
        attrs['max'] = hoy.isoformat()
        attrs['min'] = (hoy - timedelta(days=settings.RECETA_VIGENCIA_DIAS)).isoformat()

    def clean_fecha_emision(self):
        fecha = self.cleaned_data['fecha_emision']
        hoy = timezone.localdate()
        dias = settings.RECETA_VIGENCIA_DIAS

        if fecha > hoy:
            raise ValidationError('La fecha de emisión no puede ser futura.')
        if fecha < hoy - timedelta(days=dias):
            raise ValidationError(
                f'La receta tiene más de {dias} días de antigüedad. '
                'No se pueden fabricar lentes con una receta vencida.'
            )
        return fecha

    def clean_archivo(self):
        archivo = self.cleaned_data['archivo']
        limite_mb = settings.RECETA_MAX_UPLOAD_MB

        if archivo.size > limite_mb * 1024 * 1024:
            raise ValidationError(f'El archivo pesa demasiado (máximo {limite_mb} MB).')
        validar_firma_archivo(archivo)
        return archivo


def _numero(**attrs):
    return forms.NumberInput(attrs=attrs)


class EspecificacionLenteForm(forms.ModelForm):
    class Meta:
        model = EspecificacionLente
        fields = [
            'esfera_od', 'esfera_oi',
            'cilindro_od', 'cilindro_oi',
            'eje_od', 'eje_oi',
            'tipo_montura', 'color_armazon', 'tratamiento_cristal',
            'notas',
        ]
        widgets = {
            'esfera_od': _numero(step='0.25', placeholder='Ej: -2.25'),
            'esfera_oi': _numero(step='0.25', placeholder='Ej: -1.75'),
            'cilindro_od': _numero(step='0.25', placeholder='Ej: -0.50'),
            'cilindro_oi': _numero(step='0.25', placeholder='Ej: -0.75'),
            'eje_od': _numero(step='1', min='0', max='180', placeholder='Ej: 90'),
            'eje_oi': _numero(step='1', min='0', max='180', placeholder='Ej: 180'),
            'notas': forms.TextInput(
                attrs={'placeholder': 'Ej: Uso prolongado en pantallas, adición +1.50'}
            ),
        }

    def clean(self):
        cleaned = super().clean()
        # Cilindro y eje van siempre juntos: uno solo no tiene sentido óptico.
        for ojo in ('od', 'oi'):
            cilindro = cleaned.get(f'cilindro_{ojo}')
            eje = cleaned.get(f'eje_{ojo}')
            if cilindro is not None and eje is None:
                self.add_error(f'eje_{ojo}', 'Indica el eje si hay cilindro.')
            if eje is not None and cilindro is None:
                self.add_error(f'cilindro_{ojo}', 'Indica el cilindro si ingresas un eje.')
        return cleaned
