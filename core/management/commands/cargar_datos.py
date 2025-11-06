import pandas as pd
from django.core.management.base import BaseCommand
from core.models import Departamento, Provincia, Distrito, TipoZoonosis, Paciente, Caso
from datetime import datetime, timedelta
from django.db import transaction

class Command(BaseCommand):
    help = 'Carga datos desde el CSV de MINSA'
    
    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str, help='Ruta al archivo CSV')
    
    def handle(self, *args, **kwargs):
        csv_path = kwargs['csv_path']
        self.stdout.write('Iniciando carga de datos...')
        
        # Leer CSV
        df = pd.read_csv(csv_path, encoding='utf-8', low_memory=False)
        self.stdout.write(f'Total de registros: {len(df)}')
        
        # Limpieza de datos
        df['provincia'] = df['provincia'].str.replace('ï¿½', 'Ñ')
        df['distrito'] = df['distrito'].str.replace('ï¿½', 'Ñ')
        df['departamento'] = df['departamento'].str.strip().str.upper()
        df['provincia'] = df['provincia'].str.strip().str.upper()
        df['distrito'] = df['distrito'].str.strip().str.upper()
        
        # Eliminar filas con datos faltantes críticos
        df = df.dropna(subset=['departamento', 'provincia', 'distrito', 'enfermedad', 'ano', 'semana'])
        self.stdout.write(f'Registros válidos: {len(df)}')
        
        # Cargar Departamentos con código único
        self.stdout.write('Cargando departamentos...')
        departamentos_unicos = df['departamento'].unique()
        dept_counter = 1
        for dept_nombre in departamentos_unicos:
            codigo = f"{dept_counter:02d}0000"
            Departamento.objects.get_or_create(
                nombre=dept_nombre,
                defaults={'codigo_ubigeo': codigo}
            )
            dept_counter += 1
        self.stdout.write(f'Departamentos cargados: {Departamento.objects.count()}')
        
        # Cargar Provincias con código único
        self.stdout.write('Cargando provincias...')
        provincias_df = df[['departamento', 'provincia']].drop_duplicates()
        prov_counter = 1
        for _, row in provincias_df.iterrows():
            try:
                dept = Departamento.objects.get(nombre=row['departamento'])
                codigo = f"{dept.codigo_ubigeo[:2]}{prov_counter:02d}00"
                Provincia.objects.get_or_create(
                    departamento=dept,
                    nombre=row['provincia'],
                    defaults={'codigo_ubigeo': codigo}
                )
                prov_counter += 1
            except Departamento.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Departamento no encontrado: {row["departamento"]}'))
        self.stdout.write(f'Provincias cargadas: {Provincia.objects.count()}')
        
        # Cargar Distritos usando ubigeo del CSV
        self.stdout.write('Cargando distritos...')
        distritos_df = df[['departamento', 'provincia', 'distrito', 'ubigeo']].drop_duplicates()
        distritos_creados = 0
        for _, row in distritos_df.iterrows():
            try:
                dept = Departamento.objects.get(nombre=row['departamento'])
                prov = Provincia.objects.get(departamento=dept, nombre=row['provincia'])
                ubigeo = str(row['ubigeo']).zfill(6)  # Asegurar 6 dígitos
                Distrito.objects.get_or_create(
                    provincia=prov,
                    nombre=row['distrito'],
                    defaults={'codigo_ubigeo': ubigeo}
                )
                distritos_creados += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Error en distrito: {e}'))
        self.stdout.write(f'Distritos cargados: {Distrito.objects.count()}')
        
        # Cargar Zoonosis
        self.stdout.write('Cargando tipos de zoonosis...')
        enfermedades_df = df[['enfermedad', 'diagnostic']].drop_duplicates()
        for _, row in enfermedades_df.iterrows():
            TipoZoonosis.objects.get_or_create(
                nombre=row['enfermedad'],
                defaults={'codigo_cie10': row['diagnostic']}
            )
        self.stdout.write(f'Zoonosis cargadas: {TipoZoonosis.objects.count()}')
        
        # Cargar Casos (por lotes con transacciones)
        self.stdout.write('Cargando casos...')
        batch_size = 500
        casos_creados = 0
        casos_error = 0
        
        for i in range(0, len(df), batch_size):
            batch = df[i:i+batch_size]
            
            with transaction.atomic():
                for _, row in batch.iterrows():
                    try:
                        # Buscar relaciones
                        zoonosis = TipoZoonosis.objects.get(nombre=row['enfermedad'])
                        dept = Departamento.objects.get(nombre=row['departamento'])
                        prov = Provincia.objects.get(departamento=dept, nombre=row['provincia'])
                        distrito = Distrito.objects.get(provincia=prov, nombre=row['distrito'])
                        
                        # Validar datos
                        if pd.isna(row['edad']) or pd.isna(row['tipo_edad']) or pd.isna(row['sexo']):
                            casos_error += 1
                            continue
                        
                        # Crear paciente
                        paciente = Paciente.objects.create(
                            edad=int(row['edad']),
                            tipo_edad=row['tipo_edad'],
                            genero=row['sexo']
                        )
                        
                        # Calcular fecha aproximada
                        try:
                            anio = int(row['ano'])
                            semana = int(row['semana'])
                            if semana < 1 or semana > 53:
                                semana = 1
                            fecha_inicio_anio = datetime(anio, 1, 1)
                            fecha_caso = fecha_inicio_anio + timedelta(weeks=semana-1)
                        except:
                            fecha_caso = datetime(2000, 1, 1)
                        
                        # Crear caso
                        Caso.objects.create(
                            zoonosis=zoonosis,
                            distrito=distrito,
                            paciente=paciente,
                            fecha_notificacion=fecha_caso.date(),
                            semana_epidemiologica=semana,
                            anio=anio,
                            codigo_diagnostico=row['diagnostic'],
                            tipo_diagnostico=row['tipo_dx'] if not pd.isna(row['tipo_dx']) else 'P',
                            codigo_diresa=str(row['diresa']) if not pd.isna(row['diresa']) else None
                        )
                        casos_creados += 1
                        
                    except Exception as e:
                        casos_error += 1
                        if casos_error < 10:  # Solo mostrar primeros 10 errores
                            self.stdout.write(self.style.WARNING(f'Error en caso: {e}'))
            
            # Progreso
            self.stdout.write(f'Procesados: {i+len(batch)}/{len(df)} | Casos creados: {casos_creados} | Errores: {casos_error}')
        
        self.stdout.write(self.style.SUCCESS(f'\n=== CARGA COMPLETADA ==='))
        self.stdout.write(self.style.SUCCESS(f'Total casos creados: {casos_creados}'))
        self.stdout.write(self.style.SUCCESS(f'Total errores: {casos_error}'))
        self.stdout.write(self.style.SUCCESS(f'Departamentos: {Departamento.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Provincias: {Provincia.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Distritos: {Distrito.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Zoonosis: {TipoZoonosis.objects.count()}'))