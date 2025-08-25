import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ChatType

from app.database.database import DatabaseSession
from app.database.services import TeamService

logger = logging.getLogger(__name__)


async def teams_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for the /teams command
    Shows all teams created by the user
    Only works in private chats
    """
    if not update.effective_user or not update.message:
        return

    # Check if the command is being used in a private chat
    if update.message.chat.type != ChatType.PRIVATE:
        await update.message.reply_text(
            "🔒 This command can only be used in private chats."
        )
        return

    user = update.effective_user
    loading_message = None

    try:
        # Send "loading" message
        loading_message = await update.message.reply_text("🔄 Loading your teams...")

        # Get teams created by the user and format the response
        with DatabaseSession() as db:
            teams = TeamService.get_by_creator(db, user.id)

            if not teams:
                await loading_message.edit_text(
                    "📋 You haven't created any teams yet.\n\n"
                    "Create a team by using `/team PROJECT_ID PROJECT_NAME` in a group chat.",
                    parse_mode="Markdown",
                )
                return

            # Format teams list within the session context
            teams_text = "👥 Your Teams:\n\n"

            for team in teams:
                teams_text += f"🏗️ {team.team_name}\n"
                teams_text += f"   🆔 Project ID: {team.redmine_project_id}\n"
                teams_text += f"   🔗 Project Key: {team.redmine_project_code}\n"
                teams_text += (
                    f"   📅 Created: {team.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                )

            # Add footer
            teams_text += f"📊 Total: {len(teams)} teams"

        # Update the loading message with results (outside session is fine for this)
        await loading_message.edit_text(teams_text)

        logger.info(f"Teams list sent to user {user.id} ({user.username or 'Unknown'})")

    except Exception as e:
        logger.error(f"Error processing teams command for user {user.id}: {e}")
        try:
            if loading_message:
                await loading_message.edit_text(
                    "❌ An error occurred while retrieving your teams. Please try again later."
                )
            else:
                await update.message.reply_text(
                    "❌ An error occurred while retrieving your teams. Please try again later."
                )
        except Exception as edit_error:
            logger.error(f"Error editing message: {edit_error}")
            await update.message.reply_text(
                "❌ An error occurred while retrieving your teams. Please try again later."
            )


def get_teams_handler():
    """
    Returns the configured handler for the /teams command
    """
    return CommandHandler("teams", teams_command)
