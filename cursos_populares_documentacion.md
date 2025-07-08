# Cursos Populares - Nueva Funcionalidad

## 🎯 Cambio Implementado

Se ha reemplazado el sistema de "cursos destacados" (manual) por un sistema automático de "cursos populares" basado en la cantidad de estudiantes inscritos.

## 🔄 Lógica de Cursos Populares

### Criterios de Selección:
1. **Primera prioridad:** Cursos con más estudiantes inscritos en el último mes
2. **Segunda prioridad:** Si no hay cursos con estudiantes recientes, mostrar por orden de creación (más recientes primero)

### Cálculo de Popularidad:
- Se consideran estudiantes que se registraron en los últimos 30 días
- Se cuenta la cantidad de estudiantes por curso
- Se ordenan por cantidad de estudiantes (descendente) y luego por fecha de creación

## 📊 Cambios en la Interfaz

### Página de Inicio (`index.html`)
- **Antes:** "Cursos destacados" con badge manual
- **Ahora:** "Cursos más populares del mes" con:
  - Icono de fuego 🔥
  - Badge mostrando cantidad de estudiantes del mes
  - Badge alternativo mostrando total de estudiantes si no hay recientes

### Lista de Cursos (`course_list.html`)
- **Antes:** Badge "Destacado" para cursos marcados manualmente
- **Ahora:** Contador de estudiantes totales por curso

### Dashboard del Instructor (`instructor_dashboard.html`)
- **Antes:** Columna "Destacado" con sí/no
- **Ahora:** Columna "Estudiantes" con contador y badge de color

## 🛠️ Archivos Modificados

### Backend
1. **`core/views.py`**
   - Nueva lógica para calcular cursos populares
   - Filtrado por estudiantes recientes
   - Fallback a orden de creación

2. **`courses/forms.py`**
   - Eliminado campo `featured` del formulario

3. **`courses/views.py`**
   - Eliminado filtro por cursos destacados

### Frontend
1. **`templates/index.html`**
   - Nuevo diseño para cursos populares
   - Badges dinámicos con contadores

2. **`templates/courses/course_list.html`**
   - Reemplazado badge "Destacado" por contador de estudiantes

3. **`templates/courses/instructor_dashboard.html`**
   - Nueva columna "Estudiantes" con contadores

4. **`templates/courses/course_form.html`**
   - Eliminado campo "Destacado" del formulario

## 🧪 Comando de Prueba

Se creó un comando para probar la funcionalidad:

```bash
python manage.py test_popular_courses
```

Este comando:
- Crea estudiantes de prueba
- Los inscribe en cursos existentes
- Muestra estadísticas de popularidad

## 📈 Beneficios del Cambio

### Para Estudiantes:
- ✅ Cursos más relevantes basados en popularidad real
- ✅ Transparencia sobre la cantidad de estudiantes
- ✅ Descubrimiento de cursos activos

### Para Instructores:
- ✅ Motivación para crear contenido atractivo
- ✅ Feedback automático sobre el éxito de sus cursos
- ✅ Eliminación de favoritismos manuales

### Para la Plataforma:
- ✅ Sistema automático y objetivo
- ✅ Mejor engagement de usuarios
- ✅ Datos reales de popularidad

## 🔧 Configuración Técnica

### Variables Importantes:
- **Período de popularidad:** 30 días
- **Límite de cursos mostrados:** 5
- **Orden de prioridad:** Estudiantes recientes > Fecha de creación

### Consultas de Base de Datos:
```python
# Estudiantes recientes
recent_users = User.objects.filter(
    date_joined__gte=one_month_ago,
    user_type='student'
)

# Cursos populares
popular_courses = MicroCourse.objects.annotate(
    recent_student_count=Count('students', filter=Q(students__in=recent_users))
).filter(
    recent_student_count__gt=0
).order_by('-recent_student_count', '-created_at')[:5]
```

## 🚀 Cómo Funciona

1. **Cada vez que se carga la página de inicio:**
   - Se calcula la fecha de hace 30 días
   - Se buscan estudiantes registrados en ese período
   - Se cuentan estudiantes por curso
   - Se ordenan por popularidad

2. **Si no hay cursos con estudiantes recientes:**
   - Se muestran los cursos más recientes
   - Se incluye contador total de estudiantes

3. **Los badges muestran:**
   - Verde: "X estudiantes este mes" (si hay recientes)
   - Azul: "X estudiantes total" (si no hay recientes)

## 📝 Notas de Implementación

- El campo `featured` en el modelo se mantiene por compatibilidad
- No se requiere migración de base de datos
- El sistema es retrocompatible
- Se puede revertir fácilmente si es necesario

---

**Estado:** ✅ Implementado y listo para producción
**Fecha:** Diciembre 2024
**Versión:** 2.0 