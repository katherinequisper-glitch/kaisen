import requests
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from citas.models import Cita
from .models import Pago
from .serializers import PagoSerializer


class ProcesarPagoView(APIView):
    """
    Recibe el token generado por el widget de Culqi en el frontend,
    crea el cargo real contra la API de Culqi, y si es exitoso,
    confirma la cita y guarda el comprobante de pago.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cita_id = request.data.get('cita_id')
        token_culqi = request.data.get('token_culqi')

        if not cita_id or not token_culqi:
            return Response({'error': 'Faltan cita_id o token_culqi'}, status=400)

        try:
            cita = Cita.objects.get(id=cita_id, usuario=request.user)
        except Cita.DoesNotExist:
            return Response({'error': 'Cita no encontrada'}, status=404)

        if hasattr(cita, 'pago'):
            return Response({'error': 'Esta cita ya fue pagada'}, status=400)

        monto_soles = cita.servicio.precio
        monto_centimos = int(monto_soles * 100)  # Culqi trabaja en céntimos

        try:
            resp = requests.post(
                'https://api.culqi.com/v2/charges',
                headers={
                    'Authorization': f'Bearer {os.getenv("CULQI_SECRET_KEY")}',
                    'Content-Type': 'application/json',
                },
                json={
                    'amount': monto_centimos,
                    'currency_code': 'PEN',
                    'email': request.user.email,
                    'source_id': token_culqi,
                },
                timeout=10,
            )
        except requests.RequestException:
            return Response({'error': 'No se pudo conectar con Culqi'}, status=503)

        data = resp.json()

        if resp.status_code != 201:
            return Response({'error': 'Pago rechazado', 'detalle': data}, status=400)

        pago = Pago.objects.create(
            cita=cita,
            referencia_culqi=data.get('id'),
            monto=monto_soles,
            moneda='PEN',
        )
        cita.estado = 'confirmada'
        cita.save()

        return Response(PagoSerializer(pago).data, status=201)
