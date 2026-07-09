import requests
import os
from decimal import Decimal
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from citas.models import Cita, Perfil
from .models import Pago
from .serializers import PagoSerializer


def _culqi_charge(email, amount_centimos, source_id, description='Kaisen Tutorías'):
    """Realiza un cargo en Culqi. Devuelve (ok: bool, data: dict)."""
    try:
        resp = requests.post(
            'https://api.culqi.com/v2/charges',
            headers={
                'Authorization': f'Bearer {os.getenv("CULQI_SECRET_KEY")}',
                'Content-Type':  'application/json',
            },
            json={
                'amount':        amount_centimos,
                'currency_code': 'PEN',
                'email':         email,
                'source_id':     source_id,
                'description':   description,
            },
            timeout=10,
        )
    except requests.RequestException:
        return False, {'error': 'No se pudo conectar con Culqi'}

    data = resp.json()
    return (resp.status_code == 201), data


class ProcesarPagoView(APIView):
    """Cobra UNA cita (token Culqi individual) y la confirma."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cita_id     = request.data.get('cita_id')
        token_culqi = request.data.get('token_culqi')

        if not cita_id or not token_culqi:
            return Response({'error': 'Faltan cita_id o token_culqi'}, status=400)

        try:
            cita = Cita.objects.select_related('servicio').get(
                id=cita_id, usuario=request.user, estado='pendiente'
            )
        except Cita.DoesNotExist:
            return Response({'error': 'Cita no encontrada o ya pagada'}, status=404)

        if hasattr(cita, 'pago'):
            return Response({'error': 'Esta cita ya fue pagada'}, status=400)

        monto_soles    = cita.servicio.precio
        monto_centimos = int(monto_soles * 100)

        ok, data = _culqi_charge(
            email          = request.user.email,
            amount_centimos = monto_centimos,
            source_id      = token_culqi,
            description    = f'Tutoría: {cita.servicio.nombre}',
        )
        if not ok:
            return Response({'error': 'Pago rechazado', 'detalle': data}, status=400)

        with transaction.atomic():
            pago = Pago.objects.create(
                cita             = cita,
                referencia_culqi = data.get('id'),
                monto            = monto_soles,
                moneda           = 'PEN',
            )
            cita.estado = 'confirmada'
            cita.save()

        return Response(PagoSerializer(pago).data, status=201)


class PagarLoteView(APIView):
    """
    Carrito de pago: recibe una lista de cita_ids + un único token Culqi.
    Hace UN SOLO cargo por el total y confirma todas las citas seleccionadas.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cita_ids    = request.data.get('cita_ids', [])
        token_culqi = request.data.get('token_culqi')

        if not cita_ids or not token_culqi:
            return Response({'error': 'Faltan cita_ids o token_culqi'}, status=400)

        if not isinstance(cita_ids, list) or len(cita_ids) == 0:
            return Response({'error': 'cita_ids debe ser una lista no vacía'}, status=400)

        # Obtener citas pendientes del usuario
        citas = list(
            Cita.objects.select_related('servicio').filter(
                id__in   = cita_ids,
                usuario  = request.user,
                estado   = 'pendiente',
            )
        )

        if len(citas) == 0:
            return Response({'error': 'No se encontraron citas pendientes con esos IDs'}, status=404)

        # Verificar que ninguna tenga pago ya registrado
        ya_pagadas = [c.id for c in citas if hasattr(c, 'pago')]
        if ya_pagadas:
            return Response({'error': f'Las citas {ya_pagadas} ya tienen pago registrado'}, status=400)

        # Calcular total
        total_soles    = sum(c.servicio.precio for c in citas)
        total_centimos = int(total_soles * 100)
        nombres        = ', '.join(c.servicio.nombre for c in citas)

        ok, data = _culqi_charge(
            email           = request.user.email,
            amount_centimos = total_centimos,
            source_id       = token_culqi,
            description     = f'Kaisen — {len(citas)} tutoría(s): {nombres[:80]}',
        )
        if not ok:
            return Response({'error': 'Pago rechazado', 'detalle': data}, status=400)

        referencia = data.get('id')

        with transaction.atomic():
            pagos_creados = []
            for cita in citas:
                pago = Pago.objects.create(
                    cita             = cita,
                    referencia_culqi = referencia,
                    monto            = cita.servicio.precio,
                    moneda           = 'PEN',
                )
                cita.estado = 'confirmada'
                cita.save()
                pagos_creados.append(pago)

        return Response({
            'mensaje':          f'¡Pago exitoso! {len(citas)} tutoría(s) confirmada(s).',
            'referencia_culqi': referencia,
            'total':            str(total_soles),
            'citas_confirmadas': [c.id for c in citas],
        }, status=200)


class PagarPremiumView(APIView):
    """Cobra S/ 49 y activa is_premium=True en el perfil del usuario."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token_culqi = request.data.get('token_culqi')
        if not token_culqi:
            return Response({'error': 'Falta token_culqi'}, status=400)

        perfil, _ = Perfil.objects.get_or_create(usuario=request.user)
        if perfil.is_premium:
            return Response({'mensaje': 'Ya tienes el plan Premium activo.'})

        ok, data = _culqi_charge(
            email           = request.user.email,
            amount_centimos = 4900,
            source_id       = token_culqi,
            description     = 'Kaisen Premium — suscripción mensual',
        )
        if not ok:
            return Response({'error': 'Pago rechazado', 'detalle': data}, status=400)

        perfil.is_premium = True
        perfil.save()

        return Response({
            'mensaje':          '¡Plan Premium activado exitosamente!',
            'is_premium':       True,
            'referencia_culqi': data.get('id'),
        }, status=200)
