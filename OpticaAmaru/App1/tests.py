import shutil
import tempfile
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .forms import EspecificacionLenteForm, RecetaForm
from .models import EspecificacionLente, Receta

MEDIA_TMP = tempfile.mkdtemp()
PDF_VALIDO = b'%PDF-1.4\n%contenido de prueba\n'

DATOS_ESPECIFICACION = {
    'esfera_od': '-2.25', 'esfera_oi': '-1.75',
    'cilindro_od': '-0.50', 'eje_od': '90',
    'cilindro_oi': '-0.75', 'eje_oi': '180',
    'tipo_montura': 'completa',
    'color_armazon': 'negro_mate',
    'tratamiento_cristal': 'blue_block',
    'notas': 'Uso prolongado en pantallas',
}


def pdf(nombre='receta.pdf', contenido=PDF_VALIDO):
    return SimpleUploadedFile(nombre, contenido, content_type='application/pdf')


def form_receta(dias_atras=0, **kwargs):
    fecha = timezone.localdate() - timedelta(days=dias_atras)
    archivo = kwargs.pop('archivo', None) or pdf()
    return RecetaForm({'fecha_emision': fecha.isoformat()}, {'archivo': archivo})


@override_settings(MEDIA_ROOT=MEDIA_TMP)
class RecetaFormTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TMP, ignore_errors=True)

    def test_acepta_receta_de_hoy(self):
        self.assertTrue(form_receta(0).is_valid())

    def test_acepta_receta_de_exactamente_365_dias(self):
        self.assertTrue(form_receta(365).is_valid())

    def test_rechaza_receta_de_366_dias(self):
        form = form_receta(366)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_emision', form.errors)

    def test_rechaza_fecha_futura(self):
        form = form_receta(-1)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_emision', form.errors)

    def test_rechaza_archivo_que_no_es_pdf_ni_imagen(self):
        form = form_receta(0, archivo=pdf('receta.pdf', b'esto no es un pdf'))
        self.assertFalse(form.is_valid())
        self.assertIn('archivo', form.errors)

    def test_rechaza_extension_no_permitida(self):
        form = form_receta(0, archivo=pdf('receta.exe'))
        self.assertFalse(form.is_valid())
        self.assertIn('archivo', form.errors)


class EspecificacionLenteFormTests(TestCase):
    def test_datos_validos(self):
        self.assertTrue(EspecificacionLenteForm(DATOS_ESPECIFICACION).is_valid())

    def test_cilindro_y_eje_son_opcionales_si_van_vacios(self):
        datos = {**DATOS_ESPECIFICACION}
        for campo in ('cilindro_od', 'eje_od', 'cilindro_oi', 'eje_oi'):
            datos[campo] = ''
        self.assertTrue(EspecificacionLenteForm(datos).is_valid())

    def test_cilindro_sin_eje_es_invalido(self):
        datos = {**DATOS_ESPECIFICACION, 'eje_od': ''}
        form = EspecificacionLenteForm(datos)
        self.assertFalse(form.is_valid())
        self.assertIn('eje_od', form.errors)

    def test_eje_sin_cilindro_es_invalido(self):
        datos = {**DATOS_ESPECIFICACION, 'cilindro_oi': ''}
        form = EspecificacionLenteForm(datos)
        self.assertFalse(form.is_valid())
        self.assertIn('cilindro_oi', form.errors)

    def test_esfera_debe_ser_multiplo_de_un_cuarto(self):
        form = EspecificacionLenteForm({**DATOS_ESPECIFICACION, 'esfera_od': '-2.30'})
        self.assertFalse(form.is_valid())
        self.assertIn('esfera_od', form.errors)

    def test_eje_maximo_180(self):
        form = EspecificacionLenteForm({**DATOS_ESPECIFICACION, 'eje_od': '181'})
        self.assertFalse(form.is_valid())
        self.assertIn('eje_od', form.errors)


@override_settings(MEDIA_ROOT=MEDIA_TMP)
class FlujoCompletoTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TMP, ignore_errors=True)

    def test_flujo_de_los_dos_pasos(self):
        hoy = timezone.localdate().isoformat()

        # Paso 1: subir la receta
        respuesta = self.client.post(
            reverse('cargar_receta'), {'archivo': pdf(), 'fecha_emision': hoy}
        )
        receta = Receta.objects.get()
        self.assertRedirects(respuesta, reverse('detalle_receta', args=[receta.pk]))

        # Paso 2: especificaciones del lente
        respuesta = self.client.post(
            reverse('detalle_receta', args=[receta.pk]), DATOS_ESPECIFICACION
        )
        self.assertRedirects(respuesta, reverse('resumen_receta', args=[receta.pk]))
        self.assertEqual(EspecificacionLente.objects.filter(receta=receta).count(), 1)

        # Resumen
        self.assertEqual(self.client.get(reverse('resumen_receta', args=[receta.pk])).status_code, 200)

    def test_receta_vencida_no_se_guarda(self):
        vieja = (timezone.localdate() - timedelta(days=400)).isoformat()
        respuesta = self.client.post(
            reverse('cargar_receta'), {'archivo': pdf(), 'fecha_emision': vieja}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Receta.objects.count(), 0)

    def test_resumen_sin_especificacion_redirige_al_paso_2(self):
        receta = Receta.objects.create(archivo=pdf(), fecha_emision=timezone.localdate())
        respuesta = self.client.get(reverse('resumen_receta', args=[receta.pk]))
        self.assertRedirects(respuesta, reverse('detalle_receta', args=[receta.pk]))
