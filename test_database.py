#!/usr/bin/env python3
"""
Comprehensive test script to view all database information.
Combines users, teams, and daily meetings in one convenient script.
"""

import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.database import DatabaseSession, check_database_connection
from app.database.models import User, Team, Daily


def show_menu():
    """Display menu options."""
    print("\n" + "=" * 60)
    print("🤖 MINE-BOT DATABASE VIEWER - MAIN MENU")
    print("=" * 60)
    print("1. 👤 View All Users")
    print("2. 🏢 View All Teams")
    print("3. 📅 View All Daily Meetings")
    print("4. 📊 View Database Summary")
    print("5. 🔄 View All (Users + Teams + Dailys)")
    print("6. ❌ Exit")
    print("=" * 60)


def format_datetime(dt):
    """Format datetime for display."""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return "N/A"


def format_boolean(value):
    """Format boolean for display."""
    return "✅ Yes" if value else "❌ No"


def view_users_summary():
    """Show users summary."""
    print("\n👤 USERS SUMMARY")
    print("-" * 40)

    try:
        with DatabaseSession() as session:
            users = session.query(User).all()

            if not users:
                print("❌ No users found.")
                return

            print(f"📊 Total Users: {len(users)}")
            active_users = sum(1 for user in users if user.is_active)
            users_with_tokens = sum(1 for user in users if user.has_redmine_token())

            print(f"✅ Active Users: {active_users}")
            print(f"🔑 Users with Tokens: {users_with_tokens}")

            print("\n📋 Recent Users:")
            recent_users = sorted(users, key=lambda x: x.created_at, reverse=True)[:5]
            for user in recent_users:
                username = user.username or "No username"
                print(
                    f"   - {username} (ID: {user.telegram_id}) - {format_datetime(user.created_at)}"
                )

    except Exception as e:
        print(f"❌ Error: {e}")


def view_teams_summary():
    """Show teams summary."""
    print("\n🏢 TEAMS SUMMARY")
    print("-" * 40)

    try:
        with DatabaseSession() as session:
            teams = session.query(Team).all()

            if not teams:
                print("❌ No teams found.")
                return

            print(f"📊 Total Teams: {len(teams)}")
            active_teams = sum(1 for team in teams if team.is_active)
            print(f"✅ Active Teams: {active_teams}")

            # Show unique projects
            unique_projects = set(team.redmine_project_code for team in teams)
            print(f"🎯 Unique Projects: {len(unique_projects)}")

            print("\n📋 Recent Teams:")
            recent_teams = sorted(teams, key=lambda x: x.created_at, reverse=True)[:5]
            for team in recent_teams:
                print(
                    f"   - {team.team_name} ({team.redmine_project_code}) - {format_datetime(team.created_at)}"
                )

    except Exception as e:
        print(f"❌ Error: {e}")


def view_dailys_summary():
    """Show dailys summary."""
    print("\n📅 DAILY MEETINGS SUMMARY")
    print("-" * 40)

    try:
        with DatabaseSession() as session:
            dailys = session.query(Daily).all()

            if not dailys:
                print("❌ No daily meetings found.")
                return

            print(f"📊 Total Daily Meetings: {len(dailys)}")
            finished_dailys = sum(1 for daily in dailys if daily.end_time)
            registered_dailys = sum(
                1 for daily in dailys if daily.registered_in_redmine
            )

            print(f"✅ Finished Meetings: {finished_dailys}")
            print(f"🎯 Registered in Redmine: {registered_dailys}")

            # Calculate total participants
            total_participants = sum(len(daily.get_participants()) for daily in dailys)
            avg_participants = total_participants / len(dailys) if dailys else 0
            print(f"👥 Average Participants: {avg_participants:.1f}")

            print("\n📋 Recent Meetings:")
            recent_dailys = sorted(dailys, key=lambda x: x.start_time, reverse=True)[:5]
            for daily in recent_dailys:
                participants_count = len(daily.get_participants())
                print(
                    f"   - Team ID {daily.team_id} - {format_datetime(daily.start_time)} ({participants_count} participants)"
                )

    except Exception as e:
        print(f"❌ Error: {e}")


def view_database_summary():
    """Show complete database summary."""
    print("\n📊 DATABASE SUMMARY")
    print("=" * 60)

    view_users_summary()
    view_teams_summary()
    view_dailys_summary()

    # Show database file info
    print("\n💾 DATABASE FILE INFO")
    print("-" * 40)

    try:
        from app.database.database import get_database_path

        db_path = get_database_path()

        if os.path.exists(db_path):
            file_size = os.path.getsize(db_path)
            file_size_mb = file_size / (1024 * 1024)
            file_modified = datetime.fromtimestamp(os.path.getmtime(db_path))

            print(f"📁 Database Path: {db_path}")
            print(f"📏 File Size: {file_size_mb:.2f} MB ({file_size} bytes)")
            print(f"📅 Last Modified: {format_datetime(file_modified)}")
        else:
            print("❌ Database file not found!")

    except Exception as e:
        print(f"❌ Error getting database info: {e}")


def view_all():
    """View all data from all tables."""
    print("\n🔄 VIEWING ALL DATABASE DATA")
    print("=" * 60)

    # Import and run individual scripts
    try:
        print("\n" + "🔄" * 20 + " USERS " + "🔄" * 20)
        import test_users

        test_users.view_all_users()
        test_users.show_user_statistics()

        print("\n" + "🔄" * 20 + " TEAMS " + "🔄" * 20)
        import test_teams

        test_teams.view_all_teams()
        test_teams.show_team_statistics()

        print("\n" + "🔄" * 20 + " DAILYS " + "🔄" * 20)
        import test_dailys

        test_dailys.view_all_dailys()
        test_dailys.show_daily_statistics()

    except Exception as e:
        print(f"❌ Error running comprehensive view: {e}")
        # Fallback to summaries
        view_database_summary()


def main():
    """Main interactive function."""
    print("🤖 MINE-BOT DATABASE COMPREHENSIVE VIEWER")
    print(f"📅 Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check database connection
    print("\n🔍 Checking database connection...")
    if not check_database_connection():
        print("❌ Cannot connect to database. Exiting.")
        return
    print("✅ Database connection successful!")

    while True:
        show_menu()

        try:
            choice = input("\nSelect an option (1-6): ").strip()

            if choice == "1":
                import test_users

                test_users.view_all_users()
                test_users.show_user_statistics()

            elif choice == "2":
                import test_teams

                test_teams.view_all_teams()
                test_teams.show_team_statistics()

            elif choice == "3":
                import test_dailys

                test_dailys.view_all_dailys()
                test_dailys.show_daily_statistics()

            elif choice == "4":
                view_database_summary()

            elif choice == "5":
                view_all()

            elif choice == "6":
                print("\n👋 Goodbye!")
                break

            else:
                print("❌ Invalid option. Please select 1-6.")

            input("\nPress Enter to continue...")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
