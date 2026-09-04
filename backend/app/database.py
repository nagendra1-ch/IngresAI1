import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from app.config import settings

logger = logging.getLogger(__name__)

# Normalize DATABASE_URL for SQLAlchemy 2.0 (e.g., postgres:// -> postgresql://)
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Configure engine arguments based on database type
engine_kwargs = {}
if db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Check if running in serverless environment (e.g., Vercel / AWS Lambda)
    is_serverless = os.environ.get("VERCEL") == "1" or os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None
    if is_serverless:
        engine_kwargs["poolclass"] = NullPool
    else:
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = 300
        engine_kwargs["pool_size"] = 5
        engine_kwargs["max_overflow"] = 5
        engine_kwargs["pool_timeout"] = 10

engine = create_engine(db_url, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Create all database tables and performance indexes if they do not exist."""
    try:
        Base.metadata.create_all(bind=engine)
        # Create additional performance indexes on PostgreSQL / SQLite
        with engine.connect() as conn:
            from sqlalchemy import text
            indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_obs_geo_year ON groundwater_observations (geography_id, observation_year);",
                "CREATE INDEX IF NOT EXISTS idx_rain_geo_year ON rainfall_records (geography_id, rainfall_year);",
                "CREATE INDEX IF NOT EXISTS idx_gwra_geo_year ON gwra_assessments (geography_id, assessment_year);",
                "CREATE INDEX IF NOT EXISTS idx_result_access_geo_user ON result_access (geography_id, user_id);",
                "CREATE INDEX IF NOT EXISTS idx_query_history_user ON query_history (user_id, created_at);"
            ]
            for idx_stmt in indexes_sql:
                try:
                    conn.execute(text(idx_stmt))
                    conn.commit()
                except Exception:
                    pass
        logger.info("Database schema & performance indexes initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database schema: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

