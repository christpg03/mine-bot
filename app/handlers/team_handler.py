import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ChatType

from app.database.database import DatabaseSession
from app.database.services import UserService, TeamService
from app.services.redmine_service import RedmineService

logger = logging.getLogger(__name__)


async def team_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for the /team command
    Associates a Telegram group with a Redmine project
    Only works in group chats
    Usage: /team PROJECT_ID PROJECT_NAME
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
    args = context.args or []
    loading_message = None

    # Check if user is admin of the group
    try:
        chat_member = await context.bot.get_chat_member(update.message.chat.id, user.id)
        if chat_member.status not in ["administrator", "creator"]:
            await update.message.reply_text(
                "❌ Only group administrators can create team associations."
            )
            return
    except Exception as e:
        logger.error(f"Error checking admin status for user {user.id}: {e}")
        await update.message.reply_text(
            "❌ Unable to verify your admin status. Please try again."
        )
        return

    # Check if required arguments were provided
    if len(args) < 2:
        await update.message.reply_text(
            "❌ Please provide project ID and project name.\n\n"
            "Usage: `/team PROJECT_ID PROJECT_NAME`\n\n"
            "Example: `/team 123 My Project Name`",
            parse_mode="Markdown",
        )
        return

    try:
        project_id = int(args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Project ID must be a number.\n\n"
            "Usage: `/team PROJECT_ID PROJECT_NAME`",
            parse_mode="Markdown",
        )
        return

    # Join remaining arguments as project name
    project_name = " ".join(args[1:])

    if not project_name.strip():
        await update.message.reply_text(
            "❌ Project name cannot be empty.\n\n"
            "Usage: `/team PROJECT_ID PROJECT_NAME`",
            parse_mode="Markdown",
        )
        return

    try:
        # Check if user has a Redmine token
        with DatabaseSession() as db:
            db_user = UserService.get_by_telegram_id(db, user.id)

            if not db_user or not db_user.has_redmine_token():
                await update.message.reply_text(
                    "❌ You need to configure your Redmine token first.\n\n"
                    "Use `/token YOUR_REDMINE_TOKEN` in a private chat to set up your token.",
                    parse_mode="Markdown",
                )
                return

            # Get decrypted token
            redmine_token = db_user.get_redmine_token()
            if not redmine_token:
                await update.message.reply_text(
                    "❌ Error retrieving your Redmine token. Please set it up again with `/token`.",
                    parse_mode="Markdown",
                )
                return

        # Send "loading" message
        loading_message = await update.message.reply_text("🔄 Validating project...")

        # Validate project exists in Redmine
        redmine_service = RedmineService(redmine_token)

        if not redmine_service.test_connection():
            await loading_message.edit_text(
                "❌ Failed to connect to Redmine. Please check your token."
            )
            return

        # Get project details from Redmine
        project_data = redmine_service.get_project_by_id(project_id)
        if not project_data:
            await loading_message.edit_text(
                f"❌ Project with ID {project_id} not found or you don't have access to it."
            )
            return

        # Check if group is already associated with a project
        group_id = update.message.chat.id
        with DatabaseSession() as db:
            existing_team = TeamService.get_by_telegram_group_id(db, group_id)

            if existing_team:
                await loading_message.edit_text(
                    f"⚠️ This group is already associated with project:\n"
                    f"🏗️ {existing_team.team_name}\n"
                    f"🆔 Project ID: {existing_team.redmine_project_id}\n"
                    f"🔗 Project Key: {existing_team.redmine_project_code}"
                )
                return

            # Create new team association
            try:
                team = TeamService.create(
                    db=db,
                    telegram_group_id=group_id,
                    redmine_project_code=project_data["identifier"],
                    redmine_project_id=project_id,
                    team_name=project_name,
                    created_by_user_id=user.id,
                )

                await loading_message.edit_text(
                    f"✅ Team successfully created!\n\n"
                    f"🏗️ Team: {project_name}\n"
                    f"🆔 Project ID: {project_id}\n"
                    f"🔗 Project Key: {project_data['identifier']}\n"
                    f"👤 Created by: {user.first_name or user.username or 'Unknown'}\n\n"
                    f"This group is now linked to the Redmine project."
                )

                logger.info(
                    f"Team created by user {user.id} ({user.username or 'Unknown'}) "
                    f"for group {group_id} with project {project_id}"
                )

            except Exception as e:
                logger.error(f"Error creating team: {e}")
                await loading_message.edit_text(
                    "❌ Error creating team association. This group might already be linked to a project."
                )

    except Exception as e:
        logger.error(f"Error processing team command for user {user.id}: {e}")
        try:
            if loading_message:
                await loading_message.edit_text(
                    "❌ An error occurred while creating the team. Please try again later."
                )
            else:
                await update.message.reply_text(
                    "❌ An error occurred while creating the team. Please try again later."
                )
        except Exception as edit_error:
            logger.error(f"Error editing message: {edit_error}")


def get_team_handler():
    """
    Returns the configured handler for the /team command
    """
    return CommandHandler("team", team_command)
