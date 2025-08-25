import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ChatType

from app.database.database import DatabaseSession
from app.database.services import UserService, TeamService

logger = logging.getLogger(__name__)


async def team_delete_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handler for the /team-delete command
    Deletes the team association for the current group
    Only works in group chats and only the creator can delete
    """
    if not update.effective_user or not update.message:
        return

    # Check if the command is being used in a group chat
    if update.message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await update.message.reply_text(
            "🔒 This command can only be used in group chats."
        )
        return

    user = update.effective_user
    group_id = update.message.chat.id
    loading_message = None

    # Check if user is admin of the group
    try:
        chat_member = await context.bot.get_chat_member(group_id, user.id)
        if chat_member.status not in ["administrator", "creator"]:
            await update.message.reply_text(
                "❌ Only group administrators can delete team associations."
            )
            return
    except Exception as e:
        logger.error(f"Error checking admin status for user {user.id}: {e}")
        await update.message.reply_text(
            "❌ Unable to verify your admin status. Please try again."
        )
        return

    try:
        # Send "loading" message
        loading_message = await update.message.reply_text(
            "🔄 Processing team deletion..."
        )

        # Check if user has a Redmine token (authentication)
        with DatabaseSession() as db:
            db_user = UserService.get_by_telegram_id(db, user.id)

            if not db_user or not db_user.has_redmine_token():
                await loading_message.edit_text(
                    "❌ You need to configure your Redmine token first.\n\n"
                    "Use `/token YOUR_REDMINE_TOKEN` in a private chat to set up your token.",
                    parse_mode="Markdown",
                )
                return

            # Check if there's a team associated with this group
            existing_team = TeamService.get_by_telegram_group_id(db, group_id)

            if not existing_team:
                await loading_message.edit_text(
                    "❌ This group is not associated with any project.\n\n"
                    "Use `/team PROJECT_ID PROJECT_NAME` to create a team association first."
                )
                return

            # Check if the user is the creator of the team
            team_creator_id = getattr(existing_team, "created_by_user_id", None)
            if team_creator_id != user.id:
                await loading_message.edit_text(
                    "❌ Only the team creator can delete the team association.\n\n"
                    f"This team was created by a different user."
                )
                return

            # Delete the team association
            success = TeamService.delete_by_group_and_creator(db, group_id, user.id)

            if success:
                await loading_message.edit_text(
                    f"✅ Team association deleted successfully!\n\n"
                    f"🏗️ Team: {existing_team.team_name}\n"
                    f"🆔 Project ID: {existing_team.redmine_project_id}\n"
                    f"🔗 Project Key: {existing_team.redmine_project_code}\n\n"
                    f"This group is no longer linked to the Redmine project."
                )

                logger.info(
                    f"Team deleted by user {user.id} ({user.username or 'Unknown'}) "
                    f"for group {group_id} with project {existing_team.redmine_project_id}"
                )
            else:
                await loading_message.edit_text(
                    "❌ Failed to delete team association. Please try again."
                )

    except Exception as e:
        logger.error(f"Error processing team-delete command for user {user.id}: {e}")
        try:
            if loading_message:
                await loading_message.edit_text(
                    "❌ An error occurred while deleting the team. Please try again later."
                )
            else:
                await update.message.reply_text(
                    "❌ An error occurred while deleting the team. Please try again later."
                )
        except Exception as edit_error:
            logger.error(f"Error editing message: {edit_error}")


def get_team_delete_handler():
    """
    Returns the configured handler for the /team_delete command
    """
    return CommandHandler("team_delete", team_delete_command)
