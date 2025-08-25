import logging
from datetime import datetime
from typing import Any
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from telegram.constants import ChatType

from app.database.database import DatabaseSession
from app.database.services import TeamService, DailyService, UserService
from app.services.redmine_service import RedmineService
from app.config import settings

logger = logging.getLogger(__name__)


async def videochat_started_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handler for when a video chat is started in a group.
    Creates a daily record and sends a notification message.
    """
    if not update.message or not update.effective_chat:
        return

    # Only handle group chats
    if update.message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return

    group_id = update.message.chat.id
    start_time = datetime.now()

    try:
        # Check if this group has a team configured
        with DatabaseSession() as db:
            team = TeamService.get_by_telegram_group_id(db, group_id)

            if not team:
                # No team configured for this group, ignore the video chat
                logger.info(f"Video chat started in unconfigured group {group_id}")
                return

            # Check if there's already an active daily for this group
            active_daily = DailyService.get_active_daily_by_group(db, group_id)

            if active_daily:
                # There's already an active daily, ignore this video chat start
                logger.info(
                    f"Video chat started but there's already an active daily for group {group_id}"
                )
                return

            # Create new daily record
            daily = DailyService.create(
                db=db,
                team_id=team.id,  # type: ignore
                telegram_group_id=group_id,
                start_time=start_time,
                participants_ids=[],  # Will be updated as participants join
            )

            logger.info(
                f"Daily created for team {team.team_name} (ID: {daily.id}) at {start_time}"
            )

        # Send notification message
        message_text = """🎥 Video chat iniciado

⏱️ Rastreando duración automáticamente...
👥 Detectando participantes invitados...

Se mostrará un resumen cuando termine el videochat."""

        await update.message.reply_text(message_text)

        logger.info(f"Video chat start notification sent to group {group_id}")

    except Exception as e:
        logger.error(f"Error handling video chat start for group {group_id}: {e}")


async def videochat_ended_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handler for when a video chat ends in a group.
    Finishes the daily record, creates a Redmine task, logs time for participants,
    and sends a summary message.
    """
    if not update.message or not update.effective_chat:
        return

    # Only handle group chats
    if update.message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return

    group_id = update.message.chat.id
    end_time = datetime.now()

    try:
        with DatabaseSession() as db:
            # Get the active daily for this group
            active_daily = DailyService.get_active_daily_by_group(db, group_id)

            if not active_daily:
                # No active daily found, ignore
                logger.info(
                    f"Video chat ended but no active daily found for group {group_id}"
                )
                return

            # Get team information
            team = TeamService.get_by_id(db, active_daily.team_id)  # type: ignore
            if not team:
                logger.error(f"Team not found for daily {active_daily.id}")
                return

            # Finish the daily
            finished_daily = DailyService.finish_daily(db, active_daily.id, end_time)  # type: ignore
            if not finished_daily:
                logger.error(f"Failed to finish daily {active_daily.id}")
                return

            # Calculate duration in hours
            duration = end_time - finished_daily.start_time  # type: ignore
            duration_hours = duration.total_seconds() / 3600

            logger.info(
                f"Video chat ended for group {group_id}. Duration: {duration_hours:.2f} hours"
            )

            # Send notification message about the ended videochat
            await _send_videochat_ended_notification(
                update=update,
                duration_hours=duration_hours,
            )

    except Exception as e:
        logger.error(f"Error handling video chat end for group {group_id}: {e}")


async def _send_videochat_ended_notification(
    update: Update, duration_hours: float
) -> None:
    """
    Send a notification message about the ended video chat with daily command instruction.
    """
    # Format duration
    hours = int(duration_hours)
    minutes = int((duration_hours - hours) * 60)
    duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

    message = f"""🎥 Video chat finalizado

⏱️ Duración: {duration_str}

💡 Si este videochat fue una daily, usa el comando:
/daily @participante1 @participante2 @participante3

Esto creará la daily en Redmine y logueará el tiempo automáticamente para todos los participantes que tengan su token configurado."""

    try:
        if update.message:
            await update.message.reply_text(message)
            logger.info(
                f"Video chat ended notification sent to group {update.message.chat.id}"
            )
    except Exception as e:
        logger.error(f"Error sending video chat ended notification: {e}")


async def _send_no_token_message(update: Update) -> None:
    """
    Send a message indicating that the user needs to configure their Redmine token.
    """
    message = """❌ No se pudo crear la daily en Redmine

⚠️ El usuario que finalizó el videochat no tiene configurado su token de Redmine.

Usa /token <tu_token> para configurar tu token de Redmine y poder crear dailies automáticamente."""

    try:
        if update.message:
            await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error sending no token message: {e}")


async def _send_redmine_error_message(update: Update) -> None:
    """
    Send a message indicating that there was an error creating the Redmine task.
    """
    message = """❌ Error al crear la daily en Redmine

Hubo un problema al crear la tarea en Redmine. Verifica:
- Que tu token de Redmine sea válido
- Que tengas permisos en el proyecto
- Que el proyecto esté configurado correctamente"""

    try:
        if update.message:
            await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error sending Redmine error message: {e}")


async def _send_videochat_success_message(
    update: Update,
    duration_hours: float,
    redmine_task_url: str,
    logged_users: list[tuple[int, Any]],
    failed_users: list[tuple[int, Any]],
    participants_without_token: list[tuple[int, Any]],
) -> None:
    """
    Send a success message about the ended video chat.
    """
    # Format duration
    hours = int(duration_hours)
    minutes = int((duration_hours - hours) * 60)
    duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

    # Build message
    message_parts = [
        "🎥 Video chat finalizado",
        f"⏱️ Duración: {duration_str}",
        "",
        "✅ Daily creada en Redmine:",
        redmine_task_url,
        "",
    ]

    # Time logging summary
    if logged_users:
        message_parts.append(
            f"⏰ Tiempo logueado para {len(logged_users)} participante(s)"
        )

    if failed_users:
        message_parts.append(
            f"⚠️ Error al loguear tiempo para {len(failed_users)} participante(s)"
        )

    # Participants without token
    if participants_without_token:
        message_parts.extend(
            [
                "",
                "⚠️ Los siguientes participantes deben loguear tiempo manualmente:",
            ]
        )

        # Create mentions for users without token
        mentions = []
        for participant_id, participant_obj in participants_without_token:
            if (
                participant_obj
                and hasattr(participant_obj, "username")
                and participant_obj.username
            ):
                mentions.append(f"@{participant_obj.username}")
            else:
                mentions.append(
                    f"[{participant_obj.first_name if participant_obj and participant_obj.first_name else f'Usuario {participant_id}'}]"
                )

        if mentions:
            message_parts.append(" ".join(mentions))
            message_parts.extend(
                [
                    "",
                    "Usa /token <tu_token> para configurar tu token y automatizar el proceso",
                ]
            )

    message_text = "\n".join(message_parts)

    try:
        if update.message:
            await update.message.reply_text(message_text, disable_web_page_preview=True)
            logger.info(
                f"Video chat success message sent to group {update.message.chat.id}"
            )
    except Exception as e:
        logger.error(f"Error sending video chat success message: {e}")


async def _send_videochat_summary(
    update: Update,
    duration_hours: float,
    redmine_task_created: bool,
    redmine_task_url: str | None,
    logged_users: list[int],
    failed_users: list[int],
    participants_without_token: list[int],
) -> None:
    """
    Send a summary message about the ended video chat.
    """
    # Format duration
    hours = int(duration_hours)
    minutes = int((duration_hours - hours) * 60)
    duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

    # Build message
    message_parts = ["🎥 Video chat finalizado", f"⏱️ Duración: {duration_str}", ""]

    if redmine_task_created and redmine_task_url:
        message_parts.extend(["✅ Daily creada en Redmine:", redmine_task_url, ""])

        if logged_users:
            message_parts.append(
                f"⏰ Tiempo logueado para {len(logged_users)} participante(s)"
            )

        if failed_users:
            message_parts.append(
                f"⚠️ Error al loguear tiempo para {len(failed_users)} participante(s)"
            )

        if participants_without_token:
            message_parts.extend(
                [
                    "",
                    "⚠️ Los siguientes participantes necesitan configurar su token de Redmine:",
                ]
            )

            # Mention users without token
            mentions = []
            for user_id in participants_without_token:
                mentions.append(f"@{user_id}")  # This will be a basic mention

            if mentions:
                message_parts.append(" ".join(mentions))
                message_parts.extend(
                    ["", "Usa /token <tu_token> para configurar tu token de Redmine"]
                )
    else:
        message_parts.extend(
            [
                "❌ No se pudo crear la daily en Redmine",
                "Verifica que al menos un participante tenga token configurado",
            ]
        )

    message_text = "\n".join(message_parts)

    try:
        if update.message:
            await update.message.reply_text(message_text, disable_web_page_preview=True)
            logger.info(f"Video chat summary sent to group {update.message.chat.id}")
    except Exception as e:
        logger.error(f"Error sending video chat summary: {e}")


def get_videochat_handlers():
    """
    Returns the configured handlers for video chat events.
    """
    return [
        MessageHandler(
            filters.StatusUpdate.VIDEO_CHAT_STARTED, videochat_started_handler
        ),
        MessageHandler(filters.StatusUpdate.VIDEO_CHAT_ENDED, videochat_ended_handler),
    ]
