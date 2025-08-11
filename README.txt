# Aplicación de Formularios Modernizada

## Sistema de Roles Implementado

### Roles de Usuario
- **Administrador**: Control total del sistema
- **Usuario**: Acceso completo a formularios
- **Lector**: Acceso limitado con expiración de 10 días

### Funcionalidades por Rol

#### 🔧 Administrador
- ✅ **Panel de Administración de Usuarios**: Crear, editar, eliminar usuarios
- ✅ **Panel de Administración de Bancos**: Gestión de base de datos de bancos
- ✅ **Panel de Administración del Doc. 9**: Configuración y estadísticas
- ✅ **Log de Accesos**: Registro detallado con IP, ubicación, navegador, SO
- ✅ **Acceso completo** a todos los formularios y funcionalidades

#### 👤 Usuario
- ✅ **Acceso completo** a todos los formularios
- ✅ **Sin acceso** a paneles de administración
- ✅ **Sin restricciones** de tiempo

#### 👁️ Lector
- ✅ **Acceso limitado** solo a formularios asignados
- ✅ **Datos precargados** según configuración
- ✅ **Expiración automática** de 10 días
- ✅ **Sin acceso** a paneles de administración

## Estructura del Proyecto

- app.py: Punto de entrada principal, rutas y lógica base.
- models.py: Modelos de base de datos (User, Banco, AccessLog, FormularioRPC).
- static/
  - deudout_style.css: Estilos personalizados (complementa Bootstrap 5).
- templates/
  - base.html: Plantilla base moderna con Bootstrap 5.
  - menu.html: Menú principal responsivo con opciones por rol.
  - login.html: Login moderno como página de acceso principal.
  - formulario_generico.html: Ejemplo de formulario moderno.
  - formulario_rpc.html: Formulario RPC modernizado.
  - doc9_form.html: Formulario Doc. 9 modernizado.
  - admin_usuarios.html: Gestión de usuarios (solo admin).
  - admin_bancos.html: Gestión de bancos (solo admin).
  - admin_doc9.html: Administración Doc. 9 (solo admin).
  - admin_logs.html: Log de accesos (solo admin).
  - ...otras vistas.
- instance/
  - mibasedatos.db: Base de datos SQLite.
- utils/: Funciones auxiliares.

## Características Modernas

### Diseño Visual
- **Bootstrap 5**: Framework CSS moderno y responsivo.
- **Cards**: Contenedores elegantes para formularios y contenido.
- **Navbar**: Barra de navegación moderna con menú hamburguesa.
- **Botones**: Estilos consistentes con gradientes y efectos hover.
- **Tablas**: Diseño moderno con rayas y hover effects.
- **Formularios**: Campos con validación visual y estados de focus.

### Funcionalidades
- **Responsive**: Se adapta a móviles, tablets y desktop.
- **Accesibilidad**: Etiquetas semánticas y navegación por teclado.
- **Mensajes Flash**: Alertas modernas con categorías (success, danger, info).
- **JavaScript**: Funcionalidades interactivas mantenidas y mejoradas.
- **Logging**: Registro detallado de accesos con geolocalización.
- **Sistema de Roles**: Control granular de permisos por usuario.

## Migración de Vistas

1. Extiende siempre de `base.html`:
   ```jinja
   {% extends "base.html" %}
   {% block content %}
   ...
   {% endblock %}
   ```
2. Usa clases de Bootstrap 5 para formularios, tablas y botones.
3. Para mensajes flash, usa:
   ```python
   flash("Mensaje", "success"|"danger"|"info")
   ```
4. Todas las plantillas principales ya están modernizadas.

## Ejecución

1. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Ejecuta la app:
   ```bash
   python app.py
   ```
3. Accede en tu navegador a `http://localhost:5000`

## Notas
- El usuario admin por defecto es `pedro` / `admin1234`.
- Todas las plantillas principales están modernizadas con Bootstrap 5.
- Los formularios mantienen su funcionalidad original pero con diseño moderno.
- Para exportar a PDF/XLSX o enviar email, los módulos existentes funcionan con la nueva estructura visual.
- El sistema de logging registra IP, ubicación geográfica, navegador y SO de cada acceso.

## Plantillas Modernizadas

### Formularios
- `formulario_generico.html`: Formulario base moderno
- `formulario_rpc.html`: Registro Público Concursal
- `doc9_form.html`: Documento 9 con JavaScript
- `crear_usuario.html`: Creación de usuarios
- `datos_procedimiento.html`: Datos de procedimiento
- `gestion_derechos_solicitante.html`: Datos del solicitante

### Paneles y Administración
- `menu.html`: Menú principal responsivo con opciones por rol
- `admin_usuarios.html`: Gestión de usuarios (solo admin)
- `admin_bancos.html`: Gestión de bancos (solo admin)
- `admin_doc9.html`: Administración Doc. 9 (solo admin)
- `admin_logs.html`: Log de accesos (solo admin)
- `login.html`: Login moderno

### Páginas de Información
- `bienvenida.html`: Página de bienvenida
- `consulta.html`: Zona de consulta
- `derechos_rgpd.html`: Derechos RGPD
- `documento9.html`: Documento 9

### Gestión de Errores y PDFs
- `error.html`: Página de error
- `gestion_derechos_error.html`: Error en gestión de derechos
- `gestion_derechos_enviar_pdf.html`: Envío de PDF
- `gestion_derechos_descarga_pdf.html`: Descarga de PDF
- `gestion_derechos_opcion_pdf.html`: Opciones de PDF
- `gestion_derechos_step1.html`: Paso 1 de gestión

## Nuevas Funcionalidades

### Sistema de Logging
- Registro automático de todos los intentos de acceso
- Información detallada: IP, ubicación geográfica, navegador, SO
- Estadísticas de accesos exitosos vs fallidos
- Exportación de logs para análisis

### Gestión de Usuarios
- Creación de usuarios con diferentes roles
- Configuración específica para lectores (formularios permitidos, expiración)
- Edición y eliminación de usuarios
- Control de estado activo/inactivo

### Gestión de Bancos
- Base de datos de bancos para autocompletado
- Información completa: dirección, localidad, provincia, CCAA
- CRUD completo para administradores

### Configuración Doc. 9
- Tipos de deuda configurables
- Opciones de cuotas y garantías personalizables
- Estadísticas de uso
- Acciones administrativas (exportar, respaldar, limpiar)
