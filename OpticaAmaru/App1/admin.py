from django.contrib import admin

from .models import EspecificacionLente, Receta


class EspecificacionLenteInline(admin.StackedInline):
    model = EspecificacionLente
    extra = 0


@admin.register(Receta)
class RecetaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'fecha_emision', 'es_vigente', 'creada_en')
    list_filter = ('fecha_emision',)
    readonly_fields = ('creada_en',)
    inlines = [EspecificacionLenteInline]

    @admin.display(boolean=True, description='Vigente')
    def es_vigente(self, obj):
        return obj.vigente
