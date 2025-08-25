import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_NAME = "mine_bot.db"
# Get project root directory (two levels up from app/database/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATABASE_PATH = os.path.join(PROJECT_ROOT, DATABASE_NAME)
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Configuración del motor de SQLAlchemy para SQLite3
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,  # Permite usar SQLite en múltiples threads
    },
    echo=False,  # Cambiar a True para ver las consultas SQL en desarrollo
)

# Configuración de metadatos y base declarativa
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# Configuración de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_database_session():
    """
    Obtiene una nueva sesión de base de datos.
    Recuerda cerrar la sesión después de usarla.

    Returns:
        Session: Nueva sesión de SQLAlchemy
    """
    return SessionLocal()


def init_database():
    """
    Inicializa la base de datos SQLite3 creando todas las tablas.
    Debe llamarse después de definir todos los modelos.
    """
    try:
        # Crear el directorio si no existe
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

        # Crear todas las tablas definidas en los modelos
        Base.metadata.create_all(bind=engine)

        logger.info(f"✅ Base de datos SQLite3 inicializada en: {DATABASE_PATH}")
        return True
    except Exception as e:
        logger.error(f"❌ Error al inicializar la base de datos: {e}")
        return False


def check_database_connection():
    """
    Verifica que la conexión a la base de datos funcione correctamente.

    Returns:
        bool: True si la conexión es exitosa, False en caso contrario
    """
    try:
        with engine.connect() as connection:
            from sqlalchemy import text

            result = connection.execute(text("SELECT 1"))
            logger.info("✅ Conexión a la base de datos SQLite3 exitosa")
            return True
    except Exception as e:
        logger.error(f"❌ Error de conexión a la base de datos: {e}")
        return False


def close_database_connection():
    """
    Cierra todas las conexiones de la base de datos.
    """
    try:
        engine.dispose()
        logger.info("✅ Conexiones de base de datos cerradas")
    except Exception as e:
        logger.error(f"❌ Error al cerrar conexiones: {e}")


class DatabaseSession:
    """
    Context manager para manejo automático de sesiones de base de datos SQLite3.

    Uso:
        with DatabaseSession() as session:
            # Operaciones con la base de datos
            result = session.query(Model).all()
            # La sesión se cierra automáticamente
    """

    def __enter__(self):
        self.session = SessionLocal()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                self.session.rollback()
                logger.error(f"❌ Error en transacción, rollback ejecutado: {exc_val}")
            else:
                self.session.commit()
        except Exception as e:
            logger.error(f"❌ Error durante commit/rollback: {e}")
        finally:
            self.session.close()


# Función auxiliar para obtener la ruta de la base de datos
def get_database_path():
    """
    Retorna la ruta completa al archivo de base de datos SQLite3.

    Returns:
        str: Ruta completa al archivo mine_bot.db
    """
    return DATABASE_PATH
