# 📚 Documentación del Sistema de Cookies - SRI LMS

## 🎯 Resumen Ejecutivo

El sistema de cookies implementado en SRI LMS proporciona una experiencia de usuario altamente personalizable, permitiendo a los usuarios configurar sus preferencias de tema, layout, notificaciones y otras opciones que se mantienen persistentes entre sesiones.

## 🏗️ Arquitectura del Sistema

### Componentes Principales

1. **Middleware de Cookies** (`core/middleware.py`)
   - Procesa cookies antes y después de cada request
   - Valida valores de cookies
   - Establece valores por defecto

2. **Context Processor** (`core/context_processors.py`)
   - Proporciona preferencias a todas las plantillas
   - Maneja errores gracefully
   - Valores por defecto seguros

3. **Vistas de Gestión** (`users/views.py`)
   - API para actualizar preferencias
   - API para obtener preferencias actuales
   - Validación de datos

4. **Interfaz de Usuario**
   - Modal de preferencias
   - JavaScript para gestión dinámica
   - Aplicación inmediata de cambios

## ⚙️ Configuración

### Settings (`sri_lms/settings.py`)

```python
# Configuración de cookies personalizadas
CUSTOM_COOKIES = {
    'theme': {
        'name': 'sri_theme',
        'max_age': 365 * 24 * 60 * 60,  # 1 año
        'secure': not DEBUG,
        'httponly': False,
        'samesite': 'Lax'
    },
    # ... más configuraciones
}

# Validación de valores permitidos
ALLOWED_THEMES = ['light', 'dark', 'auto']
ALLOWED_LAYOUTS = ['compact', 'comfortable']
# ... más validaciones
```

### Middleware

```python
MIDDLEWARE = [
    # ... otros middlewares
    'core.middleware.CookiePreferencesMiddleware',
]
```

### Context Processors

```python
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                # ... otros processors
                'core.context_processors.cookie_preferences',
            ],
        },
    },
]
```

## 🍪 Tipos de Cookies Implementadas

### 1. **Tema Visual** (`sri_theme`)
- **Valores:** `light`, `dark`, `auto`
- **Descripción:** Controla el tema visual de la plataforma
- **Duración:** 1 año
- **Impacto:** Cambio inmediato de colores y estilos

### 2. **Layout** (`sri_layout`)
- **Valores:** `comfortable`, `compact`
- **Descripción:** Controla el espaciado de la interfaz
- **Duración:** 1 año
- **Impacto:** Ajuste de márgenes y padding

### 3. **Notificaciones** (`sri_notifications`)
- **Valores:** `enabled`, `disabled`
- **Descripción:** Controla las notificaciones del sistema
- **Duración:** 1 año
- **Impacto:** Mostrar/ocultar notificaciones

### 4. **Estilo de Aprendizaje** (`sri_learning_style`)
- **Valores:** `visual`, `auditory`, `kinesthetic`
- **Descripción:** Personaliza el contenido según el estilo de aprendizaje
- **Duración:** 1 año
- **Impacto:** Recomendaciones de contenido

### 5. **Nivel de Dificultad** (`sri_difficulty`)
- **Valores:** `beginner`, `intermediate`, `advanced`
- **Descripción:** Influencia las recomendaciones de cursos
- **Duración:** 1 año
- **Impacto:** Filtrado de contenido

### 6. **Ritmo de Aprendizaje** (`sri_pace`)
- **Valores:** `slow`, `normal`, `fast`
- **Descripción:** Ajusta la velocidad de presentación
- **Duración:** 1 año
- **Impacto:** Velocidad de navegación

### 7. **Estilo de Feedback** (`sri_feedback`)
- **Valores:** `detailed`, `summary`, `minimal`
- **Descripción:** Controla el detalle en resultados de tests
- **Duración:** 1 año
- **Impacto:** Nivel de información mostrada

### 8. **Analytics** (`sri_analytics`)
- **Valores:** `enabled`, `disabled`
- **Descripción:** Permite análisis de uso
- **Duración:** 1 año
- **Impacto:** Recopilación de datos

### 9. **Preferencias de Tests** (`sri_test_prefs`)
- **Valores:** JSON con configuraciones específicas
- **Descripción:** Configuraciones avanzadas para tests
- **Duración:** 1 año
- **Impacto:** Personalización de evaluaciones

## 🔧 API Endpoints

### Actualizar Preferencias
```
POST /users/preferences/update/
Content-Type: application/json

{
    "theme": "dark",
    "layout": "compact",
    "notifications": "enabled",
    "learning_style": "visual",
    "difficulty": "intermediate",
    "pace": "normal",
    "feedback_style": "detailed",
    "analytics": "enabled"
}
```

**Respuesta:**
```json
{
    "success": true,
    "message": "Preferencias actualizadas correctamente",
    "updates": {
        "theme": "dark",
        "layout": "compact"
    }
}
```

### Obtener Preferencias
```
GET /users/preferences/get/
```

**Respuesta:**
```json
{
    "success": true,
    "preferences": {
        "theme": "light",
        "layout": "comfortable",
        "notifications": "enabled",
        "learning_style": "visual",
        "difficulty": "beginner",
        "pace": "normal",
        "feedback_style": "detailed",
        "analytics": "enabled",
        "test_preferences": {}
    }
}
```

## 🎨 Sistema de Temas

### Variables CSS

```css
:root {
    --primary-color: #1a3a6c;
    --secondary-color: #2ecc71;
    --background-light: #f8f9fa;
    --text-color: #333;
    --card-bg: #fff;
    --border-color: #dee2e6;
    --shadow: 0 2px 8px rgba(0,0,0,0.04);
}

[data-theme="dark"] {
    --primary-color: #2c5aa0;
    --secondary-color: #27ae60;
    --background-light: #1a1a1a;
    --text-color: #ffffff;
    --card-bg: #2d2d2d;
    --border-color: #404040;
    --shadow: 0 2px 8px rgba(0,0,0,0.2);
}
```

### Detección Automática

```javascript
// Detectar preferencia del sistema
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
```

## 🔒 Seguridad

### Configuraciones de Seguridad

1. **HTTPS Only** (en producción)
   ```python
   'secure': not DEBUG
   ```

2. **SameSite Protection**
   ```python
   'samesite': 'Lax'
   ```

3. **Validación de Valores**
   ```python
   ALLOWED_THEMES = ['light', 'dark', 'auto']
   ```

4. **Duración Limitada**
   ```python
   'max_age': 365 * 24 * 60 * 60  # 1 año máximo
   ```

### Validación de Datos

```python
def _get_valid_cookie(self, request, cookie_name, default_value, allowed_values):
    value = request.COOKIES.get(cookie_name, default_value)
    return value if value in allowed_values else default_value
```

## 🚀 Funcionalidades JavaScript

### Gestión de Preferencias

```javascript
// Aplicar tema
function applyTheme(theme) {
    const html = document.documentElement;
    if (theme === 'auto') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        html.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    } else {
        html.setAttribute('data-theme', theme);
    }
}

// Aplicar layout
function applyLayout(layout) {
    const body = document.body;
    if (layout === 'compact') {
        body.classList.add('layout-compact');
    } else {
        body.classList.remove('layout-compact');
    }
}
```

### Notificaciones

```javascript
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    // ... configuración
    document.body.appendChild(notification);
}
```

## 🧪 Testing

### Comando de Prueba

```bash
python manage.py test_cookie_system
```

### Pruebas Incluidas

1. **Login y Autenticación**
2. **Obtención de Preferencias**
3. **Actualización de Preferencias**
4. **Validación de Datos**
5. **Diferentes Temas**
6. **Middleware**
7. **Configuración del Sistema**

### Ejemplo de Uso

```bash
# Probar con usuario específico
python manage.py test_cookie_system --username mi_usuario

# Probar con usuario por defecto
python manage.py test_cookie_system
```

## 📱 Interfaz de Usuario

### Modal de Preferencias

- **Acceso:** Botón de engranaje (⚙️) en el header
- **Campos:** 8 tipos de preferencias configurables
- **Guardado:** AJAX con feedback inmediato
- **Aplicación:** Cambios instantáneos sin recarga

### Características del Modal

1. **Diseño Responsivo**
2. **Validación en Tiempo Real**
3. **Feedback Visual**
4. **Aplicación Inmediata**
5. **Persistencia de Datos**

## 🔄 Flujo de Datos

### 1. Carga de Página
```
Request → Middleware → Context Processor → Template → Response
```

### 2. Actualización de Preferencias
```
JavaScript → AJAX → View → Validation → Cookie Set → Response
```

### 3. Aplicación de Cambios
```
Cookie Read → JavaScript → DOM Update → Visual Change
```

## 📊 Métricas y Analytics

### Datos Recopilados (con consentimiento)

1. **Preferencias de Tema**
2. **Uso de Layout**
3. **Configuración de Notificaciones**
4. **Estilo de Aprendizaje**
5. **Nivel de Dificultad**
6. **Ritmo de Uso**
7. **Patrones de Feedback**

### Uso de Datos

- **Personalización:** Mejorar recomendaciones
- **Optimización:** Ajustar interfaz
- **Análisis:** Entender patrones de uso
- **Desarrollo:** Priorizar nuevas funcionalidades

## 🛠️ Mantenimiento

### Logs

```python
logger = logging.getLogger(__name__)
logger.error(f"Error al obtener preferencias de cookies: {e}")
```

### Monitoreo

- **Errores de Validación**
- **Fallos de Middleware**
- **Problemas de Context Processor**
- **Errores de JavaScript**

### Limpieza

```python
# Cookies expiran automáticamente después de 1 año
'max_age': 365 * 24 * 60 * 60
```

## 🔮 Futuras Mejoras

### Funcionalidades Planificadas

1. **Sincronización entre Dispositivos**
2. **Preferencias por Curso**
3. **Temas Personalizados**
4. **Exportar/Importar Preferencias**
5. **Analytics Avanzados**
6. **A/B Testing de Preferencias**

### Optimizaciones Técnicas

1. **Cache de Preferencias**
2. **Compresión de Cookies**
3. **Lazy Loading de Temas**
4. **Service Worker para Offline**

## 📋 Checklist de Implementación

### ✅ Completado

- [x] Configuración de cookies en settings
- [x] Middleware de procesamiento
- [x] Context processor
- [x] Vistas de gestión
- [x] URLs de API
- [x] Modal de preferencias
- [x] JavaScript de gestión
- [x] Sistema de temas
- [x] Validación de datos
- [x] Seguridad implementada
- [x] Comando de testing
- [x] Documentación completa

### 🔄 En Desarrollo

- [ ] Analytics avanzados
- [ ] Preferencias por curso
- [ ] Sincronización entre dispositivos

### 📅 Planificado

- [ ] Temas personalizados
- [ ] Exportar/importar preferencias
- [ ] A/B testing
- [ ] Service worker

## 🎯 Beneficios Implementados

### Para Usuarios

1. **Experiencia Personalizada**
2. **Accesibilidad Mejorada**
3. **Control Total de Preferencias**
4. **Persistencia entre Sesiones**
5. **Cambios Inmediatos**

### Para Desarrolladores

1. **Arquitectura Escalable**
2. **Código Mantenible**
3. **Testing Automatizado**
4. **Documentación Completa**
5. **Seguridad Robusta**

### Para el Negocio

1. **Mayor Engagement**
2. **Mejor Retención**
3. **Datos de Usuario**
4. **Optimización Continua**
5. **Ventaja Competitiva**

---

**Estado:** ✅ Implementado y Funcional
**Versión:** 1.0.0
**Última Actualización:** Diciembre 2024
**Próxima Revisión:** Enero 2025 