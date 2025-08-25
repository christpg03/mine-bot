"""
CRUD services for database operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.database.models import User, Team, Daily
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UserService:
    """
    CRUD service for User model.
    """

    @staticmethod
    def create(
        db: Session,
        telegram_id: int,
        username: str | None = None,
        redmine_token: str | None = None,
    ) -> User:
        """
        Create a new user.

        Args:
            db (Session): Database session
            telegram_id (int): Telegram user ID
            username (str, optional): Telegram username
            redmine_token (str, optional): Redmine API token

        Returns:
            User: Created user instance
        """
        try:
            user = User(
                telegram_id=telegram_id, username=username, redmine_token=redmine_token
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(
                f"User created with telegram_id: {telegram_id}, username: {username}"
            )
            return user
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user with telegram_id {telegram_id}: {e}")
            raise

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            db (Session): Database session
            user_id (int): User ID

        Returns:
            Optional[User]: User instance or None
        """
        return db.query(User).filter(User.id == user_id, User.is_active == True).first()

    @staticmethod
    def get_by_telegram_id(db: Session, telegram_id: int) -> Optional[User]:
        """
        Get user by Telegram ID.

        Args:
            db (Session): Database session
            telegram_id (int): Telegram user ID

        Returns:
            Optional[User]: User instance or None
        """
        return (
            db.query(User)
            .filter(User.telegram_id == telegram_id, User.is_active == True)
            .first()
        )

    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            db (Session): Database session
            username (str): Telegram username (without @)

        Returns:
            Optional[User]: User instance or None
        """
        return (
            db.query(User)
            .filter(User.username == username, User.is_active == True)
            .first()
        )

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all active users.

        Args:
            db (Session): Database session
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return

        Returns:
            List[User]: List of user instances
        """
        return (
            db.query(User)
            .filter(User.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def update_redmine_token(
        db: Session, telegram_id: int, redmine_token: str, username: str | None = None
    ) -> Optional[User]:
        """
        Update user's Redmine token and username.

        Args:
            db (Session): Database session
            telegram_id (int): Telegram user ID
            redmine_token (str): New Redmine API token
            username (str, optional): Telegram username to update

        Returns:
            Optional[User]: Updated user instance or None
        """
        try:
            user = UserService.get_by_telegram_id(db, telegram_id)
            if user:
                if user.set_redmine_token(redmine_token):
                    # Update username if provided
                    if username is not None:
                        user.username = username
                    db.commit()
                    db.refresh(user)
                    logger.info(
                        f"Token updated for user {telegram_id}, username: {username}"
                    )
                    return user
                else:
                    db.rollback()
                    logger.error(f"Failed to encrypt token for user {telegram_id}")
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating token for user {telegram_id}: {e}")
            raise

    @staticmethod
    def delete(db: Session, user_id: int) -> bool:
        """
        Soft delete a user (set is_active to False).

        Args:
            db (Session): Database session
            user_id (int): User ID

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            user = UserService.get_by_id(db, user_id)
            if user:
                user.is_active = False
                db.commit()
                logger.info(f"User {user_id} soft deleted")
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting user {user_id}: {e}")
            raise

    @staticmethod
    def get_or_create(
        db: Session,
        telegram_id: int,
        username: str | None = None,
        redmine_token: str | None = None,
    ) -> User:
        """
        Get existing user or create new one.

        Args:
            db (Session): Database session
            telegram_id (int): Telegram user ID
            username (str, optional): Telegram username
            redmine_token (str, optional): Redmine API token

        Returns:
            User: User instance
        """
        user = UserService.get_by_telegram_id(db, telegram_id)
        if not user:
            user = UserService.create(db, telegram_id, username, redmine_token)
        return user


class TeamService:
    """
    CRUD service for Team model.
    """

    @staticmethod
    def create(
        db: Session,
        telegram_group_id: int,
        redmine_project_code: str,
        redmine_project_id: int,
        team_name: str,
        created_by_user_id: int,
    ) -> Team:
        """
        Create a new team.

        Args:
            db (Session): Database session
            telegram_group_id (int): Telegram group ID
            redmine_project_code (str): Redmine project identifier
            redmine_project_id (int): Redmine project ID
            team_name (str): Team name
            created_by_user_id (int): Telegram user ID of creator

        Returns:
            Team: Created team instance
        """
        try:
            # First, check if there's an existing team (active or inactive) for this group
            existing_team = (
                db.query(Team)
                .filter(Team.telegram_group_id == telegram_group_id)
                .first()
            )

            if existing_team:
                # Delete the existing team completely to avoid unique constraint issues
                db.delete(existing_team)
                db.commit()
                logger.info(f"Removed existing team for group {telegram_group_id}")

            # Now create the new team
            team = Team(
                telegram_group_id=telegram_group_id,
                redmine_project_code=redmine_project_code,
                redmine_project_id=redmine_project_id,
                team_name=team_name,
                created_by_user_id=created_by_user_id,
            )
            db.add(team)
            db.commit()
            db.refresh(team)
            logger.info(f"Team created: {team_name} (group_id: {telegram_group_id})")
            return team
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating team {team_name}: {e}")
            raise

    @staticmethod
    def get_by_id(db: Session, team_id: int) -> Optional[Team]:
        """
        Get team by ID.

        Args:
            db (Session): Database session
            team_id (int): Team ID

        Returns:
            Optional[Team]: Team instance or None
        """
        return db.query(Team).filter(Team.id == team_id, Team.is_active == True).first()

    @staticmethod
    def get_by_telegram_group_id(db: Session, telegram_group_id: int) -> Optional[Team]:
        """
        Get team by Telegram group ID.

        Args:
            db (Session): Database session
            telegram_group_id (int): Telegram group ID

        Returns:
            Optional[Team]: Team instance or None
        """
        return (
            db.query(Team)
            .filter(Team.telegram_group_id == telegram_group_id, Team.is_active == True)
            .first()
        )

    @staticmethod
    def get_by_project_code(db: Session, redmine_project_code: str) -> List[Team]:
        """
        Get teams by Redmine project code.

        Args:
            db (Session): Database session
            redmine_project_code (str): Redmine project identifier

        Returns:
            List[Team]: List of team instances
        """
        return (
            db.query(Team)
            .filter(
                Team.redmine_project_code == redmine_project_code,
                Team.is_active == True,
            )
            .all()
        )

    @staticmethod
    def get_by_creator(db: Session, created_by_user_id: int) -> List[Team]:
        """
        Get teams created by a specific user.

        Args:
            db (Session): Database session
            created_by_user_id (int): Telegram user ID of creator

        Returns:
            List[Team]: List of team instances created by the user
        """
        return (
            db.query(Team)
            .filter(
                Team.created_by_user_id == created_by_user_id,
                Team.is_active == True,
            )
            .all()
        )

    @staticmethod
    def delete_by_group_and_creator(
        db: Session, telegram_group_id: int, created_by_user_id: int
    ) -> bool:
        """
        Delete a team by group ID, but only if the user is the creator.

        Args:
            db (Session): Database session
            telegram_group_id (int): Telegram group ID
            created_by_user_id (int): Telegram user ID of creator

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            team = (
                db.query(Team)
                .filter(
                    Team.telegram_group_id == telegram_group_id,
                    Team.created_by_user_id == created_by_user_id,
                    Team.is_active == True,
                )
                .first()
            )

            if team:
                # Hard delete - remove the record completely to avoid unique constraint issues
                team_id = team.id
                team_name = team.team_name
                db.delete(team)
                db.commit()
                logger.info(
                    f"Team {team_id} ({team_name}) hard deleted by creator {created_by_user_id}"
                )
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting team for group {telegram_group_id}: {e}")
            raise

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Team]:
        """
        Get all active teams.

        Args:
            db (Session): Database session
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return

        Returns:
            List[Team]: List of team instances
        """
        return (
            db.query(Team)
            .filter(Team.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def update(
        db: Session,
        team_id: int,
        team_name: str = None,
        redmine_project_code: str = None,
    ) -> Optional[Team]:
        """
        Update team information.

        Args:
            db (Session): Database session
            team_id (int): Team ID
            team_name (str, optional): New team name
            redmine_project_code (str, optional): New Redmine project code

        Returns:
            Optional[Team]: Updated team instance or None
        """
        try:
            team = TeamService.get_by_id(db, team_id)
            if team:
                if team_name is not None:
                    team.team_name = team_name
                if redmine_project_code is not None:
                    team.redmine_project_code = redmine_project_code

                db.commit()
                db.refresh(team)
                logger.info(f"Team {team_id} updated")
                return team
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating team {team_id}: {e}")
            raise

    @staticmethod
    def delete(db: Session, team_id: int) -> bool:
        """
        Soft delete a team (set is_active to False).

        Args:
            db (Session): Database session
            team_id (int): Team ID

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            team = TeamService.get_by_id(db, team_id)
            if team:
                team.is_active = False
                db.commit()
                logger.info(f"Team {team_id} soft deleted")
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting team {team_id}: {e}")
            raise

    @staticmethod
    def get_or_create(
        db: Session, telegram_group_id: int, redmine_project_code: str, team_name: str
    ) -> Team:
        """
        Get existing team or create new one.

        Args:
            db (Session): Database session
            telegram_group_id (int): Telegram group ID
            redmine_project_code (str): Redmine project identifier
            team_name (str): Team name

        Returns:
            Team: Team instance
        """
        team = TeamService.get_by_telegram_group_id(db, telegram_group_id)
        if not team:
            team = TeamService.create(
                db, telegram_group_id, redmine_project_code, team_name
            )
        return team


class DailyService:
    """
    CRUD service for Daily model.
    """

    @staticmethod
    def create(
        db: Session,
        team_id: int,
        telegram_group_id: int,
        start_time: datetime,
        participants_ids: List[int] = None,
    ) -> Daily:
        """
        Create a new daily.

        Args:
            db (Session): Database session
            team_id (int): Team ID
            telegram_group_id (int): Telegram group ID
            start_time (datetime): Start time of the daily
            participants_ids (List[int], optional): List of participant Telegram IDs

        Returns:
            Daily: Created daily instance
        """
        try:
            daily = Daily(
                team_id=team_id,
                telegram_group_id=telegram_group_id,
                start_time=start_time,
                participants_ids=participants_ids or [],
            )
            db.add(daily)
            db.commit()
            db.refresh(daily)
            logger.info(f"Daily created for team {team_id} at {start_time}")
            return daily
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating daily for team {team_id}: {e}")
            raise

    @staticmethod
    def get_by_id(db: Session, daily_id: int) -> Optional[Daily]:
        """
        Get daily by ID.

        Args:
            db (Session): Database session
            daily_id (int): Daily ID

        Returns:
            Optional[Daily]: Daily instance or None
        """
        return db.query(Daily).filter(Daily.id == daily_id).first()

    @staticmethod
    def get_active_daily_by_group(
        db: Session, telegram_group_id: int
    ) -> Optional[Daily]:
        """
        Get active daily (not finished) by Telegram group ID.

        Args:
            db (Session): Database session
            telegram_group_id (int): Telegram group ID

        Returns:
            Optional[Daily]: Active daily instance or None
        """
        return (
            db.query(Daily)
            .filter(
                Daily.telegram_group_id == telegram_group_id, Daily.end_time.is_(None)
            )
            .first()
        )

    @staticmethod
    def finish_daily(
        db: Session, daily_id: int, end_time: datetime = None
    ) -> Optional[Daily]:
        """
        Mark a daily as finished.

        Args:
            db (Session): Database session
            daily_id (int): Daily ID
            end_time (datetime, optional): End time. If None, uses current time.

        Returns:
            Optional[Daily]: Updated daily instance or None
        """
        try:
            daily = DailyService.get_by_id(db, daily_id)
            if daily:
                daily.finish_daily(end_time)
                db.commit()
                db.refresh(daily)
                logger.info(f"Daily {daily_id} finished at {daily.end_time}")
                return daily
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"Error finishing daily {daily_id}: {e}")
            raise

    @staticmethod
    def update_participants(
        db: Session, daily_id: int, participants_ids: List[int]
    ) -> Optional[Daily]:
        """
        Update participants of a daily.

        Args:
            db (Session): Database session
            daily_id (int): Daily ID
            participants_ids (List[int]): List of participant Telegram IDs

        Returns:
            Optional[Daily]: Updated daily instance or None
        """
        try:
            daily = DailyService.get_by_id(db, daily_id)
            if daily:
                daily.set_participants(participants_ids)
                db.commit()
                db.refresh(daily)
                logger.info(
                    f"Daily {daily_id} participants updated: {len(participants_ids)} participants"
                )
                return daily
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating participants for daily {daily_id}: {e}")
            raise

    @staticmethod
    def mark_registered_in_redmine(db: Session, daily_id: int) -> Optional[Daily]:
        """
        Mark a daily as registered in Redmine.

        Args:
            db (Session): Database session
            daily_id (int): Daily ID

        Returns:
            Optional[Daily]: Updated daily instance or None
        """
        try:
            daily = DailyService.get_by_id(db, daily_id)
            if daily:
                daily.mark_registered_in_redmine()
                db.commit()
                db.refresh(daily)
                logger.info(f"Daily {daily_id} marked as registered in Redmine")
                return daily
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking daily {daily_id} as registered: {e}")
            raise

    @staticmethod
    def get_latest_unregistered_daily_by_group(
        db: Session, telegram_group_id: int
    ) -> Optional[Daily]:
        """
        Get the latest daily that has not been registered in Redmine for a group.

        Args:
            db (Session): Database session
            telegram_group_id (int): Telegram group ID

        Returns:
            Optional[Daily]: Latest unregistered daily instance or None
        """
        return (
            db.query(Daily)
            .filter(
                Daily.telegram_group_id == telegram_group_id,
                Daily.registered_in_redmine == False,
                Daily.end_time != None,  # Only finished dailies
            )
            .order_by(Daily.end_time.desc())
            .first()
        )
