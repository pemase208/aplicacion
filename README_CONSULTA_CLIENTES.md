# 🔍 Consulta de Clientes - Deudout

## Descripción

Esta nueva funcionalidad permite a usuarios y administradores realizar búsquedas integrales de clientes por DNI/NIE en:

1. **Base de datos local** - Todos los formularios rellenados
2. **Registro Público Concursal (RPC)** - Fuente oficial española
3. **BOE y Tablón Edictal Único** - Publicaciones oficiales

## 🚀 Características

### ✅ Búsqueda Local
- **Formularios RPC**: Registros de concursos mercantiles
- **Datos de Lector**: Información de usuarios del sistema
- **Usuarios Registrados**: Perfiles de usuarios del sistema

### ✅ Consultas Externas
- **RPC**: Consulta directa al registro oficial español
- **BOE**: Búsqueda en publicaciones oficiales (últimos 5 años)
- **Tablón Edictal**: Edictos y anuncios oficiales

### ✅ Interfaz Moderna
- Diseño responsive y atractivo
- Resultados organizados por secciones
- Indicadores visuales claros
- Mensajes informativos para cada fuente

## 📁 Archivos Implementados

### Backend
- `app.py` - Nueva ruta `/consulta_cliente`
- `utils/external_queries.py` - Módulo de consultas externas
- `models.py` - Modelos de base de datos existentes

### Frontend
- `templates/consulta_cliente.html` - Template principal
- `templates/menu.html` - Menú actualizado

### Utilidades
- `test_external_queries.py` - Script de pruebas
- `requirements.txt` - Dependencias actualizadas

## 🛠️ Instalación

### 1. Dependencias
```bash
pip install -r requirements.txt
```

### 2. Nuevas Dependencias Agregadas
```
beautifulsoup4==4.12.3  # Parsing HTML
html5lib==1.1           # Parser HTML robusto
```

### 3. Verificar Instalación
```bash
python test_external_queries.py
```

## 🔧 Configuración

### URLs de Consulta
Las URLs están configuradas en `utils/external_queries.py`:

- **RPC**: `https://www.registroconcursal.es/`
- **BOE**: `https://www.boe.es/buscar/consulta.php`
- **TEU**: `https://www.boe.es/tablon_edictal/`

### Headers HTTP
El sistema incluye headers realistas para evitar bloqueos:
- User-Agent moderno
- Accept-Language en español
- Delays aleatorios entre consultas

## 📱 Uso

### 1. Acceso
- Menú principal → "🔍 Consulta de Clientes"
- Disponible para usuarios, administradores y lectores

### 2. Búsqueda
1. Introducir DNI/NIE en el campo de búsqueda
2. Hacer clic en "🔍 Buscar Cliente"
3. Esperar resultados de todas las fuentes

### 3. Resultados
- **Base de Datos Local**: Resultados inmediatos
- **RPC**: Consulta en tiempo real
- **BOE/TEU**: Búsqueda en publicaciones oficiales

## 🧪 Pruebas

### Script de Prueba
```bash
python test_external_queries.py
```

### Pruebas Manuales
1. Acceder a la aplicación
2. Ir a "Consulta de Clientes"
3. Probar con DNIs reales y de ejemplo
4. Verificar resultados de todas las fuentes

## ⚠️ Consideraciones

### Limitaciones
- Las consultas externas dependen de la disponibilidad de los servicios
- Algunos sitios pueden tener protección anti-bot
- Los delays están configurados para ser respetuosos

### Mejoras Futuras
- Cache de consultas frecuentes
- Notificaciones por email de nuevos resultados
- Exportación de resultados a PDF/Excel
- API REST para integraciones externas

## 🎯 Casos de Uso

### Para Abogados
- Verificar estado de concursos mercantiles
- Consultar publicaciones oficiales
- Historial completo de clientes

### Para Administradores
- Auditoría de formularios rellenados
- Seguimiento de procedimientos
- Gestión de base de datos de clientes

### Para Usuarios
- Consulta de su propio historial
- Verificación de publicaciones oficiales
- Estado de procedimientos

## 🔒 Seguridad

### Autenticación
- Solo usuarios autenticados pueden acceder
- Verificación de sesión activa
- Logs de acceso registrados

### Privacidad
- Solo se muestran datos del DNI consultado
- No se almacenan consultas externas
- Cumplimiento RGPD

## 📊 Monitoreo

### Logs
- Todas las consultas se registran
- Errores de conexión externa
- Tiempo de respuesta de cada fuente

### Métricas
- Número de consultas por usuario
- Tasa de éxito por fuente externa
- Tiempo promedio de respuesta

## 🚨 Solución de Problemas

### Error de Conexión
- Verificar conectividad a internet
- Comprobar que los sitios externos estén disponibles
- Revisar logs de error

### Sin Resultados
- Verificar formato del DNI/NIE
- Comprobar que el DNI exista
- Revisar si hay cambios en las fuentes externas

### Errores de Parsing
- Los sitios externos pueden cambiar su estructura
- Actualizar patrones de búsqueda en `external_queries.py`
- Revisar logs de parsing

## 📞 Soporte

### Contacto
- **Desarrollador**: Pedro
- **Empresa**: Deudout Abogados
- **Proyecto**: Sistema de Gestión Legal

### Documentación
- Este README
- Código comentado
- Scripts de prueba

---

## 🎉 Agradecimientos

Esta funcionalidad es un regalo de agradecimiento a **Juan** y **Deudout** por haber arreglado la vida del desarrollador. 

¡Que disfruten de esta herramienta integral de consulta de clientes! 🚀
