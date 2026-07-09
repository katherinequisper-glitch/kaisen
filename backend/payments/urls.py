from django.urls import path
from .views import ProcesarPagoView

urlpatterns = [
    path('procesar/', ProcesarPagoView.as_view(), name='procesar-pago'),
]


