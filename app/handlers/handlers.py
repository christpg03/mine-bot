from telegram.ext import Application

from .start_handler import get_start_handler
from .token_handler import get_token_handler
from .projects_handler import get_projects_handler
from .team_handler import get_team_handler
from .teams_handler import get_teams_handler
from .team_delete_handler import get_team_delete_handler
from .videochat_handler import get_videochat_handlers
from .daily_handler import get_daily_handler


def setup_handlers(app: Application) -> None:
    """
    Sets up all bot handlers for the Redmine Telegram Bot

    This bot provides integration between Telegram groups and Redmine projects,
    allowing users to manage their daily meetings, track video chat sessions,
    and automatically log time entries in Redmine.

    Commands Available:
    ==================

    PUBLIC COMMANDS (any chat):
    - /start: Welcome message and commands overview

    PRIVATE CHAT ONLY:
    - /token YOUR_TOKEN: Configure Redmine API token (secure)
    - /projects: List all accessible Redmine projects
    - /teams: Show teams created by the user

    GROUP CHAT ONLY:
    - /team PROJECT_ID PROJECT_NAME: Link group to Redmine project (admins only)
    - /team_delete: Unlink group from project (creator only)
    - /daily @user1 @user2 @user3: Register daily meeting in Redmine

    AUTOMATIC FEATURES:
    - Video chat tracking: Automatically detects video chat start/end
    - Time logging: Auto-logs time for users with configured tokens
    - Daily creation: Creates Redmine tasks for daily meetings

    Args:
        app: Telegram application instance
    """

    # CORE COMMAND HANDLERS
    # =====================

    # /start - Welcome and help command (works in all chats)
    app.add_handler(get_start_handler())

    # /token - Secure token configuration (private chats only)
    app.add_handler(get_token_handler())

    # /projects - List user's Redmine projects (private chats only)
    app.add_handler(get_projects_handler())

    # TEAM MANAGEMENT HANDLERS
    # ========================

    # /team - Create team association between group and Redmine project (group admins only)
    app.add_handler(get_team_handler())

    # /teams - List teams created by user (private chats only)
    app.add_handler(get_teams_handler())

    # /team_delete - Delete team association (group admins, creator only)
    app.add_handler(get_team_delete_handler())

    # DAILY MEETING HANDLERS
    # ======================

    # /daily - Register daily meeting and log time for participants (groups only)
    app.add_handler(get_daily_handler())

    # AUTOMATIC EVENT HANDLERS
    # =========================

    # Video chat event handlers (automatic tracking)
    # - Detects when video chats start/end in configured groups
    # - Creates daily records and tracks duration
    # - Provides instructions for manual daily registration
    for handler in get_videochat_handlers():
        app.add_handler(handler)

    # FUTURE HANDLERS (planned features)
    # ==================================
    # app.add_handler(get_help_handler())           # Detailed help command
    # app.add_handler(get_tasks_handler())          # List Redmine tasks
    # app.add_handler(get_time_entries_handler())   # View time entries
    # app.add_handler(get_settings_handler())       # User settings management
