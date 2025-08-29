"""
Redmine API service for interacting with Redmine server
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from redminelib import Redmine
from redminelib.exceptions import ResourceNotFoundError, AuthError
from app.config import settings

logger = logging.getLogger(__name__)


class RedmineService:
    """
    Service class for Redmine API operations
    """

    def __init__(self, api_token: str):
        """
        Initialize Redmine service with API token

        Args:
            api_token (str): User's Redmine API token
        """
        self.api_token = api_token
        self.redmine = Redmine(settings.redmine_url, key=api_token)

    def test_connection(self) -> bool:
        """
        Test connection to Redmine API

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Try to get current user info to test authentication
            user = self.redmine.auth()
            logger.info(f"Connection test successful for user: {user.login}")
            return True
        except (AuthError, Exception) as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_projects(self) -> List[Dict]:
        """
        Get all projects accessible to the user

        Returns:
            List[Dict]: List of projects with id, name, and identifier
        """
        try:
            projects = []
            redmine_projects = self.redmine.project.all()

            for project in redmine_projects:
                projects.append(
                    {
                        "id": project.id,
                        "name": project.name,
                        "identifier": project.identifier,
                        "description": getattr(project, "description", ""),
                        "status": getattr(project, "status", 1),
                    }
                )

            logger.info(f"Retrieved {len(projects)} projects")
            return projects

        except (AuthError, Exception) as e:
            logger.error(f"Error retrieving projects: {e}")
            return []

    def get_project_by_id(self, project_id: int) -> Optional[Dict]:
        """
        Get specific project by ID

        Args:
            project_id (int): Project ID

        Returns:
            Optional[Dict]: Project data or None if not found
        """
        try:
            project = self.redmine.project.get(project_id)
            return {
                "id": project.id,
                "name": project.name,
                "identifier": project.identifier,
                "description": getattr(project, "description", ""),
                "status": getattr(project, "status", 1),
            }
        except (ResourceNotFoundError, AuthError, Exception) as e:
            logger.error(f"Error retrieving project {project_id}: {e}")
            return None

    def get_project_by_identifier(self, identifier: str) -> Optional[Dict]:
        """
        Get specific project by identifier

        Args:
            identifier (str): Project identifier

        Returns:
            Optional[Dict]: Project data or None if not found
        """
        try:
            project = self.redmine.project.get(identifier)
            return {
                "id": project.id,
                "name": project.name,
                "identifier": project.identifier,
                "description": getattr(project, "description", ""),
                "status": getattr(project, "status", 1),
            }
        except (ResourceNotFoundError, AuthError, Exception) as e:
            logger.error(f"Error retrieving project {identifier}: {e}")
            return None

    def get_current_user_id(self) -> Optional[int]:
        """
        Get current authenticated user ID

        Returns:
            Optional[int]: Current user ID or None if failed
        """
        try:
            user = self.redmine.auth()
            logger.info(f"Retrieved current user ID: {user.id}")
            return user.id
        except (AuthError, Exception) as e:
            logger.error(f"Error getting current user ID: {e}")
            return None

    def create_daily_task(
        self,
        project_id: int,
        team_name: str,
        daily_date: Optional[datetime] = None,
        estimated_time: Optional[float] = None,
    ) -> Optional[Dict]:
        """
        Create a daily task in Redmine

        Args:
            project_id (int): Project ID where the task will be created
            team_name (str): Team name for the task subject
            daily_date (datetime, optional): Date for the daily. If None, uses current date
            estimated_time (float, optional): Estimated time in hours for the task

        Returns:
            Optional[Dict]: Created task data or None if failed
        """
        try:
            if daily_date is None:
                daily_date = datetime.now()

            # Get current user ID for assignment
            current_user_id = self.get_current_user_id()
            if current_user_id is None:
                logger.error("Could not get current user ID for task assignment")
                return None

            # Format date as DD-MM-YYYY
            date_str = daily_date.strftime("%d-%m-%Y")

            # Create subject with format [Daily][team_name] DD-MM-YYYY
            subject = f"[Daily][{team_name}] {date_str}"

            # Create the task with only required fields
            issue_data = {
                "project_id": project_id,
                "subject": subject,
                "assigned_to_id": current_user_id,
                "start_date": daily_date.date(),
                "due_date": daily_date.date(),
            }

            # Add estimated time if provided
            if estimated_time is not None:
                issue_data["estimated_hours"] = estimated_time

            issue = self.redmine.issue.create(**issue_data)

            logger.info(f"Daily task created successfully with ID: {issue.id}")

            return {
                "id": issue.id,
                "subject": issue.subject,
                "project_id": project_id,
                "tracker_id": issue.tracker.id,
                "status_id": issue.status.id,
                "assigned_to_id": (
                    issue.assigned_to.id if hasattr(issue, "assigned_to") else None
                ),
                "start_date": str(issue.start_date),
                "due_date": str(issue.due_date),
            }

        except (ResourceNotFoundError, AuthError, Exception) as e:
            logger.error(f"Error creating daily task for team {team_name}: {e}")
            return None

    def log_daily(
        self, issue_id: int, hours: float, activity_name: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Log time entry for a daily task in Redmine

        Args:
            issue_id (int): Issue ID to log time to
            hours (float): Hours to log
            activity_name (str, optional): Name of the activity. If None, uses first available activity

        Returns:
            Optional[Dict]: Created time entry data or None if failed
        """
        try:
            # Get activity ID
            activity_id = None
            if activity_name:
                activity_id = self.get_activity_id_by_name(activity_name)

            # If no specific activity or not found, try to find "Meeting" or use first available
            if activity_id is None:
                activities = self.get_activities()
                if not activities:
                    logger.error("No activities available for time logging")
                    return None

                # Try to find "Meeting" activity first
                for activity in activities:
                    if "meeting" in activity["name"].lower():
                        activity_id = activity["id"]
                        break

                # If no meeting activity found, use the first one
                if activity_id is None:
                    activity_id = activities[0]["id"]
                    logger.info(
                        f"Using first available activity: {activities[0]['name']} (ID: {activity_id})"
                    )

            # Create time entry
            time_entry = self.redmine.time_entry.create(
                issue_id=issue_id,
                spent_on=datetime.now().date(),
                hours=hours,
                comments="Daily",
                activity_id=activity_id,
            )

            logger.info(f"Time entry logged successfully with ID: {time_entry.id}")

            return {
                "id": time_entry.id,
                "issue_id": issue_id,
                "spent_on": str(time_entry.spent_on),
                "hours": time_entry.hours,
                "comments": time_entry.comments,
                "activity_id": time_entry.activity.id,
                "activity_name": time_entry.activity.name,
            }

        except (ResourceNotFoundError, AuthError, Exception) as e:
            logger.error(f"Error logging time for issue {issue_id}: {e}")
            return None

    def get_trackers(self) -> List[Dict]:
        """
        Get all available trackers

        Returns:
            List[Dict]: List of trackers with id and name
        """
        try:
            trackers = []
            redmine_trackers = self.redmine.tracker.all()

            for tracker in redmine_trackers:
                trackers.append({"id": tracker.id, "name": tracker.name})

            logger.info(f"Retrieved {len(trackers)} trackers")
            return trackers

        except (AuthError, Exception) as e:
            logger.error(f"Error retrieving trackers: {e}")
            return []

    def get_tracker_id_by_name(self, tracker_name: str) -> Optional[int]:
        """
        Get tracker ID by name

        Args:
            tracker_name (str): Name of the tracker

        Returns:
            Optional[int]: Tracker ID or None if not found
        """
        try:
            trackers = self.get_trackers()
            for tracker in trackers:
                if tracker["name"].lower() == tracker_name.lower():
                    return tracker["id"]

            logger.warning(f"Tracker '{tracker_name}' not found")
            return None

        except Exception as e:
            logger.error(f"Error getting tracker ID for '{tracker_name}': {e}")
            return None

    def get_issue_statuses(self) -> List[Dict]:
        """
        Get all available issue statuses

        Returns:
            List[Dict]: List of statuses with id and name
        """
        try:
            statuses = []
            redmine_statuses = self.redmine.issue_status.all()

            for status in redmine_statuses:
                statuses.append({"id": status.id, "name": status.name})

            logger.info(f"Retrieved {len(statuses)} issue statuses")
            return statuses

        except (AuthError, Exception) as e:
            logger.error(f"Error retrieving issue statuses: {e}")
            return []

    def get_status_id_by_name(self, status_name: str) -> Optional[int]:
        """
        Get status ID by name

        Args:
            status_name (str): Name of the status

        Returns:
            Optional[int]: Status ID or None if not found
        """
        try:
            statuses = self.get_issue_statuses()
            for status in statuses:
                if status["name"].lower() == status_name.lower():
                    return status["id"]

            logger.warning(f"Status '{status_name}' not found")
            return None

        except Exception as e:
            logger.error(f"Error getting status ID for '{status_name}': {e}")
            return None

    def get_activities(self) -> List[Dict]:
        """
        Get all available time entry activities

        Returns:
            List[Dict]: List of activities with id and name
        """
        try:
            activities = []
            redmine_activities = self.redmine.enumeration.filter(
                resource="time_entry_activities"
            )

            for activity in redmine_activities:
                activities.append({"id": activity.id, "name": activity.name})

            logger.info(f"Retrieved {len(activities)} time entry activities")
            return activities

        except (AuthError, Exception) as e:
            logger.error(f"Error retrieving time entry activities: {e}")
            return []

    def get_activity_id_by_name(self, activity_name: str) -> Optional[int]:
        """
        Get activity ID by name

        Args:
            activity_name (str): Name of the activity

        Returns:
            Optional[int]: Activity ID or None if not found
        """
        try:
            activities = self.get_activities()
            for activity in activities:
                if activity["name"].lower() == activity_name.lower():
                    return activity["id"]

            logger.warning(f"Activity '{activity_name}' not found")
            return None

        except Exception as e:
            logger.error(f"Error getting activity ID for '{activity_name}': {e}")
            return None

    def update_issue_status(self, issue_id: int, status_name: str) -> Optional[Dict]:
        """
        Update the status of an issue in Redmine

        Args:
            issue_id (int): Issue ID to update
            status_name (str): Name of the status to set (e.g., 'IN PROGRESS', 'Closed', etc.)

        Returns:
            Optional[Dict]: Updated issue data or None if failed
        """
        try:
            # Get the status ID by name
            status_id = self.get_status_id_by_name(status_name)
            if status_id is None:
                logger.error(f"Status '{status_name}' not found")
                return None

            # Get the current issue to verify it exists
            try:
                issue = self.redmine.issue.get(issue_id)
            except ResourceNotFoundError:
                logger.error(f"Issue with ID {issue_id} not found")
                return None

            # Update the issue status
            issue.status_id = status_id
            issue.save()

            logger.info(
                f"Issue {issue_id} status updated to '{status_name}' (ID: {status_id})"
            )

            # Return updated issue data
            updated_issue = self.redmine.issue.get(issue_id)
            return {
                "id": updated_issue.id,
                "subject": updated_issue.subject,
                "project_id": updated_issue.project.id,
                "tracker_id": updated_issue.tracker.id,
                "status_id": updated_issue.status.id,
                "status_name": updated_issue.status.name,
                "assigned_to_id": (
                    updated_issue.assigned_to.id
                    if hasattr(updated_issue, "assigned_to")
                    else None
                ),
                "start_date": str(getattr(updated_issue, "start_date", "")),
                "due_date": str(getattr(updated_issue, "due_date", "")),
                "updated_on": str(updated_issue.updated_on),
            }

        except (ResourceNotFoundError, AuthError, Exception) as e:
            logger.error(
                f"Error updating status for issue {issue_id} to '{status_name}': {e}"
            )
            return None
