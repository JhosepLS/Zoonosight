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

def dashboard_patrones(request):
    """Vista del dashboard de patrones estacionales"""
    zoonosis_list = TipoZoonosis.objects.all().order_by('nombre')
    anos = Caso.objects.values_list('anio', flat=True).distinct().order_by('anio')
    departamentos = Departamento.objects.all().order_by('nombre')
    
    context = {
        'zoonosis_list': zoonosis_list,
        'anos': list(anos),
        'departamentos': departamentos,
    }
    return render(request, 'core/dashboard_patrones.html', context)

def api_patrones_estacionales(request):
    """API para obtener patrones estacionales por mes con comparación entre zoonosis"""
    zoonosis_ids = request.GET.getlist('zoonosis_ids[]')
    anio_inicio = request.GET.get('anio_inicio')
    anio_fin = request.GET.get('anio_fin')
    departamento_id = request.GET.get('departamento_id')
    
    if not all([zoonosis_ids, anio_inicio, anio_fin]):
        return JsonResponse({'error': 'Parámetros incompletos'}, status=400)
    
    # Preparar datasets para cada zoonosis seleccionada
    datasets = []
    colores = [
        {'border': 'rgb(255, 99, 132)', 'bg': 'rgba(255, 99, 132, 0.2)'},
        {'border': 'rgb(54, 162, 235)', 'bg': 'rgba(54, 162, 235, 0.2)'},
        {'border': 'rgb(255, 206, 86)', 'bg': 'rgba(255, 206, 86, 0.2)'},
        {'border': 'rgb(75, 192, 192)', 'bg': 'rgba(75, 192, 192, 0.2)'},
        {'border': 'rgb(153, 102, 255)', 'bg': 'rgba(153, 102, 255, 0.2)'},
    ]
    
    estadisticas_globales = {
        'total_general': 0,
        'zoonosis_data': []
    }
    
    for idx, zoonosis_id in enumerate(zoonosis_ids):
        # Construir consulta para esta zoonosis
        query = Q(zoonosis_id=zoonosis_id, anio__gte=anio_inicio, anio__lte=anio_fin)
        
        if departamento_id and departamento_id != 'nacional':
            query &= Q(distrito__provincia__departamento_id=departamento_id)
        
        casos = Caso.objects.filter(query)
        
        # Calcular casos por mes
        meses_data = {}
        for mes in range(1, 13):
            semana_inicio = (mes - 1) * 4 + 1
            semana_fin = mes * 4
            
            casos_mes = casos.filter(
                semana_epidemiologica__gte=semana_inicio,
                semana_epidemiologica__lte=semana_fin
            ).count()
            
            meses_data[mes] = casos_mes
        
        casos_por_mes = [meses_data[i] for i in range(1, 13)]
        total_casos = sum(casos_por_mes)
        
        # Obtener nombre de la zoonosis
        zoonosis = TipoZoonosis.objects.get(id=zoonosis_id)
        
        # Añadir dataset
        color = colores[idx % len(colores)]
        datasets.append({
            'label': zoonosis.nombre,
            'data': casos_por_mes,
            'borderColor': color['border'],
            'backgroundColor': color['bg'],
            'total': total_casos
        })
        
        # Estadísticas por zoonosis
        if casos_por_mes:
            mes_max_index = casos_por_mes.index(max(casos_por_mes))
            mes_min_index = casos_por_mes.index(min(casos_por_mes))
        else:
            mes_max_index = 0
            mes_min_index = 0
        
        meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        
        estadisticas_globales['zoonosis_data'].append({
            'nombre': zoonosis.nombre,
            'total': total_casos,
            'promedio': round(total_casos / 12, 1),
            'mes_max': meses_nombres[mes_max_index],
            'casos_max': casos_por_mes[mes_max_index],
            'mes_min': meses_nombres[mes_min_index],
            'casos_min': casos_por_mes[mes_min_index]
        })
        
        estadisticas_globales['total_general'] += total_casos
    
    # Meses del año
    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    data = {
        'meses': meses,
        'datasets': datasets,
        'estadisticas': estadisticas_globales
    }
    
    return JsonResponse(data)

def dashboard_reportes(request):
    """Vista del generador de reportes"""
    zoonosis_list = TipoZoonosis.objects.all().order_by('nombre')
    anos = Caso.objects.values_list('anio', flat=True).distinct().order_by('anio')
    departamentos = Departamento.objects.all().order_by('nombre')
    
    context = {
        'zoonosis_list': zoonosis_list,
        'anos': list(anos),
        'departamentos': departamentos,
    }
    return render(request, 'core/dashboard_reportes.html', context)

def api_generar_reporte(request):
    """API para generar vista previa de reporte"""
    departamentos_ids = request.GET.getlist('departamentos[]')
    zoonosis_id = request.GET.get('zoonosis_id')
    anio_inicio = request.GET.get('anio_inicio')
    anio_fin = request.GET.get('anio_fin')
    
    if not all([departamentos_ids, zoonosis_id, anio_inicio, anio_fin]):
        return JsonResponse({'error': 'Parámetros incompletos'}, status=400)
    
    # Obtener datos para cada departamento
    datos_departamentos = []
    
    for dept_id in departamentos_ids:
        casos = Caso.objects.filter(
            zoonosis_id=zoonosis_id,
            anio__gte=anio_inicio,
            anio__lte=anio_fin,
            distrito__provincia__departamento_id=dept_id
        )
        
        total_casos = casos.count()
        casos_por_anio = casos.values('anio').annotate(total=Count('id')).order_by('anio')
        
        num_anios = int(anio_fin) - int(anio_inicio) + 1
        promedio_anual = total_casos / num_anios if num_anios > 0 else 0
        
        # Calcular tendencia
        if len(casos_por_anio) >= 2:
            primer_anio_casos = list(casos_por_anio)[0]['total']
            ultimo_anio_casos = list(casos_por_anio)[-1]['total']
            tendencia = ((ultimo_anio_casos - primer_anio_casos) / primer_anio_casos * 100) if primer_anio_casos > 0 else 0
        else:
            tendencia = 0
        
        departamento = Departamento.objects.get(id=dept_id)
        
        datos_departamentos.append({
            'nombre': departamento.nombre,
            'total_casos': total_casos,
            'promedio_anual': round(promedio_anual, 1),
            'tendencia': round(tendencia, 1),
            'casos_por_anio': list(casos_por_anio)
        })
    
    # Obtener nombre de zoonosis
    zoonosis = TipoZoonosis.objects.get(id=zoonosis_id)
    
    data = {
        'departamentos': datos_departamentos,
        'zoonosis_nombre': zoonosis.nombre,
        'periodo': f"{anio_inicio}-{anio_fin}"
    }
    
    return JsonResponse(data)