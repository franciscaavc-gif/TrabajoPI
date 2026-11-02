from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EspecificacionLenteForm, RecetaForm
from .models import Receta


def cargar_receta(request):
    if request.method == 'POST':
        form = RecetaForm(request.POST, request.FILES)
        if form.is_valid():
            receta = form.save()
            return redirect('detalle_receta', pk=receta.pk)
    else:
        form = RecetaForm()

    return render(request, 'cargar_receta.html', {
        'form': form,
        'vigencia_dias': settings.RECETA_VIGENCIA_DIAS,
    })


def detalle_receta(request, pk):
    receta = get_object_or_404(Receta, pk=pk)
    # Si ya existe una especificación, se edita en vez de crear otra.
    especificacion = getattr(receta, 'especificacion', None)

    if request.method == 'POST':
        form = EspecificacionLenteForm(request.POST, instance=especificacion)
        if form.is_valid():
            especificacion = form.save(commit=False)
            especificacion.receta = receta
            especificacion.save()
            return redirect('resumen_receta', pk=receta.pk)
    else:
        form = EspecificacionLenteForm(instance=especificacion)

    return render(request, 'detalle_receta.html', {'form': form, 'receta': receta})


def resumen_receta(request, pk):
    receta = get_object_or_404(Receta, pk=pk)
    especificacion = getattr(receta, 'especificacion', None)
    if especificacion is None:
        return redirect('detalle_receta', pk=receta.pk)

    return render(request, 'resumen_receta.html', {
        'receta': receta,
        'especificacion': especificacion,
    })
