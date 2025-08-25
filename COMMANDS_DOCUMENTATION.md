# 🤖 Redmine Telegram Bot - Documentación de Comandos

## 📋 Descripción General

Este bot proporciona integración completa entre grupos de Telegram y proyectos de Redmine, permitiendo:

- **Gestión automática de dailies**
- **Registro automático de tiempo**
- **Detección de videollamadas**
- **Vinculación de grupos con proyectos**
- **Seguridad y encriptación de tokens**

---

## 🔐 Comandos de Chat Privado

### `/token TU_TOKEN_REDMINE`
**Propósito:** Configurar tu token de API de Redmine de forma segura
**Ubicación:** Solo chat privado (por seguridad)
**Permisos:** Cualquier usuario

**Funcionamiento:**
- Almacena el token de forma encriptada en la base de datos
- Actualiza el username si ya existe el usuario
- Elimina automáticamente el mensaje con el token por seguridad
- Valida la conexión con Redmine

**Ejemplo:**
```
/token abc123def456ghi789
```

**Respuestas:**
- ✅ Token guardado exitosamente
- ❌ Error en el token o conexión
- 🔒 Comando solo disponible en chat privado

---

### `/projects`
**Propósito:** Listar todos los proyectos de Redmine accesibles
**Ubicación:** Solo chat privado
**Permisos:** Usuario con token configurado

**Funcionamiento:**
- Conecta a Redmine usando tu token
- Lista proyectos con ID, nombre y estado
- Muestra total de proyectos encontrados

**Ejemplo de respuesta:**
```
📋 Your Redmine Projects:

✅ Proyecto Web 🆔 ID: 123
✅ App Mobile 🆔 ID: 456
⏸️ Proyecto Pausado 🆔 ID: 789

📊 Total: 3 projects
```

---

### `/teams`
**Propósito:** Mostrar todos los equipos que has creado
**Ubicación:** Solo chat privado
**Permisos:** Cualquier usuario

**Funcionamiento:**
- Lista equipos creados por el usuario
- Muestra información del proyecto vinculado
- Incluye fecha de creación

**Ejemplo de respuesta:**
```
👥 Your Teams:

🏗️ Equipo Frontend
   🆔 Project ID: 123
   🔗 Project Key: web-frontend
   📅 Created: 2024-01-15 10:30

📊 Total: 1 teams
```

---

## 👥 Comandos de Grupo

### `/team ID_PROYECTO NOMBRE_EQUIPO`
**Propósito:** Vincular el grupo actual con un proyecto de Redmine
**Ubicación:** Solo grupos
**Permisos:** Administradores del grupo con token configurado

**Funcionamiento:**
- Valida que el usuario sea admin del grupo
- Verifica que el proyecto existe en Redmine
- Crea la asociación grupo-proyecto
- Previene múltiples vinculaciones

**Ejemplo:**
```
/team 123 Equipo Frontend Web
```

**Respuestas:**
```
✅ Team successfully created!

🏗️ Team: Equipo Frontend Web
🆔 Project ID: 123
🔗 Project Key: web-frontend
👤 Created by: Juan
```

---

### `/team_delete`
**Propósito:** Eliminar la vinculación del grupo con el proyecto
**Ubicación:** Solo grupos
**Permisos:** Administrador del grupo Y creador del equipo

**Funcionamiento:**
- Valida permisos de admin y creador
- Elimina la asociación permanentemente
- Confirma la eliminación

**Respuestas:**
```
✅ Team association deleted successfully!

🏗️ Team: Equipo Frontend Web
🆔 Project ID: 123
🔗 Project Key: web-frontend
```

---

### `/daily @usuario1 @usuario2 @usuario3`
**Propósito:** Registrar una daily meeting en Redmine con participantes
**Ubicación:** Solo grupos vinculados
**Permisos:** Usuario con token configurado

**Funcionamiento:**
- Busca la última videollamada no registrada (máximo 30 min)
- Crea tarea "Daily" en Redmine con fecha actual
- Registra tiempo automáticamente para usuarios con token
- Genera resumen completo de la operación

**Ejemplo:**
```
/daily @juan @maria @carlos
```

**Respuesta completa:**
```
✅ Daily registrada exitosamente

🔗 Enlace: https://redmine.com/issues/1234

✅ Tiempo registrado para:
   • @juan (45min)
   • @maria (45min)

⚠️ Usuarios sin token configurado:
   • @carlos (debe registrar manualmente)

👤 Registrado por: Juan
```

---

## 🎥 Funciones Automáticas

### Detección de Videollamadas

**Inicio de videollamada:**
- Detecta automáticamente cuando inicia una videollamada
- Crea registro de daily en la base de datos
- Inicia el cronómetro de duración

**Mensaje automático:**
```
🎥 Video chat iniciado

⏱️ Rastreando duración automáticamente...
👥 Detectando participantes invitados...

Se mostrará un resumen cuando termine el videochat.
```

**Final de videollamada:**
- Detecta automáticamente cuando termina
- Calcula duración total
- Proporciona instrucciones para registro

**Mensaje automático:**
```
🎥 Video chat finalizado

⏱️ Duración: 45min

💡 Si este videochat fue una daily, usa el comando:
/daily @participante1 @participante2 @participante3

Esto creará la daily en Redmine y logueará el tiempo automáticamente.
```

---

## 🔧 Arquitectura de Handlers

### Estructura de archivos:
```
app/handlers/
├── handlers.py              # Configuración principal
├── start_handler.py         # Comando /start
├── token_handler.py         # Comando /token
├── projects_handler.py      # Comando /projects
├── team_handler.py          # Comando /team
├── teams_handler.py         # Comando /teams
├── team_delete_handler.py   # Comando /team_delete
├── daily_handler.py         # Comando /daily
└── videochat_handler.py     # Eventos de videollamada
```

### Dependencias principales:
- **Database Services:** UserService, TeamService, DailyService
- **Redmine Service:** Conexión y operaciones con API
- **Crypto Utils:** Encriptación de tokens
- **Telegram API:** Manejo de eventos y mensajes

---

## 🛡️ Seguridad y Validaciones

### Seguridad de tokens:
- ✅ Almacenamiento encriptado en base de datos
- ✅ Eliminación automática de mensajes con tokens
- ✅ Validación de conexión antes de almacenar
- ✅ Solo acceso en chats privados

### Validaciones de permisos:
- ✅ Verificación de admin para comandos de grupo
- ✅ Validación de creador para eliminación de equipos
- ✅ Restricción de comandos por tipo de chat
- ✅ Verificación de existencia de proyectos

### Validaciones de datos:
- ✅ Formato correcto de mentions (@usuario)
- ✅ IDs de proyecto numéricos válidos
- ✅ Existencia de equipos antes de operaciones
- ✅ Tiempo límite para registro de dailies (30 min)

---

## 📊 Flujo de Trabajo Típico

1. **Configuración inicial:**
   ```
   Usuario → /token abc123 (privado)
   Admin → /team 123 Mi Equipo (grupo)
   ```

2. **Reunión daily:**
   ```
   Sistema → Detecta videollamada automáticamente
   Sistema → Rastrea duración
   Sistema → Notifica fin de videollamada
   Usuario → /daily @juan @maria @carlos
   Sistema → Crea tarea en Redmine + registra tiempo
   ```

3. **Gestión:**
   ```
   Usuario → /teams (ver equipos creados)
   Usuario → /projects (ver proyectos disponibles)
   Admin → /team_delete (eliminar vinculación)
   ```

---

## 🚀 Funciones Planificadas

```python
# FUTURE HANDLERS (planned features)
# app.add_handler(get_help_handler())           # Ayuda detallada
# app.add_handler(get_tasks_handler())          # Listar tareas Redmine
# app.add_handler(get_time_entries_handler())   # Ver entradas de tiempo
# app.add_handler(get_settings_handler())       # Configuración usuario
```

---

## 📞 Soporte y Mantenimiento

### Logs disponibles:
- Creación/actualización de usuarios
- Operaciones de equipos
- Registro de dailies
- Errores de conexión con Redmine
- Eventos de videollamadas

### Troubleshooting común:
1. **Token inválido:** Verificar permisos en Redmine
2. **Proyecto no encontrado:** Confirmar ID y acceso
3. **No se puede crear equipo:** Verificar que no exista ya
4. **Daily no registra:** Verificar tiempo límite (30 min)
