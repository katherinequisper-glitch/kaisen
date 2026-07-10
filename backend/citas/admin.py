from django.contrib import admin
from .models import Servicio, Cita, Disponibilidad, Perfil, Tutor, ServicioTutor


@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'activo')
    list_editable = ('activo',)
    search_fields = ('nombre',)


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display  = ('usuario', 'is_premium', 'creado_en')
    list_editable = ('is_premium',)
    search_fields = ('usuario__username', 'usuario__email')
    list_filter   = ('is_premium',)


class ServicioTutorInline(admin.TabularInline):
    model = ServicioTutor
    extra = 1
    verbose_name = "Tutor asignado"
    verbose_name_plural = "Tutores asignados (elige modalidad por cada uno)"


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'precio', 'duracion_minutos', 'activo')
    list_editable = ('precio', 'activo')
    list_filter   = ('activo',)
    inlines       = [ServicioTutorInline]


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display  = ('usuario', 'servicio', 'tutor', 'fecha', 'hora', 'estado', 'expira_en')
    list_filter   = ('estado', 'fecha')
    search_fields = ('usuario__username', 'servicio__nombre')
    readonly_fields = ('meet_link', 'meet_password', 'direccion_alumno')


@admin.register(Disponibilidad)
class DisponibilidadAdmin(admin.ModelAdmin):
    list_display  = ('servicio', 'tutor', 'fecha', 'hora', 'cupo_maximo', 'cupos_disponibles_display')
    list_filter   = ('servicio', 'tutor')
    list_editable = ('cupo_maximo',)

    def cupos_disponibles_display(self, obj):
        return f"{obj.cupos_disponibles}/{obj.cupo_maximo}"
    cupos_disponibles_display.short_description = 'Cupos libres'