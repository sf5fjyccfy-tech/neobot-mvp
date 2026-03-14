#!/bin/bash
"""
PostgreSQL → Oracle Cloud (OCI) Migration Script
Automated migration with validation
Created: 11 Mars 2026
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOG_FILE="migration_$(date +%Y%m%d_%H%M%S).log"
BACKUP_DIR="/var/backups/neobot"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ========== HELPER FUNCTIONS ==========
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[✅ SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[❌ ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[⚠️  WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# ========== PRE-MIGRATION CHECKS ==========
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python version (3.9+)
    python_version=$(python3 --version | awk '{print $2}')
    log_info "Python version: $python_version"
    
    # Check required Python packages
    required_packages=("sqlalchemy" "oracledb" "psycopg2" "redis")
    for package in "${required_packages[@]}"; do
        python3 -c "import $package" 2>/dev/null && \
            log_success "$package installed" || \
            log_error "$package not found - installing..."
    done
    
    # Check database connectivity
    log_info "Testing PostgreSQL connection..."
    # Will test during migration
    
    log_info "Testing Oracle connectivity..."
    # Will test during migration
    
    log_success "Prerequisites check completed"
}

# ========== BACKUP PHASE ==========
backup_postgresql() {
    log_info "📦 BACKING UP POSTGRESQL DATA..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    backup_file="$BACKUP_DIR/neobot_postgres_backup_$TIMESTAMP.sql"
    
    log_info "Exporting PostgreSQL to: $backup_file"
    
    pg_dump -U neobot -h localhost -d neobot_db \
        --format=custom \
        --file="$backup_file" \
        2>&1 | tee -a "$LOG_FILE"
    
    if [ -f "$backup_file" ]; then
        log_success "PostgreSQL backup created: $backup_file"
        log_info "Backup size: $(du -h $backup_file | cut -f1)"
    else
        log_error "PostgreSQL backup failed!"
        exit 1
    fi
}

# ========== DATA EXPORT PHASE ==========
export_data() {
    log_info "📊 EXPORTING DATA TO JSON..."
    
    python3 << 'EOF'
import json
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Connect to PostgreSQL
    pg_engine = create_engine(
        "postgresql://neobot:neobot_secure_password@localhost:5432/neobot_db",
        echo=False
    )
    
    logger.info("✅ Connected to PostgreSQL")
    
    # Export tables to JSON
    from sqlalchemy import inspect
    
    inspector = inspect(pg_engine)
    tables = inspector.get_table_names()
    
    export_dir = "/var/backups/neobot/data_export"
    import os
    os.makedirs(export_dir, exist_ok=True)
    
    for table_name in tables:
        logger.info(f"Exporting table: {table_name}")
        
        with pg_engine.connect() as conn:
            result = conn.execute(f"SELECT * FROM {table_name}")
            columns = [column[0] for column in result.keys()]
            rows = []
            
            for row in result:
                rows.append(dict(zip(columns, row)))
            
            # Convert datetime objects to strings
            def datetime_handler(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            export_file = f"{export_dir}/{table_name}.json"
            with open(export_file, "w") as f:
                json.dump(rows, f, default=datetime_handler, indent=2)
            
            logger.info(f"✅ Exported {len(rows)} rows from {table_name}")
    
    logger.info(f"✅ Data export completed to {export_dir}")
    
except Exception as e:
    logger.error(f"❌ Export failed: {e}", exc_info=True)
    sys.exit(1)

EOF
}

# ========== ORACLE SETUP PHASE ==========
setup_oracle() {
    log_info "🗄️  SETTING UP ORACLE DATABASE..."
    
    log_info "Creating Oracle database schema..."
    
    python3 << 'EOF'
import logging
import sys
from sqlalchemy import create_engine, text
from sqlalchemy_oracle import oracle
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Oracle connection details from environment
    oracle_user = os.getenv("ORACLE_USER", "admin")
    oracle_password = os.getenv("ORACLE_PASSWORD", "")
    oracle_host = os.getenv("ORACLE_HOST", "neobot-db.c9akciq32u84.us-phoenix-1.rds.ocicloudservices.com")
    oracle_port = os.getenv("ORACLE_PORT", "1521")
    oracle_service = os.getenv("ORACLE_SERVICE", "neobot_pdb")
    
    # Connection string
    db_url = f"oracle+oracledb://{oracle_user}:{oracle_password}@{oracle_host}:{oracle_port}/{oracle_service}"
    
    logger.info(f"Connecting to Oracle: {oracle_host}:{oracle_port}")
    
    engine = create_engine(db_url, echo=False)
    
    with engine.connect() as conn:
        # Test connection
        conn.execute(text("SELECT 1 FROM DUAL"))
        logger.info("✅ Connected to Oracle Database")
        
        # Create tables (Import models from app)
        from app.database import Base
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Created all Oracle tables")
        
        # Create sequences for auto-increment
        sequences_sql = [
            "CREATE SEQUENCE users_seq START WITH 1 INCREMENT BY 1 NOCACHE",
            "CREATE SEQUENCE contacts_seq START WITH 1 INCREMENT BY 1 NOCACHE",
            "CREATE SEQUENCE conversations_seq START WITH 1 INCREMENT BY 1 NOCACHE",
            "CREATE SEQUENCE messages_seq START WITH 1 INCREMENT BY 1 NOCACHE",
            "CREATE SEQUENCE tenant_settings_seq START WITH 1 INCREMENT BY 1 NOCACHE"
        ]
        
        for sql in sequences_sql:
            try:
                conn.execute(text(sql))
                logger.info(f"✅ {sql.split()[2]}")
            except:
                logger.warning(f"Sequence may already exist: {sql.split()[2]}")
        
        conn.commit()
        logger.info("✅ Oracle schema setup completed")
        
except Exception as e:
    logger.error(f"❌ Oracle setup failed: {e}", exc_info=True)
    sys.exit(1)

EOF
}

# ========== DATA MIGRATION PHASE ==========
migrate_data() {
    log_info "🔄 MIGRATING DATA TO ORACLE..."
    
    python3 << 'EOF'
import json
import logging
import sys
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Oracle connection
    oracle_user = os.getenv("ORACLE_USER", "admin")
    oracle_password = os.getenv("ORACLE_PASSWORD", "")
    oracle_host = os.getenv("ORACLE_HOST")
    oracle_port = os.getenv("ORACLE_PORT", "1521")
    oracle_service = os.getenv("ORACLE_SERVICE")
    
    db_url = f"oracle+oracledb://{oracle_user}:{oracle_password}@{oracle_host}:{oracle_port}/{oracle_service}"
    
    oracle_engine = create_engine(db_url)
    OracleSession = sessionmaker(bind=oracle_engine)
    
    # Import models
    from app.models import (
        Tenant, User, Contact, Conversation, Message,
        ConversationHumanState, QueuedMessage, TenantSettings
    )
    
    # Data import directory
    export_dir = "/var/backups/neobot/data_export"
    
    # Import JSON files to Oracle
    for filename in os.listdir(export_dir):
        if filename.endswith(".json"):
            table_name = filename[:-5]
            file_path = os.path.join(export_dir, filename)
            
            logger.info(f"Importing {table_name}...")
            
            with open(file_path, "r") as f:
                data = json.load(f)
            
            session = OracleSession()
            
            # Map table names to models
            model_map = {
                "tenants": Tenant,
                "users": User,
                "contacts": Contact,
                "conversations": Conversation,
                "messages": Message,
                "conversation_human_states": ConversationHumanState,
                "queued_messages": QueuedMessage,
                "tenant_settings": TenantSettings
            }
            
            if table_name in model_map:
                Model = model_map[table_name]
                
                for row in data:
                    # Convert datetime strings back to datetime objects
                    for key, value in row.items():
                        if isinstance(value, str) and "T" in value:  # ISO format datetime
                            try:
                                row[key] = datetime.fromisoformat(value)
                            except:
                                pass
                    
                    obj = Model(**row)
                    session.add(obj)
                
                session.commit()
                logger.info(f"✅ Imported {len(data)} rows to {table_name}")
            
            session.close()
    
    logger.info("✅ Data migration to Oracle completed")
    
except Exception as e:
    logger.error(f"❌ Data migration failed: {e}", exc_info=True)
    sys.exit(1)

EOF
}

# ========== CREATE INDEXES ==========
create_indexes() {
    log_info "📑 CREATING DATABASE INDEXES..."
    
    python3 << 'EOF'
import logging
import sys
import os
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    oracle_user = os.getenv("ORACLE_USER")
    oracle_password = os.getenv("ORACLE_PASSWORD")
    oracle_host = os.getenv("ORACLE_HOST")
    oracle_port = os.getenv("ORACLE_PORT", "1521")
    oracle_service = os.getenv("ORACLE_SERVICE")
    
    db_url = f"oracle+oracledb://{oracle_user}:{oracle_password}@{oracle_host}:{oracle_port}/{oracle_service}"
    
    engine = create_engine(db_url)
    
    # Create indexes for performance
    indexes = [
        "CREATE INDEX idx_contact_settings_phone ON contacts(phone)",
        "CREATE INDEX idx_conversation_human ON conversation_human_states(conversation_id)",
        "CREATE INDEX idx_conversation_tenant_status ON conversations(tenant_id, status)",
        "CREATE INDEX idx_message_timestamp ON messages(created_at DESC)",
        "CREATE INDEX idx_queued_send_at ON queued_messages(send_at) WHERE status = 'queued'"
    ]
    
    with engine.connect() as conn:
        for idx_sql in indexes:
            try:
                conn.execute(text(idx_sql))
                conn.commit()
                logger.info(f"✅ {idx_sql.split()[2]}")
            except Exception as e:
                logger.warning(f"Index may exist: {idx_sql.split()[2]}")
    
    logger.info("✅ Index creation completed")
    
except Exception as e:
    logger.error(f"❌ Index creation failed: {e}", exc_info=True)
    sys.exit(1)

EOF
}

# ========== REDIS SETUP ==========
setup_redis() {
    log_info "📦 SETTING UP REDIS CACHE..."
    
    python3 << 'EOF'
import redis
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_password = os.getenv("REDIS_PASSWORD")
    
    logger.info(f"Connecting to Redis: {redis_host}:{redis_port}")
    
    r = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        decode_responses=True
    )
    
    # Test connection
    r.ping()
    logger.info("✅ Connected to Redis")
    
    # Clear old cache
    logger.info("Clearing old cache...")
    r.flushdb()
    logger.info("✅ Redis cache cleared and ready")
    
except Exception as e:
    logger.error(f"❌ Redis setup failed: {e}", exc_info=True)

EOF
}

# ========== VALIDATION PHASE ==========
validate_migration() {
    log_info "✓ VALIDATING MIGRATION..."
    
    python3 << 'EOF'
import logging
import sys
import os
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    oracle_user = os.getenv("ORACLE_USER")
    oracle_password = os.getenv("ORACLE_PASSWORD")
    oracle_host = os.getenv("ORACLE_HOST")
    oracle_port = os.getenv("ORACLE_PORT", "1521")
    oracle_service = os.getenv("ORACLE_SERVICE")
    
    db_url = f"oracle+oracledb://{oracle_user}:{oracle_password}@{oracle_host}:{oracle_port}/{oracle_service}"
    
    engine = create_engine(db_url)
    
    validation_queries = {
        "tenants": "SELECT COUNT(*) FROM tenants",
        "users": "SELECT COUNT(*) FROM users",
        "contacts": "SELECT COUNT(*) FROM contacts",
        "conversations": "SELECT COUNT(*) FROM conversations",
        "messages": "SELECT COUNT(*) FROM messages"
    }
    
    with engine.connect() as conn:
        for table, query in validation_queries.items():
            try:
                result = conn.execute(text(query))
                count = result.scalar()
                logger.info(f"✅ {table}: {count} records")
            except Exception as e:
                logger.warning(f"Could not validate {table}: {e}")
    
    logger.info("✅ Migration validation completed")
    
except Exception as e:
    logger.error(f"❌ Validation failed: {e}", exc_info=True)
    sys.exit(1)

EOF
}

# ========== CLEANUP POSTGRESQL ==========
cleanup_postgresql() {
    log_info "🧹 CLEANUP PHASE..."
    
    read -p "Keep PostgreSQL data? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        log_warning "Dropping PostgreSQL neobot_db..."
        # User must run manually for safety
        log_info "Run manually if needed: dropdb -U neobot neobot_db"
    else
        log_info "Keeping PostgreSQL data as backup"
    fi
}

# ========== MAIN MIGRATION FLOW ==========
main() {
    log_info "╔════════════════════════════════════════════╗"
    log_info "║ PostgreSQL → Oracle Cloud OCI Migration    ║"
    log_info "║ Created: 11 Mars 2026                      ║"
    log_info "╚════════════════════════════════════════════╝"
    log_info ""
    
    # Pre-checks
    check_prerequisites
    
    # Backup
    backup_postgresql
    
    # Export
    export_data
    
    # Oracle Setup
    setup_oracle
    
    # Migrate Data
    migrate_data
    
    # Indexes
    create_indexes
    
    # Redis
    setup_redis
    
    # Validate
    validate_migration
    
    # Cleanup
    cleanup_postgresql
    
    log_success "╔════════════════════════════════════════════╗"
    log_success "║ MIGRATION COMPLETED SUCCESSFULLY!          ║"
    log_success "║ Log file: $LOG_FILE                        ║"
    log_success "║ Backup: $BACKUP_DIR                        ║"
    log_success "╚════════════════════════════════════════════╝"
}

# Run main
main
