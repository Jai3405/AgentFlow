#!/usr/bin/env python
"""
Database initialization script for AgentFlow
Creates all tables and runs migrations
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.base import Base, engine
from database.models import ConversationDB, MessageDB, WorkflowDB

def init_database():
    """Initialize database tables"""
    print("Creating database tables...")

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully!")

        # Print created tables
        print("\nCreated tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")

    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database()
