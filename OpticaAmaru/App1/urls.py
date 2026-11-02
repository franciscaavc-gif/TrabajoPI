from django.urls import path

from . import views

urlpatterns = [
    path('', views.cargar_receta, name='cargar_receta'),
    path('receta/<uuid:pk>/detalle/', views.detalle_receta, name='detalle_receta'),
    path('receta/<uuid:pk>/resumen/', views.resumen_receta, name='resumen_receta'),
]
