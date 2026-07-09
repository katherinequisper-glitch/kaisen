from rest_framework import serializers
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Servicio, Cita, Disponibilidad


class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = '__all__'


class DisponibilidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disponibilidad
        fields = ['id', 'servicio', 'fecha', 'hora', 'ocupado']


class CitaSerializer(serializers.ModelSerializer):
    servicio_nombre = serializers.CharField(source='servicio.nombre', read_only=True)
    disponibilidad_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Cita
        fields = ['id', 'usuario', 'servicio', 'servicio_nombre', 'disponibilidad_id',
                  'fecha', 'hora', 'estado', 'creado_en']
        read_only_fields = ['usuario', 'servicio', 'fecha', 'hora', 'estado', 'creado_en']

    def create(self, validated_data):
        disp_id = validated_data.pop('disponibilidad_id')
        with transaction.atomic():
            try:
                disponibilidad = Disponibilidad.objects.select_for_update().get(id=disp_id, ocupado=False)
            except Disponibilidad.DoesNotExist:
                raise serializers.ValidationError('Ese horario ya no está disponible.')

            cita = Cita.objects.create(
                usuario=self.context['request'].user,
                servicio=disponibilidad.servicio,
                disponibilidad=disponibilidad,
                fecha=disponibilidad.fecha,
                hora=disponibilidad.hora,
                estado='pendiente',
            )
            disponibilidad.ocupado = True
            disponibilidad.save()
        return cita


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )