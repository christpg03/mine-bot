#!/usr/bin/env python3
"""
Test script to view all registered users in the database.
Shows all user information including decrypted tokens.
"""

import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.database import DatabaseSession
from app.database.models import User


def format_datetime(dt):
    """Format datetime for display."""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return "N/A"


def format_boolean(value):
    """Format boolean for display."""
    return "✅ Yes" if value else "❌ No"


def view_all_users():
    """View all users registered in the database."""
    print("=" * 80)
    print("🔍 VIEWING ALL REGISTERED USERS")
    print("=" * 80)

    try:
        with DatabaseSession() as session:
            users = session.query(User).all()

            if not users:
                print("❌ No users found in the database.")
                return

            print(f"📊 Total users found: {len(users)}")
            print("-" * 80)

            for i, user in enumerate(users, 1):
                print(f"\n👤 USER #{i}")
                print(f"   Database ID: {user.id}")
                print(f"   Telegram ID: {user.telegram_id}")
                print(f"   Username: {user.username or 'Not set'}")
                print(
                    f"   Has Redmine Token: {format_boolean(user.has_redmine_token())}"
                )

                # Show token if available (be careful with this in production!)
                if user.has_redmine_token():
                    try:
                        token = user.get_redmine_token()
                        if token:
                            # Show only first and last 4 characters for security
                            masked_token = (
                                f"{token[:4]}...{token[-4:]}"
                                if len(token) > 8
                                else "****"
                            )
                            print(f"   Redmine Token: {masked_token}")
                        else:
                            print(f"   Redmine Token: ❌ Error decrypting")
                    except Exception as e:
                        print(f"   Redmine Token: ❌ Error: {e}")

                print(f"   Is Active: {format_boolean(user.is_active)}")
                print(f"   Created At: {format_datetime(user.created_at)}")
                print(f"   Updated At: {format_datetime(user.updated_at)}")
                print("-" * 50)

    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        return False

    return True


def show_user_statistics():
    """Show basic statistics about users."""
    print("\n📈 USER STATISTICS")
    print("=" * 40)

    try:
        with DatabaseSession() as session:
            total_users = session.query(User).count()
            active_users = session.query(User).filter(User.is_active == True).count()
            users_with_tokens = (
                session.query(User)
                .filter(User.encrypted_redmine_token.isnot(None))
                .count()
            )
            users_with_usernames = (
                session.query(User).filter(User.username.isnot(None)).count()
            )

            print(f"📊 Total Users: {total_users}")
            print(f"✅ Active Users: {active_users}")
            print(f"🔑 Users with Redmine Tokens: {users_with_tokens}")
            print(f"👤 Users with Usernames: {users_with_usernames}")

            if total_users > 0:
                print(f"📈 Token Coverage: {(users_with_tokens/total_users)*100:.1f}%")
                print(
                    f"📈 Username Coverage: {(users_with_usernames/total_users)*100:.1f}%"
                )
                print(f"📈 Active Rate: {(active_users/total_users)*100:.1f}%")

    except Exception as e:
        print(f"❌ Error calculating statistics: {e}")


def main():
    """Main function."""
    print("🤖 MINE-BOT DATABASE VIEWER - USERS")
    print(f"📅 Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # View all users
    if view_all_users():
        # Show statistics
        show_user_statistics()

    print("\n" + "=" * 80)
    print("✅ User database view completed!")


if __name__ == "__main__":
    main()
