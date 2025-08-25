#!/usr/bin/env python3
"""
Test script to view all daily meetings in the database.
Shows all daily information including participants and related data.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.database import DatabaseSession
from app.database.models import Daily, Team, User


def format_datetime(dt):
    """Format datetime for display."""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return "N/A"


def format_boolean(value):
    """Format boolean for display."""
    return "✅ Yes" if value else "❌ No"


def calculate_duration(start_time, end_time):
    """Calculate duration between start and end time."""
    if start_time and end_time:
        duration = end_time - start_time
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    return "Ongoing" if start_time and not end_time else "N/A"


def get_team_info(session, team_id):
    """Get team information."""
    try:
        team = session.query(Team).filter(Team.id == team_id).first()
        if team:
            return f"{team.team_name} ({team.redmine_project_code})"
        else:
            return f"Team not found (ID: {team_id})"
    except Exception as e:
        return f"Error getting team info: {e}"


def get_participants_info(session, participants_ids):
    """Get participant information."""
    if not participants_ids:
        return "No participants"

    try:
        participants = []
        for participant_id in participants_ids:
            user = (
                session.query(User).filter(User.telegram_id == participant_id).first()
            )
            if user:
                participants.append(f"{user.username or 'Unknown'} ({participant_id})")
            else:
                participants.append(f"Unknown ({participant_id})")

        return participants
    except Exception as e:
        return [f"Error getting participants: {e}"]


def view_all_dailys():
    """View all daily meetings registered in the database."""
    print("=" * 80)
    print("🔍 VIEWING ALL DAILY MEETINGS")
    print("=" * 80)

    try:
        with DatabaseSession() as session:
            dailys = session.query(Daily).order_by(Daily.start_time.desc()).all()

            if not dailys:
                print("❌ No daily meetings found in the database.")
                return

            print(f"📊 Total daily meetings found: {len(dailys)}")
            print("-" * 80)

            for i, daily in enumerate(dailys, 1):
                print(f"\n📅 DAILY #{i}")
                print(f"   Database ID: {daily.id}")
                print(f"   Team: {get_team_info(session, daily.team_id)}")
                print(f"   Telegram Group ID: {daily.telegram_group_id}")
                print(f"   Start Time: {format_datetime(daily.start_time)}")
                print(f"   End Time: {format_datetime(daily.end_time)}")
                print(
                    f"   Duration: {calculate_duration(daily.start_time, daily.end_time)}"
                )
                print(
                    f"   Registered in Redmine: {format_boolean(daily.registered_in_redmine)}"
                )

                # Show participants
                participants = get_participants_info(session, daily.get_participants())
                print(f"   Participants ({len(daily.get_participants())} total):")
                if isinstance(participants, list):
                    for participant in participants:
                        print(f"     - {participant}")
                else:
                    print(f"     {participants}")

                print(f"   Created At: {format_datetime(daily.created_at)}")
                print(f"   Updated At: {format_datetime(daily.updated_at)}")
                print("-" * 50)

    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        return False

    return True


def show_daily_statistics():
    """Show basic statistics about daily meetings."""
    print("\n📈 DAILY MEETING STATISTICS")
    print("=" * 40)

    try:
        with DatabaseSession() as session:
            total_dailys = session.query(Daily).count()
            finished_dailys = (
                session.query(Daily).filter(Daily.end_time.isnot(None)).count()
            )
            ongoing_dailys = (
                session.query(Daily).filter(Daily.end_time.is_(None)).count()
            )
            registered_in_redmine = (
                session.query(Daily).filter(Daily.registered_in_redmine == True).count()
            )

            print(f"📊 Total Daily Meetings: {total_dailys}")
            print(f"✅ Finished Meetings: {finished_dailys}")
            print(f"⏰ Ongoing Meetings: {ongoing_dailys}")
            print(f"🎯 Registered in Redmine: {registered_in_redmine}")

            if total_dailys > 0:
                print(f"📈 Completion Rate: {(finished_dailys/total_dailys)*100:.1f}%")
                print(
                    f"📈 Redmine Registration Rate: {(registered_in_redmine/total_dailys)*100:.1f}%"
                )

            # Calculate average participants
            dailys = session.query(Daily).all()
            total_participants = sum(len(daily.get_participants()) for daily in dailys)
            avg_participants = (
                total_participants / total_dailys if total_dailys > 0 else 0
            )
            print(f"👥 Average Participants per Daily: {avg_participants:.1f}")

            # Show recent activity (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_dailys = (
                session.query(Daily).filter(Daily.start_time >= week_ago).count()
            )
            print(f"📅 Daily Meetings (Last 7 days): {recent_dailys}")

    except Exception as e:
        print(f"❌ Error calculating statistics: {e}")


def show_team_daily_activity():
    """Show daily activity by team."""
    print("\n🏢 DAILY ACTIVITY BY TEAM")
    print("=" * 40)

    try:
        with DatabaseSession() as session:
            team_counts = {}
            dailys = session.query(Daily).all()

            for daily in dailys:
                team_info = get_team_info(session, daily.team_id)
                team_counts[team_info] = team_counts.get(team_info, 0) + 1

            print("📋 Daily meetings by team:")
            for team, count in sorted(
                team_counts.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"   {team}: {count} meeting(s)")

    except Exception as e:
        print(f"❌ Error getting team activity: {e}")


def show_most_active_participants():
    """Show users who participate most in dailys."""
    print("\n👥 MOST ACTIVE PARTICIPANTS")
    print("=" * 40)

    try:
        with DatabaseSession() as session:
            participant_counts = {}
            dailys = session.query(Daily).all()

            for daily in dailys:
                for participant_id in daily.get_participants():
                    participant_counts[participant_id] = (
                        participant_counts.get(participant_id, 0) + 1
                    )

            print("📋 Daily participation by user:")
            for participant_id, count in sorted(
                participant_counts.items(), key=lambda x: x[1], reverse=True
            )[:10]:
                user = (
                    session.query(User)
                    .filter(User.telegram_id == participant_id)
                    .first()
                )
                username = user.username if user else "Unknown"
                print(f"   {username} ({participant_id}): {count} meeting(s)")

    except Exception as e:
        print(f"❌ Error getting participant statistics: {e}")


def main():
    """Main function."""
    print("🤖 MINE-BOT DATABASE VIEWER - DAILY MEETINGS")
    print(f"📅 Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # View all dailys
    if view_all_dailys():
        # Show statistics
        show_daily_statistics()
        # Show team activity
        show_team_daily_activity()
        # Show most active participants
        show_most_active_participants()

    print("\n" + "=" * 80)
    print("✅ Daily meetings database view completed!")


if __name__ == "__main__":
    main()
