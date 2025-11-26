from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('dashboard/tendencias/', views.dashboard_tendencias, name='dashboard_tendencias'),
    path('dashboard/mapas/', views.dashboard_mapas, name='dashboard_mapas'),  # Nuevo
    path('api/tendencias/', views.api_tendencias, name='api_tendencias'),
    path('api/mapa-calor/', views.api_mapa_calor, name='api_mapa_calor'),  # Nuevo
]