"""
Database models for the Redmine bot.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    BigInteger,
    Boolean,
    JSON,
)
from sqlalchemy.sql import func
from app.database.database import Base
from app.utils.crypto import CryptoManager
import logging

logger = logging.getLogger(__name__)


class User(Base):
    """
    Model for bot users.
    Stores information of Telegram users linked with Redmine tokens.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True, index=True)
    encrypted_redmine_token = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)

    def __init__(
        self,
        telegram_id,
        username=None,
        redmine_token=None,
    ):
        self.telegram_id = telegram_id
        self.username = username

        if redmine_token:
            self.set_redmine_token(redmine_token)

    def set_redmine_token(self, token: str) -> bool:
        """
        Encrypts and saves the Redmine token.

        Args:
            token (str): Redmine token in plain text

        Returns:
            bool: True if saved correctly, False on error
        """
        try:
            crypto = CryptoManager()
            self.encrypted_redmine_token = crypto.encrypt(token).decode("utf-8")
            logger.info(f"Token encrypted for user {self.telegram_id}")
            return True
        except Exception as e:
            logger.error(f"Error encrypting token for user {self.telegram_id}: {e}")
            return False

    def get_redmine_token(self) -> str | None:
        """
        Decrypts and returns the Redmine token.

        Returns:
            str | None: Redmine token in plain text or None if error
        """

        try:
            crypto = CryptoManager()
            token = crypto.decrypt(self.encrypted_redmine_token.encode("utf-8"))
            return token
        except Exception as e:
            logger.error(f"Error decrypting token for user {self.telegram_id}: {e}")
            return None

    def has_redmine_token(self) -> bool:
        """
        Checks if the user has a configured Redmine token.

        Returns:
            bool: True if has token, False otherwise
        """
        return self.encrypted_redmine_token is not None

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username}, has_token={self.has_redmine_token()})>"


class Team(Base):
    """
    Model for bot teams.
    Stores information of teams that link Telegram groups with Redmine projects.
    """

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    telegram_group_id = Column(BigInteger, unique=True, nullable=False, index=True)
    redmine_project_code = Column(String(100), nullable=False, index=True)
    redmine_project_id = Column(Integer, nullable=False, index=True)
    team_name = Column(String(255), nullable=False)
    created_by_user_id = Column(
        BigInteger, nullable=False, index=True
    )  # Telegram user ID of creator

    # Audit fields
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)

    def __init__(
        self,
        telegram_group_id,
        redmine_project_code,
        redmine_project_id,
        team_name,
        created_by_user_id,
    ):
        self.telegram_group_id = telegram_group_id
        self.redmine_project_code = redmine_project_code
        self.redmine_project_id = redmine_project_id
        self.team_name = team_name
        self.created_by_user_id = created_by_user_id

    def __repr__(self):
        return f"<Team(id={self.id}, name={self.team_name}, group_id={self.telegram_group_id}, project={self.redmine_project_code})>"


class Daily(Base):
    """
    Model for daily meetings.
    Stores information of daily meetings for teams.
    """

    __tablename__ = "dailys"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    team_id = Column(Integer, nullable=False, index=True)  # Foreign key to teams table
    telegram_group_id = Column(
        BigInteger, nullable=False, index=True
    )  # Telegram group ID
    start_time = Column(DateTime(timezone=True), nullable=False)  # Start time of daily
    end_time = Column(
        DateTime(timezone=True), nullable=True
    )  # End time of daily (nullable)
    registered_in_redmine = Column(
        Boolean, default=False, nullable=False
    )  # Registered in Redmine
    participants_ids = Column(JSON, nullable=True)  # JSON array of Telegram user IDs

    # Audit fields
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __init__(
        self,
        team_id,
        telegram_group_id,
        start_time,
        participants_ids=None,
    ):
        self.team_id = team_id
        self.telegram_group_id = telegram_group_id
        self.start_time = start_time
        self.participants_ids = participants_ids or []

    def set_participants(self, participants_list: list[int]) -> None:
        """
        Sets the complete list of participants.

        Args:
            participants_list (list[int]): List of Telegram user IDs
        """
        self.participants_ids = participants_list

    def get_participants(self) -> list[int]:
        """
        Gets the list of participants.

        Returns:
            list[int]: List of Telegram user IDs
        """
        # Type: ignore is needed due to SQLAlchemy JSON column typing
        return self.participants_ids or []  # type: ignore

    def finish_daily(self, end_datetime=None) -> None:
        """
        Marks the daily as finished.

        Args:
            end_datetime (datetime, optional): End time. If None, uses current time.
        """
        from datetime import datetime

        self.end_time = end_datetime or datetime.now()

    def mark_registered_in_redmine(self) -> None:
        """
        Marks the daily as registered in Redmine.
        """
        self.registered_in_redmine = True

    def __repr__(self):
        participants_count = len(self.get_participants())
        return f"<Daily(id={self.id}, team_id={self.team_id}, group_id={self.telegram_group_id}, start_time={self.start_time}, end_time={self.end_time}, participants={participants_count})>"
