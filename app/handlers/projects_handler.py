import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ChatType

from app.database.database import DatabaseSession
from app.database.services import UserService
from app.services.redmine_service import RedmineService

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
        "[",
        "]",
        "(",
        ")",
        "~",
        "`",
        ">",
        "#",
        "+",
        "-",
        "=",
        "|",
        "{",
        "}",
        ".",
        "!",
    ]
    escaped_text = text
    for char in special_chars:
        escaped_text = escaped_text.replace(char, f"\\{char}")
    return escaped_text


async def projects_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for the /projects command
    Shows all Redmine projects accessible to the user
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
        # Get user from database
        with DatabaseSession() as db:
            db_user = UserService.get_by_telegram_id(db, user.id)

            if not db_user or not db_user.has_redmine_token():
                await update.message.reply_text(
                    "❌ You need to configure your Redmine token first.\n\n"
                    "Use `/token YOUR_REDMINE_TOKEN` to set up your token.",
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
        loading_message = await update.message.reply_text("🔄 Loading your projects...")

        # Connect to Redmine and get projects
        redmine_service = RedmineService(redmine_token)

        # Test connection first
        if not redmine_service.test_connection():
            await loading_message.edit_text(
                "❌ Failed to connect to Redmine. Please check your token and try again."
            )
            return

        # Get projects
        projects = redmine_service.get_projects()

        if not projects:
            await loading_message.edit_text(
                "📋 No projects found or you don't have access to any projects."
            )
            return

        # Format projects list (using plain text to avoid Markdown parsing issues)
        projects_text = "📋 Your Redmine Projects:\n\n"

        for project in projects:
            status_icon = "✅" if project.get("status", 1) == 1 else "⏸️"

            projects_text += f"{status_icon} {project['name']} 🆔 ID: {project['id']}\n"
            # projects_text += f"   "
            # projects_text += f"   🔗 Key: {project['identifier']}\n"

            # Add description if available and not too long
            # description = project.get("description", "").strip()
            # if description:
            #     # Truncate description if too long
            #     if len(description) > 100:
            #         description = description[:97] + "..."
            #     projects_text += f"   📝 {description}\n"

            projects_text += "\n"

        # Add footer
        projects_text += f"📊 Total: {len(projects)} projects"

        # Update the loading message with results (no parse_mode to avoid Markdown issues)
        await loading_message.edit_text(projects_text)

        logger.info(
            f"Projects list sent to user {user.id} ({user.username or 'Unknown'})"
        )

    except Exception as e:
        logger.error(f"Error processing projects command for user {user.id}: {e}")
        try:
            if loading_message:
                await loading_message.edit_text(
                    "❌ An error occurred while retrieving your projects. Please try again later."
                )
            else:
                await update.message.reply_text(
                    "❌ An error occurred while retrieving your projects. Please try again later."
                )
        except Exception as edit_error:
            logger.error(f"Error editing message: {edit_error}")
            await update.message.reply_text(
                "❌ An error occurred while retrieving your projects. Please try again later."
            )


def get_projects_handler():
    """
    Returns the configured handler for the /projects command
    """
    return CommandHandler("projects", projects_command)
