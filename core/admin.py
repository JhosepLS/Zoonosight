from django.contrib import admin
from .models import Departamento, Provincia, Distrito, TipoZoonosis, Paciente, Caso

@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo_ubigeo', 'poblacion']
    search_fields = ['nombre']

@admin.register(Provincia)
class ProvinciaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'departamento', 'codigo_ubigeo']
    list_filter = ['departamento']
    search_fields = ['nombre']

@admin.register(Distrito)
class DistritoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'provincia', 'codigo_ubigeo']
    list_filter = ['provincia__departamento']
    search_fields = ['nombre']

@admin.register(TipoZoonosis)
class TipoZoonosisAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo_cie10', 'animal_vector']
    search_fields = ['nombre']

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ['id', 'edad', 'tipo_edad', 'grupo_etario', 'genero']
    list_filter = ['grupo_etario', 'genero']

@admin.register(Caso)
class CasoAdmin(admin.ModelAdmin):
    list_display = ['id', 'zoonosis', 'distrito', 'anio', 'semana_epidemiologica', 'tipo_diagnostico']
    list_filter = ['anio', 'zoonosis', 'tipo_diagnostico']
    search_fields = ['distrito__nombre']
    date_hierarchy = 'fecha_notificacion'