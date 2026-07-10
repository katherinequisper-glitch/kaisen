import requests
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework import viewsets, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, F
from .models import Servicio, Cita, Disponibilidad, Perfil, Tutor
from .serializers import (
    ServicioSerializer, CitaSerializer, DisponibilidadSerializer,
    RegistroSerializer, PerfilSerializer, TutorSerializer,
)


class ServicioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset           = Servicio.objects.filter(activo=True).prefetch_related('tutores')
    serializer_class   = ServicioSerializer
    permission_classes = [permissions.AllowAny]


class TutorViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/tutores/          — todos los tutores activos
       GET /api/tutores/?servicio=<id> — tutores de un servicio concreto"""
    serializer_class   = TutorSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Tutor.objects.filter(activo=True)
        servicio_id = self.request.query_params.get('servicio')
        if servicio_id:
            qs = qs.filter(servicios__id=servicio_id)
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['servicio_id'] = self.request.query_params.get('servicio')
        return context


class DisponibilidadViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/disponibilidades/?servicio=<id>[&tutor=<id>] — solo con cupos libres"""
    serializer_class   = DisponibilidadSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Disponibilidad.objects.select_related('tutor').annotate(
            ocupados=Count('citas', filter=Q(citas__estado__in=['pendiente', 'confirmada']))
        ).filter(ocupados__lt=F('cupo_maximo'))

        servicio_id = self.request.query_params.get('servicio')
        tutor_id    = self.request.query_params.get('tutor')
        if servicio_id:
            qs = qs.filter(servicio_id=servicio_id)
        if tutor_id:
            qs = qs.filter(tutor_id=tutor_id)
        return qs


class MisCitasViewSet(viewsets.ModelViewSet):
    serializer_class   = CitaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        ahora = timezone.now()
        # Auto-cancelar citas pendientes expiradas antes de devolverlas
        Cita.objects.filter(
            usuario=self.request.user,
            estado='pendiente',
            expira_en__lt=ahora,
        ).update(estado='cancelada')

        return Cita.objects.filter(
            usuario=self.request.user
        ).exclude(estado='cancelada').order_by('-fecha', '-hora')

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
            resp     = requests.get(
                f'https://date.nager.at/api/v3/publicholidays/{anio}/PE', timeout=5
            )
            feriados = [f['date'] for f in resp.json()]
        except requests.RequestException:
            return Response({'error': 'No se pudo consultar la API de feriados'}, status=503)
        return Response({'fecha': fecha, 'es_feriado': fecha in feriados})


class RegistroView(generics.CreateAPIView):
    serializer_class   = RegistroSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return User.objects.all()


class PerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil, _ = Perfil.objects.get_or_create(usuario=request.user)
        return Response(PerfilSerializer(perfil).data)

    def patch(self, request):
        perfil, _ = Perfil.objects.get_or_create(usuario=request.user)
        serializer = PerfilSerializer(perfil, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

