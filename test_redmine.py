#!/usr/bin/env python3
"""
Test script for Redmine daily task creation functionality
"""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.redmine_service import RedmineService


def test_create_daily():
    """
    Test the create_daily_task functionality
    """
    print("🧪 Test de creación de Daily en Redmine")
    print("=" * 50)

    # Get token from user input
    token = input("Introduce tu token de Redmine: ").strip()

    if not token:
        print("❌ Token no proporcionado")
        return

    # Initialize Redmine service
    redmine_service = RedmineService(token)

    # Test connection first
    print("\n🔗 Probando conexión...")
    if not redmine_service.test_connection():
        print("❌ Error en la conexión. Verifica tu token.")
        return

    print("✅ Conexión exitosa")

    # Get available projects
    print("\n📋 Obteniendo proyectos disponibles...")
    projects = redmine_service.get_projects()

    if not projects:
        print("❌ No se encontraron proyectos")
        return

    print(f"✅ Encontrados {len(projects)} proyectos:")
    for i, project in enumerate(projects[:10]):  # Show first 10 projects
        print(
            f"  {i+1}. {project['name']} (ID: {project['id']}, Code: {project['identifier']})"
        )

    if len(projects) > 10:
        print(f"  ... y {len(projects) - 10} más")

    # Let user select a project
    try:
        project_choice = input(
            "\nSelecciona el número del proyecto (o presiona Enter para usar el primero): "
        ).strip()

        if project_choice:
            project_index = int(project_choice) - 1
            if project_index < 0 or project_index >= len(projects):
                print("❌ Selección inválida, usando el primer proyecto")
                project_index = 0
        else:
            project_index = 0

        selected_project = projects[project_index]
        print(
            f"\n🎯 Proyecto seleccionado: {selected_project['name']} (ID: {selected_project['id']})"
        )

    except (ValueError, IndexError):
        print("❌ Selección inválida, usando el primer proyecto")
        selected_project = projects[0]

    # Get team name
    team_name = input(
        "\nIntroduce el nombre del equipo (o presiona Enter para 'TestTeam'): "
    ).strip()
    if not team_name:
        team_name = "TestTeam"

    # Create the daily task
    print(f"\n🚀 Creando daily para el equipo '{team_name}'...")

    task_data = redmine_service.create_daily_task(
        project_id=selected_project["id"],
        team_name=team_name,
        daily_date=datetime.now(),
    )

    if task_data:
        print("✅ Daily creada exitosamente!")
        print(f"   ID: {task_data['id']}")
        print(f"   Título: {task_data['subject']}")
        print(f"   Proyecto: {selected_project['name']}")
        print(f"   Fecha inicio: {task_data['start_date']}")
        print(f"   Fecha fin: {task_data['due_date']}")

        # Test time logging
        print(f"\n⏱️  Probando logueo de tiempo...")

        hours = input(
            "Introduce las horas a loguear (o presiona Enter para 1.5): "
        ).strip()
        try:
            hours = float(hours) if hours else 1.5
        except ValueError:
            hours = 1.5

        time_entry = redmine_service.log_daily(issue_id=task_data["id"], hours=hours)

        if time_entry:
            print("✅ Tiempo logueado exitosamente!")
            print(f"   ID entrada tiempo: {time_entry['id']}")
            print(f"   Horas: {time_entry['hours']}")
            print(f"   Fecha: {time_entry['spent_on']}")
            print(f"   Comentarios: {time_entry['comments']}")
        else:
            print("❌ Error al loguear tiempo")

        # Show final URL
        from app.config import settings

        task_url = f"{settings.redmine_url}/issues/{task_data['id']}"
        print(f"\n🔗 URL de la tarea: {task_url}")

    else:
        print("❌ Error al crear la daily")


if __name__ == "__main__":
    try:
        test_create_daily()
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelado por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback

        traceback.print_exc()
