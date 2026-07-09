from rest_framework import serializers
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Servicio, Cita, Disponibilidad, Perfil


class PerfilSerializer(serializers.ModelSerializer):
    username   = serializers.CharField(source='usuario.username', read_only=True)
    email      = serializers.EmailField(source='usuario.email',   read_only=True)

    class Meta:
        model  = Perfil
        fields = ['username', 'email', 'is_premium', 'creado_en']
        read_only_fields = ['username', 'email', 'creado_en']


class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Servicio
        fields = '__all__'


class DisponibilidadSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Disponibilidad
        fields = ['id', 'servicio', 'fecha', 'hora', 'ocupado']


class CitaSerializer(serializers.ModelSerializer):
    servicio_nombre = serializers.CharField(source='servicio.nombre',      read_only=True)
    es_presencial   = serializers.BooleanField(source='servicio.presencial', read_only=True)
    disponibilidad_id = serializers.IntegerField(write_only=True)

    class Meta:
        model  = Cita
        fields = [
            'id', 'usuario', 'servicio', 'servicio_nombre', 'es_presencial',
            'disponibilidad_id', 'fecha', 'hora', 'estado', 'creado_en',
        ]
        read_only_fields = ['usuario', 'servicio', 'fecha', 'hora', 'estado', 'creado_en']

    def validate(self, attrs):
        """
        Si el servicio es presencial, el usuario debe tener el plan Premium.
        """
        disp_id = attrs.get('disponibilidad_id')
        try:
            disponibilidad = Disponibilidad.objects.get(id=disp_id)
        except Disponibilidad.DoesNotExist:
            raise serializers.ValidationError('Ese horario no existe.')

        if disponibilidad.servicio.presencial:
            user = self.context['request'].user
            perfil = getattr(user, 'perfil', None)
            if perfil is None or not perfil.is_premium:
                raise serializers.ValidationError(
                    'Este servicio es presencial y requiere el Plan Premium.'
                )
        return attrs

    def create(self, validated_data):
        disp_id = validated_data.pop('disponibilidad_id')
        with transaction.atomic():
            try:
                disponibilidad = Disponibilidad.objects.select_for_update().get(id=disp_id, ocupado=False)
            except Disponibilidad.DoesNotExist:
                raise serializers.ValidationError('Ese horario ya no está disponible.')

            cita = Cita.objects.create(
                usuario       = self.context['request'].user,
                servicio      = disponibilidad.servicio,
                disponibilidad = disponibilidad,
                fecha         = disponibilidad.fecha,
                hora          = disponibilidad.hora,
                estado        = 'pendiente',
            )
            disponibilidad.ocupado = True
            disponibilidad.save()
        return cita


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username = validated_data['username'],
            email    = validated_data.get('email', ''),
            password = validated_data['password'],
        )
        # El signal post_save ya crea el Perfil, pero nos aseguramos
        Perfil.objects.get_or_create(usuario=user)
        return user