from django.shortcuts import render
from django.db.models import Count, Q, Avg
from django.http import JsonResponse
from django.db.models import Sum
from datetime import datetime
import calendar
from .models import Caso, TipoZoonosis, Departamento, Provincia, Distrito
import json

def home(view):
    """Vista principal - Dashboard"""
    return render(request, 'core/home.html')

def dashboard_tendencias(request):
    """Vista del dashboard de tendencias históricas"""
    # Obtener lista de zoonosis para el filtro
    zoonosis_list = TipoZoonosis.objects.all().order_by('nombre')
    
    # Obtener años disponibles
    anos_queryset = Caso.objects.values_list('anio', flat=True).distinct().order_by('anio')
    anos = list(anos_queryset)  # Convertir a lista
    
    # Debug - imprimir en consola
    print(f"Zoonosis encontradas: {zoonosis_list.count()}")
    print(f"Años disponibles: {anos}")
    
    context = {
        'zoonosis_list': zoonosis_list,
        'anos': anos,
    }
    return render(request, 'core/dashboard_tendencias.html', context)

def api_tendencias(request):
    """API para obtener datos de tendencias"""
    zoonosis_id = request.GET.get('zoonosis_id')
    anio_inicio = request.GET.get('anio_inicio')
    anio_fin = request.GET.get('anio_fin')
    
    # Validar parámetros
    if not all([zoonosis_id, anio_inicio, anio_fin]):
        return JsonResponse({'error': 'Parámetros incompletos'}, status=400)
    
    # Consultar casos
    casos = Caso.objects.filter(
        zoonosis_id=zoonosis_id,
        anio__gte=anio_inicio,
        anio__lte=anio_fin
    )
    
    # Agrupar por año
    datos_por_anio = casos.values('anio').annotate(
        total_casos=Count('id')
    ).order_by('anio')
    
    # Preparar datos para el gráfico
    anos = [item['anio'] for item in datos_por_anio]
    casos_totales = [item['total_casos'] for item in datos_por_anio]
    
    # Calcular estadísticas
    total = sum(casos_totales)
    promedio = total / len(casos_totales) if casos_totales else 0
    
    # Calcular tendencia simple
    if len(casos_totales) >= 2:
        tendencia = ((casos_totales[-1] - casos_totales[0]) / casos_totales[0] * 100) if casos_totales[0] > 0 else 0
    else:
        tendencia = 0
    
    # Año con mayor incidencia
    if casos_totales:
        max_index = casos_totales.index(max(casos_totales))
        anio_max = anos[max_index]
        casos_max = casos_totales[max_index]
    else:
        anio_max = None
        casos_max = 0
    
    data = {
        'anos': anos,
        'casos': casos_totales,
        'estadisticas': {
            'total': total,
            'promedio': round(promedio, 1),
            'tendencia': round(tendencia, 1),
            'anio_max': anio_max,
            'casos_max': casos_max
        }
    }
    
    return JsonResponse(data)

def dashboard_mapas(request):
    """Vista del dashboard de mapas de calor"""
    zoonosis_list = TipoZoonosis.objects.all().order_by('nombre')
    anos = Caso.objects.values_list('anio', flat=True).distinct().order_by('anio')
    
    context = {
        'zoonosis_list': zoonosis_list,
        'anos': list(anos),
    }
    return render(request, 'core/dashboard_mapas.html', context)

def api_mapa_calor(request):
    """API para obtener datos del mapa de calor"""
    zoonosis_id = request.GET.get('zoonosis_id')
    anio = request.GET.get('anio')
    escala = request.GET.get('escala', 'total')  # total o percapita
    
    if not all([zoonosis_id, anio]):
        return JsonResponse({'error': 'Parámetros incompletos'}, status=400)
    
    # Consultar casos agrupados por departamento
    casos_por_depto = Caso.objects.filter(
        zoonosis_id=zoonosis_id,
        anio=anio
    ).values(
        'distrito__provincia__departamento__nombre',
        'distrito__provincia__departamento__id'
    ).annotate(
        total_casos=Count('id')
    ).order_by('-total_casos')
    
    # Preparar datos para el mapa
    departamentos_data = []
    for item in casos_por_depto:
        dept_nombre = item['distrito__provincia__departamento__nombre']
        if dept_nombre:
            departamentos_data.append({
                'nombre': dept_nombre,
                'casos': item['total_casos']
            })
    
    # Calcular estadísticas
    total_nacional = sum(d['casos'] for d in departamentos_data)
    num_deptos = len(departamentos_data)
    promedio = total_nacional / num_deptos if num_deptos > 0 else 0
    
    # Top 5 departamentos
    top5 = departamentos_data[:5] if len(departamentos_data) >= 5 else departamentos_data
    
    data = {
        'departamentos': departamentos_data,
        'estadisticas': {
            'total_nacional': total_nacional,
            'departamentos_afectados': num_deptos,
            'promedio': round(promedio, 1),
            'top5': top5
        }
    }
    
    return JsonResponse(data)

