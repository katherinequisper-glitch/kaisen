import requests
from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Servicio, Cita, Disponibilidad
from .serializers import ServicioSerializer, CitaSerializer, DisponibilidadSerializer, RegistroSerializer


class ServicioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Servicio.objects.filter(activo=True)
    serializer_class = ServicioSerializer
    permission_classes = [permissions.AllowAny]


class DisponibilidadViewSet(viewsets.ReadOnlyModelViewSet):
    """Lista horarios libres, opcionalmente filtrados por ?servicio=<id>"""
    serializer_class = DisponibilidadSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Disponibilidad.objects.filter(ocupado=False)
        servicio_id = self.request.query_params.get('servicio')
        if servicio_id:
            qs = qs.filter(servicio_id=servicio_id)
        return qs


class MisCitasViewSet(viewsets.ModelViewSet):
    serializer_class = CitaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cita.objects.filter(usuario=self.request.user).order_by('-fecha', '-hora')

    def get_serializer_context(self):
        return {'request': self.request}


class VerificarFeriadoView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        fecha = request.query_params.get('fecha')
        if not fecha:
            return Response({'error': 'Debes enviar ?fecha=YYYY-MM-DD'}, status=400)
        anio = fecha.split('-')[0]
        try:
            resp = requests.get(f'https://date.nager.at/api/v3/publicholidays/{anio}/PE', timeout=5)
            feriados = [f['date'] for f in resp.json()]
        except requests.RequestException:
            return Response({'error': 'No se pudo consultar la API de feriados'}, status=503)
        return Response({'fecha': fecha, 'es_feriado': fecha in feriados})


class RegistroView(generics.CreateAPIView):
    queryset = User.objects.all() if False else None
    serializer_class = RegistroSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        from django.contrib.auth.models import User
        return User.objects.all()