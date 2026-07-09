from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ServicioViewSet, DisponibilidadViewSet, MisCitasViewSet, VerificarFeriadoView, RegistroView

router = DefaultRouter()
router.register('servicios', ServicioViewSet, basename='servicios')
router.register('disponibilidades', DisponibilidadViewSet, basename='disponibilidades')
router.register('citas', MisCitasViewSet, basename='citas')

urlpatterns = router.urls + [
    path('feriados/', VerificarFeriadoView.as_view(), name='verificar-feriado'),
    path('auth/register/', RegistroView.as_view(), name='registro'),
]