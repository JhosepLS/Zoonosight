from django.db import models

class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    codigo_ubigeo = models.CharField(max_length=6, unique=True)
    region_natural = models.CharField(max_length=50, null=True, blank=True)
    poblacion = models.IntegerField(null=True, blank=True)
    area_km2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'departamento'
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Provincia(models.Model):
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='provincias')
    nombre = models.CharField(max_length=100)
    codigo_ubigeo = models.CharField(max_length=6, unique=True)
    
    class Meta:
        db_table = 'provincia'
        verbose_name = 'Provincia'
        verbose_name_plural = 'Provincias'
        ordering = ['nombre']
        unique_together = ['departamento', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.departamento.nombre}"


class Distrito(models.Model):
    provincia = models.ForeignKey(Provincia, on_delete=models.CASCADE, related_name='distritos')
    nombre = models.CharField(max_length=100)
    codigo_ubigeo = models.CharField(max_length=6, unique=True)
    
    class Meta:
        db_table = 'distrito'
        verbose_name = 'Distrito'
        verbose_name_plural = 'Distritos'
        ordering = ['nombre']
        unique_together = ['provincia', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.provincia.nombre}"


class TipoZoonosis(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(null=True, blank=True)
    agente_causante = models.CharField(max_length=200, null=True, blank=True)
    animal_vector = models.CharField(max_length=100, null=True, blank=True)
    periodo_incubacion = models.CharField(max_length=50, null=True, blank=True)
    codigo_cie10 = models.CharField(max_length=10, null=True, blank=True)
    
    class Meta:
        db_table = 'tipo_zoonosis'
        verbose_name = 'Tipo de Zoonosis'
        verbose_name_plural = 'Tipos de Zoonosis'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Paciente(models.Model):
    TIPO_EDAD_CHOICES = [
        ('A', 'Años'),
        ('M', 'Meses'),
        ('D', 'Días'),
    ]
    
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]
    
    edad = models.IntegerField()
    tipo_edad = models.CharField(max_length=1, choices=TIPO_EDAD_CHOICES)
    grupo_etario = models.CharField(max_length=50, null=True, blank=True)
    genero = models.CharField(max_length=1, choices=SEXO_CHOICES)
    ocupacion = models.CharField(max_length=100, null=True, blank=True)
    zona_residencia = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        db_table = 'paciente'
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
    
    def __str__(self):
        return f"Paciente {self.id} - {self.edad}{self.tipo_edad} - {self.genero}"
    
    def save(self, *args, **kwargs):
        # Calcular grupo etario automáticamente
        if self.tipo_edad == 'A':
            if self.edad <= 5:
                self.grupo_etario = 'Infancia'
            elif self.edad <= 17:
                self.grupo_etario = 'Adolescencia'
            elif self.edad <= 64:
                self.grupo_etario = 'Adulto'
            else:
                self.grupo_etario = 'Adulto Mayor'
        super().save(*args, **kwargs)


class Caso(models.Model):
    TIPO_DX_CHOICES = [
        ('P', 'Presuntivo'),
        ('C', 'Confirmado'),
    ]
    
    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('RECUPERADO', 'Recuperado'),
        ('FALLECIDO', 'Fallecido'),
    ]
    
    zoonosis = models.ForeignKey(TipoZoonosis, on_delete=models.CASCADE, related_name='casos')
    distrito = models.ForeignKey(Distrito, on_delete=models.CASCADE, related_name='casos')
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='casos')
    
    fecha_notificacion = models.DateField()
    semana_epidemiologica = models.IntegerField()
    anio = models.IntegerField()
    
    codigo_diagnostico = models.CharField(max_length=10)
    tipo_diagnostico = models.CharField(max_length=1, choices=TIPO_DX_CHOICES)
    estado_caso = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='ACTIVO')
    
    codigo_diresa = models.CharField(max_length=10, null=True, blank=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'caso'
        verbose_name = 'Caso'
        verbose_name_plural = 'Casos'
        ordering = ['-anio', '-semana_epidemiologica']
        indexes = [
            models.Index(fields=['anio', 'semana_epidemiologica']),
            models.Index(fields=['anio']),
            models.Index(fields=['zoonosis', 'anio']),
        ]
    
    def __str__(self):
        return f"Caso {self.id} - {self.zoonosis.nombre} - {self.anio}/S{self.semana_epidemiologica}"