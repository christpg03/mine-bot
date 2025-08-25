import logging
from telegram.ext import ApplicationBuilder
from app.config import settings
from app.handlers.handlers import setup_handlers
from app.database.database import init_database, check_database_connection


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def main():
    settings.validate()

    # Initialize database
    if not init_database():
        logging.error("Failed to initialize database. Exiting.")
        return

    if not check_database_connection():
        logging.error("Database connection failed. Exiting.")
        return

    # Build the application
    app = ApplicationBuilder().token(settings.bot_token).build()

    # Set up all handlers
    setup_handlers(app)

    logging.info("Bot started")

    # Run the bot with proper initialization
    try:
        app.run_polling(allowed_updates=["message", "chat_member"])
    except Exception as e:
        logging.error(f"Error running bot: {e}")


if __name__ == "__main__":
    main()
