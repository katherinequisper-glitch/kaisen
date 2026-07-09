from django.urls import path
from .views import ProcesarPagoView, PagarLoteView, PagarPremiumView

urlpatterns = [
    path('procesar/', ProcesarPagoView.as_view(), name='procesar-pago'),
    path('lote/',     PagarLoteView.as_view(),    name='pagar-lote'),
    path('premium/',  PagarPremiumView.as_view(), name='pagar-premium'),
]
