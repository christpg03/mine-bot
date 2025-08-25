#!/usr/bin/env python3
"""
Test script to view all registered teams in the database.
Shows all team information including related data.
"""

import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.database import DatabaseSession
from app.database.models import Team, User


def format_datetime(dt):
    """Format datetime for display."""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return "N/A"


def format_boolean(value):
    """Format boolean for display."""
    return "✅ Yes" if value else "❌ No"


def get_creator_info(session, creator_id):
    """Get creator user information."""
    try:
        user = session.query(User).filter(User.telegram_id == creator_id).first()
        if user:
            return f"{user.username or 'Unknown'} (ID: {creator_id})"
        else:
            return f"User not found (ID: {creator_id})"
    except Exception as e:
        return f"Error getting user info: {e}"


def view_all_teams():
    """View all teams registered in the database."""
    print("=" * 80)
    print("🔍 VIEWING ALL REGISTERED TEAMS")
    print("=" * 80)

    try:
        with DatabaseSession() as session:
            teams = session.query(Team).all()

            if not teams:
                print("❌ No teams found in the database.")
                return

            print(f"📊 Total teams found: {len(teams)}")
            print("-" * 80)

            for i, team in enumerate(teams, 1):
                print(f"\n🏢 TEAM #{i}")
                print(f"   Database ID: {team.id}")
                print(f"   Team Name: {team.team_name}")
                print(f"   Telegram Group ID: {team.telegram_group_id}")
                print(f"   Redmine Project Code: {team.redmine_project_code}")
                print(f"   Redmine Project ID: {team.redmine_project_id}")
                print(
                    f"   Created By: {get_creator_info(session, team.created_by_user_id)}"
                )
                print(f"   Is Active: {format_boolean(team.is_active)}")
                print(f"   Created At: {format_datetime(team.created_at)}")
                print(f"   Updated At: {format_datetime(team.updated_at)}")
                print("-" * 50)

    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        return False

    return True


def show_team_statistics():
    """Show basic statistics about teams."""
    print("\n📈 TEAM STATISTICS")
    print("=" * 40)

    try:
        with DatabaseSession() as session:
            total_teams = session.query(Team).count()
            active_teams = session.query(Team).filter(Team.is_active == True).count()

            # Get unique project codes and group IDs
            unique_projects = (
                session.query(Team.redmine_project_code).distinct().count()
            )
            unique_groups = session.query(Team.telegram_group_id).distinct().count()

            print(f"📊 Total Teams: {total_teams}")
            print(f"✅ Active Teams: {active_teams}")
            print(f"🎯 Unique Redmine Projects: {unique_projects}")
            print(f"💬 Unique Telegram Groups: {unique_groups}")

            if total_teams > 0:
                print(f"📈 Active Rate: {(active_teams/total_teams)*100:.1f}%")

            # Show most popular project codes
            print(f"\n📋 PROJECT DISTRIBUTION:")
            project_counts = {}
            teams = session.query(Team).all()
            for team in teams:
                project_counts[team.redmine_project_code] = (
                    project_counts.get(team.redmine_project_code, 0) + 1
                )

            for project, count in sorted(
                project_counts.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"   {project}: {count} team(s)")

    except Exception as e:
        print(f"❌ Error calculating statistics: {e}")


def show_team_creators():
    """Show who created the most teams."""
    print("\n👥 TEAM CREATORS")
    print("=" * 40)

    try:
        with DatabaseSession() as session:
            creator_counts = {}
            teams = session.query(Team).all()

            for team in teams:
                creator_counts[team.created_by_user_id] = (
                    creator_counts.get(team.created_by_user_id, 0) + 1
                )

            print("📋 Teams created by user:")
            for creator_id, count in sorted(
                creator_counts.items(), key=lambda x: x[1], reverse=True
            ):
                creator_info = get_creator_info(session, creator_id)
                print(f"   {creator_info}: {count} team(s)")

    except Exception as e:
        print(f"❌ Error getting creator statistics: {e}")


def main():
    """Main function."""
    print("🤖 MINE-BOT DATABASE VIEWER - TEAMS")
    print(f"📅 Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # View all teams
    if view_all_teams():
        # Show statistics
        show_team_statistics()
        # Show creators
        show_team_creators()

    print("\n" + "=" * 80)
    print("✅ Team database view completed!")


if __name__ == "__main__":
    main()
