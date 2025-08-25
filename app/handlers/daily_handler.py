import logging
import re
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ChatType

from app.database.database import DatabaseSession
from app.database.services import UserService, TeamService, DailyService
from app.services.redmine_service import RedmineService
from app.config import settings

logger = logging.getLogger(__name__)


def escape_markdown(text: str) -> str:
    """
    Escape special characters for Markdown formatting

    Args:
        text (str): Text to escape

    Returns:
        str: Escaped text safe for Markdown
    """
    if not text:
        return ""

    # Escape special Markdown characters
    special_chars = [
        "_",
        "*",
        "(",
        ")",
        "~",
        "`",
        ">",
        "#",
        "+",
        "=",
        "|",
        "{",
        "}",
        ".",
        "!",
    ]
    escaped_text = str(text)
    for char in special_chars:
        escaped_text = escaped_text.replace(char, f"\\{char}")
    return escaped_text


async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for the /daily command
    Creates a daily task and logs time for participants
    Only works in group chats
    Usage: /daily @user1 @user2 @user3...
    """
    if not update.effective_user or not update.message:
        return

    # Check if the command is being used in a group chat
    if update.message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await update.message.reply_text("🔒 Este comando solo puede usarse en grupos.")
        return

    user = update.effective_user
    args = context.args or []
    loading_message = None

    # Check if any mentions were provided
    if not args:
        await update.message.reply_text(
            "❌ Debes mencionar a los usuarios que participaron en la daily.\n\n"
            "Uso: `/daily @usuario1 @usuario2 @usuario3`\n\n"
            "Ejemplo: `/daily @juan @maria @carlos`",
            parse_mode="Markdown",
        )
        return

    # Extract mentions from arguments
    mentioned_usernames = []
    for arg in args:
        if arg.startswith("@"):
            username = arg[1:]  # Remove @ symbol
            if username:
                mentioned_usernames.append(username)

    if not mentioned_usernames:
        await update.message.reply_text(
            "❌ No se encontraron menciones válidas.\n\n"
            "Uso: `/daily @usuario1 @usuario2 @usuario3`",
            parse_mode="Markdown",
        )
        return

    group_id = update.message.chat.id

    try:
        loading_message = await update.message.reply_text("🔄 Validando información...")

        with DatabaseSession() as db:
            # Check if the group has a team configuration
            team = TeamService.get_by_telegram_group_id(db, group_id)
            if not team:
                await loading_message.edit_text(
                    "❌ Este grupo no está asociado a ningún proyecto de Redmine.\n\n"
                    "Usa `/team PROJECT_ID PROJECT_NAME` para configurar el equipo primero.",
                    parse_mode="Markdown",
                )
                return

            # Check if user who issued the command has a Redmine token
            command_user = UserService.get_by_telegram_id(db, user.id)
            if not command_user or not command_user.has_redmine_token():
                await loading_message.edit_text(
                    "❌ Necesitas configurar tu token de Redmine primero.\n\n"
                    "Usa `/token TU_TOKEN_REDMINE` en un chat privado para configurar tu token.",
                    parse_mode="Markdown",
                )
                return

            # Get the latest unregistered daily for this group
            latest_daily = DailyService.get_latest_unregistered_daily_by_group(
                db, group_id
            )

            if not latest_daily:
                await loading_message.edit_text(
                    "❌ No hay ninguna daily pendiente de registrar en Redmine.\n\n"
                    "Todas las dailies de este grupo ya han sido registradas o no se ha iniciado ninguna daily."
                )
                return

            # Check if the daily has ended
            if latest_daily.end_time is None:
                await loading_message.edit_text(
                    "❌ La daily actual aún no ha terminado.\n\n"
                    "Espera a que termine para poder registrarla en Redmine."
                )
                return

            # Check if enough time has passed since the daily ended (30 minutes max)
            time_since_ended = datetime.now() - latest_daily.end_time
            if time_since_ended.total_seconds() > 30 * 60:  # 30 minutes in seconds
                await loading_message.edit_text(
                    f"❌ Han pasado más de 30 minutos desde que terminó la última daily ({latest_daily.end_time.strftime('%H:%M:%S')}).\n\n"
                    "No se puede registrar en Redmine."
                )
                return

            # Get the command user's Redmine token
            redmine_token = command_user.get_redmine_token()
            if not redmine_token:
                await loading_message.edit_text(
                    "❌ Error al obtener tu token de Redmine. Configúralo nuevamente con `/token`.",
                    parse_mode="Markdown",
                )
                return

            # Test Redmine connection
            redmine_service = RedmineService(redmine_token)
            if not redmine_service.test_connection():
                await loading_message.edit_text(
                    "❌ No se pudo conectar a Redmine. Verifica tu token."
                )
                return

            await loading_message.edit_text("🔄 Creando tarea daily en Redmine...")

            # Create daily task in Redmine
            daily_task = redmine_service.create_daily_task(
                project_id=team.redmine_project_id,  # type: ignore
                team_name=team.team_name,  # type: ignore
                daily_date=datetime.now(),
            )

            if not daily_task:
                await loading_message.edit_text(
                    "❌ Error al crear la tarea daily en Redmine."
                )
                return

            await loading_message.edit_text(
                "🔄 Buscando usuarios y registrando tiempo..."
            )

            # Calculate daily duration in hours
            # At this point we know latest_daily exists and has both start_time and end_time
            duration_delta = latest_daily.end_time - latest_daily.start_time
            daily_duration_hours = (
                duration_delta.total_seconds() / 3600
            )  # Convert to hours

            # Format duration for display
            total_minutes = int(duration_delta.total_seconds() / 60)
            if total_minutes >= 60:
                hours = total_minutes // 60
                minutes = total_minutes % 60
                duration_text = f"{hours}h {minutes}min" if minutes > 0 else f"{hours}h"
            else:
                duration_text = f"{total_minutes} min"

            # Find users by username and collect results
            found_users = []
            not_found_users = []
            users_without_token = []
            successful_logs = []
            failed_logs = []

            for username in mentioned_usernames:
                db_user = UserService.get_by_username(db, username)

                if not db_user:
                    not_found_users.append(username)
                    continue

                found_users.append((username, db_user))

                if not db_user.has_redmine_token():
                    users_without_token.append(username)
                    continue

                # Try to log time for this user
                user_token = db_user.get_redmine_token()
                if not user_token:
                    users_without_token.append(username)
                    continue

                user_redmine_service = RedmineService(user_token)

                # Log the actual daily duration for each participant
                time_entry = user_redmine_service.log_daily(
                    daily_task["id"], daily_duration_hours
                )

                if time_entry:
                    successful_logs.append(username)
                else:
                    failed_logs.append(username)

            # Mark the daily as registered in Redmine
            DailyService.mark_registered_in_redmine(db, latest_daily.id)  # type: ignore

            # Prepare response message
            response_parts = [
                f"✅ **Daily registrada exitosamente**",
                f"",
                f"🔗 **Enlace:** {settings.redmine_url}/issues/{daily_task['id']}",
                f"",
            ]

            if successful_logs:
                response_parts.append(f"✅ **Tiempo registrado para:**")
                for username in successful_logs:
                    response_parts.append(
                        f"   • @{escape_markdown(username)} ({escape_markdown(duration_text)})"
                    )
                response_parts.append("")

            if users_without_token:
                response_parts.append(f"⚠️ **Usuarios sin token configurado:**")
                for username in users_without_token:
                    response_parts.append(
                        f"   • @{escape_markdown(username)} (debe registrar manualmente)"
                    )
                response_parts.append("")

            if failed_logs:
                response_parts.append(f"❌ **Error registrando tiempo para:**")
                for username in failed_logs:
                    response_parts.append(f"   • @{escape_markdown(username)}")
                response_parts.append("")

            if not_found_users:
                response_parts.append(f"❓ **Usuarios no registrados:**")
                for username in not_found_users:
                    response_parts.append(f"   • @{escape_markdown(username)}")
                response_parts.append("")

            response_parts.append(
                f"👤 **Registrado por:** {escape_markdown(str(user.first_name or user.username or 'Usuario'))}"
            )

            response_message = "\n".join(response_parts)

            await loading_message.edit_text(response_message, parse_mode="Markdown")

            logger.info(
                f"Daily command executed by user {user.id} ({user.username or 'Unknown'}) "
                f"for group {group_id} with {len(mentioned_usernames)} participants. "
                f"Task ID: {daily_task['id']}"
            )

    except Exception as e:
        logger.error(f"Error processing daily command for user {user.id}: {e}")
        try:
            if loading_message:
                await loading_message.edit_text(
                    "❌ Ocurrió un error al procesar la daily. Inténtalo más tarde."
                )
            else:
                await update.message.reply_text(
                    "❌ Ocurrió un error al procesar la daily. Inténtalo más tarde."
                )
        except Exception as edit_error:
            logger.error(f"Error editing message: {edit_error}")


def get_daily_handler():
    """
    Returns the configured handler for the /daily command
    """
    return CommandHandler("daily", daily_command)
