from django.urls import path
from .views import ProcesarPagoView, PagarPremiumView

urlpatterns = [
    path('procesar/', ProcesarPagoView.as_view(), name='procesar-pago'),
    path('premium/',  PagarPremiumView.as_view(), name='pagar-premium'),
]
