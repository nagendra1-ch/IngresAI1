import os
import sys
import time
import argparse
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import Base
from app.models import (
    User, Geography, GeographyAlias, GWRAAssessment,
    GroundwaterObservation, RainfallRecord, QueryHistory,
    ResultAccess, Conversation, ConversationMessage
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("db_migrator")

TABLE_ORDER = [
    ("users", User),
    ("geographies", Geography),
    ("geography_aliases", GeographyAlias),
    ("gwra_assessments", GWRAAssessment),
    ("rainfall_records", RainfallRecord),
    ("groundwater_observations", GroundwaterObservation),
    ("query_history", QueryHistory),
    ("result_access", ResultAccess),
    ("conversations", Conversation),
    ("conversation_messages", ConversationMessage)
]

def find_sqlite_db():
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ingres_ai.db")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ingres_ai.db")),
        os.path.abspath("ingres_ai.db"),
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.getsize(c) > 0:
            return c
    return None

def migrate(source_url: str, target_url: str, batch_size: int = 5000, limit_obs: int = None, tables_to_migrate: list = None):
    # Normalize Postgres URL
    if target_url.startswith("postgres://"):
        target_url = target_url.replace("postgres://", "postgresql://", 1)

    logger.info(f"Source DB: {source_url}")
    logger.info(f"Target DB: {target_url.split('@')[-1] if '@' in target_url else target_url}")

    # Create engines
    source_engine = create_engine(source_url, connect_args={"check_same_thread": False} if "sqlite" in source_url else {})
    target_engine = create_engine(target_url, pool_pre_ping=True)

    # Verify target connection
    logger.info("Connecting to target database...")
    with target_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Connection to target database established successfully!")

    # Create schema on target
    logger.info("Creating tables on target database if not exist...")
    Base.metadata.create_all(bind=target_engine)
    logger.info("Schema synchronization complete.")

    SourceSession = sessionmaker(bind=source_engine)
    TargetSession = sessionmaker(bind=target_engine)

    src_db = SourceSession()
    tgt_db = TargetSession()

    try:
        for table_name, model_class in TABLE_ORDER:
            if tables_to_migrate and table_name not in tables_to_migrate:
                logger.info(f"Skipping table '{table_name}' (not in selected tables).")
                continue

            total_count = src_db.query(model_class).count()
            target_count = tgt_db.query(model_class).count()
            logger.info(f"--- Table [{table_name}]: Source has {total_count:,} rows (Target has {target_count:,}) ---")

            if total_count == 0:
                continue

            if target_count >= total_count:
                logger.info(f"Table [{table_name}] already has {target_count:,} rows. Skipping...")
                continue

            # Handle observations limit if specified
            max_to_sync = total_count
            if table_name == "groundwater_observations" and limit_obs and limit_obs < total_count:
                max_to_sync = limit_obs
                logger.info(f"Limiting groundwater_observations migration to {limit_obs:,} rows.")

            offset = 0
            inserted = 0
            start_time = time.time()

            while offset < max_to_sync:
                limit = min(batch_size, max_to_sync - offset)
                records = src_db.query(model_class).offset(offset).limit(limit).all()
                if not records:
                    break

                batch_dicts = []
                for rec in records:
                    d = {c.name: getattr(rec, c.name) for c in model_class.__table__.columns}
                    batch_dicts.append(d)

                # Bulk insert into target
                tgt_db.bulk_insert_mappings(model_class, batch_dicts)
                tgt_db.commit()

                inserted += len(batch_dicts)
                offset += limit

                elapsed = time.time() - start_time
                rate = inserted / elapsed if elapsed > 0 else 0
                logger.info(f"  [{table_name}] Progress: {inserted:,}/{max_to_sync:,} rows ({(inserted/max_to_sync)*100:.1f}%) - {rate:.0f} rows/sec")

            logger.info(f"Successfully migrated {inserted:,} rows for [{table_name}].")

    except Exception as e:
        logger.error(f"Migration error: {e}", exc_info=True)
        tgt_db.rollback()
        raise
    finally:
        src_db.close()
        tgt_db.close()

    logger.info("All data migration completed successfully!")

def main():
    parser = argparse.ArgumentParser(description="Migrate local SQLite DB data to free online database (Neon, Supabase, Render, etc.)")
    parser.add_argument("--source", type=str, default=None, help="Source SQLite database URL (defaults to auto-detected ingres_ai.db)")
    parser.add_argument("--target", type=str, default=None, help="Target Online Database URL (defaults to DATABASE_URL in .env)")
    parser.add_argument("--batch-size", type=int, default=5000, help="Batch size for bulk insertion (default: 5000)")
    parser.add_argument("--limit-obs", type=int, default=None, help="Limit number of groundwater observations to migrate")
    parser.add_argument("--tables", type=str, default=None, help="Comma-separated list of tables to migrate")
    args = parser.parse_args()

    # Determine source URL
    source_url = args.source
    if not source_url:
        sqlite_file = find_sqlite_db()
        if not sqlite_file:
            logger.error("Could not find local ingres_ai.db file. Specify with --source sqlite:///path/to/db")
            sys.exit(1)
        source_url = f"sqlite:///{sqlite_file.replace(os.sep, '/')}"

    # Determine target URL
    target_url = args.target or settings.DATABASE_URL
    if not target_url or target_url.startswith("sqlite"):
        if not args.target:
            logger.warning("Target DATABASE_URL in .env is currently pointing to SQLite.")
            logger.info("Please set DATABASE_URL in backend/.env to your online database URL (e.g., Neon or Supabase PostgreSQL), or pass --target 'postgresql://...'")
            print("\nExample Neon connection string:")
            print("  python scripts/migrate_to_online_db.py --target 'postgresql://neondb_owner:pwd@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require'\n")
            sys.exit(0)

    tables = [t.strip() for t in args.tables.split(",")] if args.tables else None

    migrate(
        source_url=source_url,
        target_url=target_url,
        batch_size=args.batch_size,
        limit_obs=args.limit_obs,
        tables_to_migrate=tables
    )

if __name__ == "__main__":
    main()
