from rest_framework import serializers
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Servicio, Cita, Disponibilidad, Perfil, Tutor, ServicioTutor


class PerfilSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='usuario.username', read_only=True)
    email    = serializers.EmailField(source='usuario.email',   read_only=True)

    class Meta:
        model  = Perfil
        fields = ['username', 'email', 'is_premium', 'creado_en']
        read_only_fields = ['username', 'email', 'creado_en']


class TutorSerializer(serializers.ModelSerializer):
    foto_src      = serializers.ReadOnlyField()
    es_presencial = serializers.SerializerMethodField()

    class Meta:
        model  = Tutor
        fields = ['id', 'nombre', 'foto_src', 'descripcion', 'estudios', 'requisitos', 'es_presencial']

    def get_es_presencial(self, obj):
        servicio_id = self.context.get('servicio_id')
        if not servicio_id:
            return None
        st = ServicioTutor.objects.filter(servicio_id=servicio_id, tutor=obj).first()
        return st.presencial if st else False


class ServicioSerializer(serializers.ModelSerializer):
    tutores = TutorSerializer(many=True, read_only=True)

    class Meta:
        model  = Servicio
        fields  = ['id', 'nombre', 'descripcion', 'duracion_minutos', 'precio', 'activo', 'tutores']


class DisponibilidadSerializer(serializers.ModelSerializer):
    tutor_nombre       = serializers.CharField(source='tutor.nombre', read_only=True, default=None)
    tutor_id           = serializers.IntegerField(source='tutor.id',  read_only=True, default=None)
    es_presencial      = serializers.SerializerMethodField()
    cupos_disponibles  = serializers.ReadOnlyField()

    class Meta:
        model  = Disponibilidad
        fields = ['id', 'servicio', 'tutor_id', 'tutor_nombre', 'es_presencial',
                  'cupo_maximo', 'cupos_disponibles', 'fecha', 'hora']

    def get_es_presencial(self, obj):
        return obj.es_presencial


class CitaSerializer(serializers.ModelSerializer):
    servicio_nombre   = serializers.CharField(source='servicio.nombre', read_only=True)
    servicio_precio   = serializers.DecimalField(source='servicio.precio', max_digits=8, decimal_places=2, read_only=True)
    es_presencial     = serializers.SerializerMethodField()
    tutor_nombre      = serializers.CharField(source='tutor.nombre', read_only=True, default=None)
    tutor_whatsapp    = serializers.SerializerMethodField()
    disponibilidad_id = serializers.IntegerField(write_only=True)

    class Meta:
        model  = Cita
        fields = [
            'id', 'usuario', 'servicio', 'servicio_nombre', 'servicio_precio',
            'es_presencial', 'tutor_nombre', 'tutor_whatsapp', 'disponibilidad_id',
            'fecha', 'hora', 'estado', 'creado_en', 'expira_en',
            'meet_link', 'meet_password', 'direccion_alumno',
        ]
        read_only_fields = [
            'usuario', 'servicio', 'fecha', 'hora', 'estado', 'creado_en', 'expira_en',
            'meet_link', 'meet_password',
        ]

    def get_es_presencial(self, obj):
        st = ServicioTutor.objects.filter(servicio=obj.servicio, tutor=obj.tutor).first()
        return st.presencial if st else False

    def get_tutor_whatsapp(self, obj):
        # Solo se revela el WhatsApp si la cita ya está confirmada (pagada) y es presencial
        if obj.estado == 'confirmada' and self.get_es_presencial(obj) and obj.tutor:
            return obj.tutor.whatsapp
        return None

    def validate(self, attrs):
        disp_id = attrs.get('disponibilidad_id')

        # Solo valida el horario cuando SÍ se está creando/cambiando uno (POST).
        # En un PATCH parcial (ej. solo enviar direccion_alumno), este bloque se salta.
        if disp_id is not None:
            try:
                disponibilidad = Disponibilidad.objects.get(id=disp_id)
            except Disponibilidad.DoesNotExist:
                raise serializers.ValidationError('Ese horario no existe.')

            if disponibilidad.cupos_disponibles <= 0:
                raise serializers.ValidationError('Ya no hay cupos disponibles en este horario.')

            if disponibilidad.es_presencial:
                user   = self.context['request'].user
                perfil = getattr(user, 'perfil', None)
                if perfil is None or not perfil.is_premium:
                    raise serializers.ValidationError(
                        'Esta modalidad con este tutor es presencial y requiere el Plan Premium.'
                    )

        # Si están mandando solo la dirección (PATCH), validamos que aplique de verdad
        elif 'direccion_alumno' in attrs and self.instance is not None:
            if self.instance.estado != 'confirmada':
                raise serializers.ValidationError('Solo puedes registrar la dirección después de pagar la tutoría.')
            if not self.get_es_presencial(self.instance):
                raise serializers.ValidationError('Este campo solo aplica a tutorías presenciales.')

        return attrs

    def create(self, validated_data):
        disp_id = validated_data.pop('disponibilidad_id')
        with transaction.atomic():
            try:
                disponibilidad = Disponibilidad.objects.select_for_update().get(id=disp_id)
            except Disponibilidad.DoesNotExist:
                raise serializers.ValidationError('Ese horario ya no existe.')

            if disponibilidad.cupos_disponibles <= 0:
                raise serializers.ValidationError('Ya no hay cupos disponibles en este horario.')

            cita = Cita.objects.create(
                usuario        = self.context['request'].user,
                servicio       = disponibilidad.servicio,
                disponibilidad = disponibilidad,
                tutor          = disponibilidad.tutor,
                fecha          = disponibilidad.fecha,
                hora           = disponibilidad.hora,
                estado         = 'pendiente',
            )
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
        Perfil.objects.get_or_create(usuario=user)
        return user