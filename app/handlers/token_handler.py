import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ChatType

from app.database.database import DatabaseSession
from app.database.services import UserService

logger = logging.getLogger(__name__)


async def token_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for the /token command
    Allows users to set their Redmine API token in private chats only
    Usage: /token YOUR_REDMINE_TOKEN
    """
    if not update.effective_user or not update.message:
        return

    # Check if the command is being used in a private chat
    if update.message.chat.type != ChatType.PRIVATE:
        await update.message.reply_text(
            "🔒 This command can only be used in private chats for security reasons."
        )
        return

    user = update.effective_user
    args = context.args

    # Check if token was provided
    if not args:
        await update.message.reply_text(
            "❌ Please provide your Redmine API token.\n\n"
            "Usage: `/token YOUR_REDMINE_TOKEN`\n\n"
            "ℹ️ You can find your API token in your Redmine profile settings.",
            parse_mode="Markdown",
        )
        return

    # Extract token from arguments
    redmine_token = args[0].strip()

    if not redmine_token:
        await update.message.reply_text(
            "❌ Invalid token. Please provide a valid Redmine API token."
        )
        return

    try:
        # Save or update user token in database
        with DatabaseSession() as db:
            # Check if user exists, create if not
            existing_user = UserService.get_by_telegram_id(db, user.id)

            if existing_user:
                # Update existing user's token and username
                updated_user = UserService.update_redmine_token(
                    db, user.id, redmine_token, user.username
                )
                if updated_user:
                    logger.info(
                        f"Token updated for user {user.id} ({user.username or 'Unknown'})"
                    )
                    await update.message.reply_text(
                        "✅ Your Redmine token has been updated successfully!\n\n"
                        "🔐 Your token is stored securely and encrypted."
                    )
                else:
                    await update.message.reply_text(
                        "❌ Failed to update your token. Please try again."
                    )
            else:
                # Create new user with token and username
                new_user = UserService.create(db, user.id, user.username, redmine_token)
                if new_user and new_user.has_redmine_token():
                    logger.info(
                        f"New user created with token: {user.id} ({user.username or 'Unknown'})"
                    )
                    await update.message.reply_text(
                        "✅ Your Redmine token has been saved successfully!\n\n"
                        "🔐 Your token is stored securely and encrypted.\n"
                        "🎉 You can now use all bot features!"
                    )
                else:
                    await update.message.reply_text(
                        "❌ Failed to save your token. Please try again."
                    )

    except Exception as e:
        logger.error(f"Error processing token for user {user.id}: {e}")
        await update.message.reply_text(
            "❌ An error occurred while processing your token. Please try again later."
        )

    # Delete the message containing the token for security
    try:
        await update.message.delete()
        logger.info(f"Token message deleted for security (user: {user.id})")
    except Exception as e:
        logger.warning(f"Could not delete token message for user {user.id}: {e}")


def get_token_handler():
    """
    Returns the configured handler for the /token command
    """
    return CommandHandler("token", token_command)
