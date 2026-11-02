from django.core.exceptions import ValidationError


def validar_paso_cuarto(valor):
    if valor is not None and (valor * 4) % 1 != 0:
        raise ValidationError(
            'Debe ser múltiplo de 0.25 (ej: -2.25, -1.75, +0.50).',
            code='paso_invalido',
        )


def validar_firma_archivo(archivo):
    cabecera = archivo.read(12)
    archivo.seek(0)

    es_pdf = cabecera.startswith(b'%PDF-')
    es_jpg = cabecera.startswith(b'\xff\xd8\xff')
    es_png = cabecera.startswith(b'\x89PNG\r\n\x1a\n')
    es_webp = cabecera[:4] == b'RIFF' and cabecera[8:12] == b'WEBP'

    if not (es_pdf or es_jpg or es_png or es_webp):
        raise ValidationError(
            'El archivo no parece ser un PDF ni una imagen válida (JPG, PNG o WEBP).',
            code='archivo_invalido',
        )
