from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('dashboard/tendencias/', views.dashboard_tendencias, name='dashboard_tendencias'),
    path('dashboard/mapas/', views.dashboard_mapas, name='dashboard_mapas'),
    path('dashboard/patrones/', views.dashboard_patrones, name='dashboard_patrones'),
    path('dashboard/reportes/', views.dashboard_reportes, name='dashboard_reportes'),
    path('api/tendencias/', views.api_tendencias, name='api_tendencias'),
    path('api/mapa-calor/', views.api_mapa_calor, name='api_mapa_calor'),
    path('api/patrones-estacionales/', views.api_patrones_estacionales, name='api_patrones_estacionales'),
    path('api/generar-reporte/', views.api_generar_reporte, name='api_generar_reporte'),
]