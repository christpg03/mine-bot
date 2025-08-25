import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler


logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for the /start command
    Sends a welcome message to the user
    """
    if not update.effective_user or not update.message:
        return

    user = update.effective_user
    logger.info(
        f"User {user.id} ({user.username or 'Unknown'}) executed /start command"
    )

    welcome_message = f"""🤖 **Redmine Bot - Integración Telegram & Redmine**

¡Hola {user.first_name or 'there'}! 👋

Este bot te ayuda a integrar tus grupos de Telegram con proyectos de Redmine, facilitando la gestión de dailies y el registro automático de tiempo.

📋 **COMANDOS DISPONIBLES:**

**🔐 Chat Privado:**
• `/token TU_TOKEN` - Configurar token de Redmine API (seguro)
• `/projects` - Listar tus proyectos de Redmine
• `/teams` - Mostrar equipos que has creado

**👥 Solo en Grupos:**
• `/team ID_PROYECTO NOMBRE` - Vincular grupo a proyecto Redmine (solo admins)
• `/team_delete` - Desvincular grupo del proyecto (solo creador)
• `/daily @user1 @user2` - Registrar daily en Redmine con participantes

**🎥 FUNCIONES AUTOMÁTICAS:**
• **Detección de videollamadas** - Rastrea inicio/fin automáticamente
• **Registro de tiempo** - Auto-registra tiempo para usuarios con token
• **Creación de dailies** - Crea tareas en Redmine para reuniones

**🚀 PRIMEROS PASOS:**
1. Envíame tu token de Redmine con `/token TU_TOKEN` (solo en chat privado)
2. Ve a tu grupo y vincúlalo con `/team ID_PROYECTO NOMBRE_PROYECTO`
3. ¡Listo! Ahora puedes usar `/daily` después de tus reuniones

**💡 CONSEJOS:**
• Usa `/projects` para ver IDs de tus proyectos
• El bot detecta videollamadas automáticamente
• Solo admins del grupo pueden crear/eliminar vínculos
• Tu token se almacena de forma segura y encriptada

¿Necesitas ayuda? Usa los comandos para empezar 🚀"""

    await update.message.reply_text(welcome_message, parse_mode="Markdown")


def get_start_handler():
    """
    Returns the configured handler for the /start command
    """
    return CommandHandler("start", start_command)
