---

# ZoonoSight - Sistema de Análisis de Patrones Epidemiológicos de Zoonosis

Plataforma web para análisis histórico y visualización de datos de vigilancia epidemiológica de zoonosis en Perú (2000-2023).

---

## Requisitos Previos

* Python 3.11 o superior
* pip (gestor de paquetes de Python)
* Git

---

## Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/zoonosight.git
cd zoonosight
```

### 2. Crear y Activar Entorno Virtual

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Base de Datos

```bash
# Crear las tablas en la base de datos
python manage.py migrate

# Crear superusuario para acceder al admin
python manage.py createsuperuser
```

### 5. Cargar Datos (Opcional)

Si tienes el archivo CSV de datos:

```bash
python manage.py cargar_datos datos_abiertos_vigilancia_zoonosis_2000_2023.csv
```

### 6. Ejecutar Servidor de Desarrollo

```bash
python manage.py runserver
```

La aplicación estará disponible en:
`http://127.0.0.1:8000/`

Panel de administración:
`http://127.0.0.1:8000/admin/`

## Comandos Útiles

### Crear migraciones después de cambios en modelos
```bash
python manage.py makemigrations
python manage.py migrate
```

### Acceder a la shell de Django
```bash
python manage.py shell
```

### Crear un superusuario adicional
```bash
python manage.py createsuperuser
```

## Estado del Proyecto

- Fase 1: Inicio (Completado)
- Fase 2: Elaboración (Completado)
- Fase 3: Construcción (En progreso - Sprint 1)
- Fase 4: Transición (Pendiente)


---