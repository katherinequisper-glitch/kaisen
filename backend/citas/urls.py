from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    ServicioViewSet, DisponibilidadViewSet, MisCitasViewSet,
    TutorViewSet, VerificarFeriadoView, RegistroView, PerfilView,
)

router = DefaultRouter()
router.register('servicios',        ServicioViewSet,       basename='servicios')
router.register('disponibilidades', DisponibilidadViewSet, basename='disponibilidades')
router.register('citas',            MisCitasViewSet,       basename='citas')
router.register('tutores',          TutorViewSet,          basename='tutores')

urlpatterns = router.urls + [
    path('feriado/',       VerificarFeriadoView.as_view(), name='verificar-feriado'),
    path('feriados/',      VerificarFeriadoView.as_view(), name='verificar-feriado-alt'),
    path('auth/register/', RegistroView.as_view(),         name='registro'),
    path('perfil/',        PerfilView.as_view(),            name='perfil'),
]