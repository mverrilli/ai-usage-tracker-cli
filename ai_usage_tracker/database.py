"""
Database module for AI Usage Tracker
Handles SQLite database creation and management
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

class Database:
    """SQLite database manager for usage tracking"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            # Default location
            self.db_path = str(Path.home() / ".local" / "share" / "ai-usage-tracker" / "usage.db")
        else:
            self.db_path = os.path.expanduser(db_path)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect to the database"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        # Enable foreign keys
        self.cursor.execute("PRAGMA foreign_keys = ON")
        return self.conn
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def create_tables(self):
        """Create all database tables if they don't exist"""
        self.connect()
        
        # 1. providers table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            base_url TEXT,
            api_key_hash TEXT,
            config_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 2. models table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_id INTEGER NOT NULL,
            model_id TEXT NOT NULL,
            name TEXT NOT NULL,
            context_window INTEGER,
            max_tokens INTEGER,
            input_cost REAL,
            output_cost REAL,
            cache_read_cost REAL,
            cache_write_cost REAL,
            supports_images BOOLEAN DEFAULT FALSE,
            supports_reasoning BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (provider_id) REFERENCES providers(id),
            UNIQUE(provider_id, model_id)
        )
        """)
        
        # 3. sessions table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_key TEXT NOT NULL UNIQUE,
            session_id TEXT,
            source TEXT,
            channel TEXT,
            user_id TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            total_tokens INTEGER DEFAULT 0,
            total_cost REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 4. usage_entries table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            model_id INTEGER NOT NULL,
            request_id TEXT,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            cache_read_tokens INTEGER DEFAULT 0,
            cache_write_tokens INTEGER DEFAULT 0,
            input_cost REAL DEFAULT 0.0,
            output_cost REAL DEFAULT 0.0,
            cache_read_cost REAL DEFAULT 0.0,
            cache_write_cost REAL DEFAULT 0.0,
            total_cost REAL DEFAULT 0.0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id),
            FOREIGN KEY (model_id) REFERENCES models(id)
        )
        """)
        
        # 5. budgets table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_id INTEGER,
            model_id INTEGER,
            period TEXT NOT NULL,
            amount REAL NOT NULL,
            alert_threshold REAL DEFAULT 0.8,
            enabled BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (provider_id) REFERENCES providers(id),
            FOREIGN KEY (model_id) REFERENCES models(id)
        )
        """)
        
        # 6. alerts table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            budget_id INTEGER NOT NULL,
            alert_type TEXT NOT NULL,
            current_usage REAL NOT NULL,
            current_budget REAL NOT NULL,
            percentage REAL NOT NULL,
            triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            acknowledged BOOLEAN DEFAULT FALSE,
            acknowledged_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (budget_id) REFERENCES budgets(id)
        )
        """)
        
        # Create indexes for performance
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_entries_timestamp ON usage_entries(timestamp)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_entries_session_id ON usage_entries(session_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_entries_model_id ON usage_entries(model_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON sessions(started_at)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_session_key ON sessions(session_key)")
        
        # Create triggers for updated_at
        self.cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_providers_timestamp 
        AFTER UPDATE ON providers
        BEGIN
            UPDATE providers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
        """)
        
        self.cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_models_timestamp 
        AFTER UPDATE ON models
        BEGIN
            UPDATE models SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
        """)
        
        self.cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_budgets_timestamp 
        AFTER UPDATE ON budgets
        BEGIN
            UPDATE budgets SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
        """)
        
        self.conn.commit()
        self.close()
        
        return True
    
    def get_table_info(self):
        """Get information about all tables"""
        self.connect()
        
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = self.cursor.fetchall()
        
        result = []
        for table in tables:
            table_name = table[0]
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = self.cursor.fetchone()[0]
            result.append({"name": table_name, "row_count": count})
        
        self.close()
        return result
    
    def initialize(self):
        """Initialize the database with default data"""
        print(f"Initializing database at: {self.db_path}")
        
        # Create tables
        self.create_tables()
        
        # Add default providers and models
        self._add_default_providers()
        
        # Create default budgets
        self._create_default_budgets()
        
        # Show table info
        tables = self.get_table_info()
        print(f"\nDatabase initialized with {len(tables)} tables:")
        for table in tables:
            print(f"  - {table['name']}: {table['row_count']} rows")
        
        return True
    
    def _add_default_providers(self):
        """Add default AI providers and models"""
        self.connect()
        
        # Default providers data
        providers = [
            {
                "name": "openai",
                "models": [
                    {"model_id": "gpt-4o", "name": "GPT-4o", "input_cost": 0.005, "output_cost": 0.015},
                    {"model_id": "gpt-4o-mini", "name": "GPT-4o-mini", "input_cost": 0.0015, "output_cost": 0.006},
                    {"model_id": "o1-mini", "name": "o1-mini", "input_cost": 0.003, "output_cost": 0.012},
                    {"model_id": "o1-preview", "name": "o1-preview", "input_cost": 0.015, "output_cost": 0.06},
                ]
            },
            {
                "name": "anthropic",
                "models": [
                    {"model_id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "input_cost": 0.003, "output_cost": 0.015},
                    {"model_id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "input_cost": 0.00025, "output_cost": 0.00125},
                ]
            },
            {
                "name": "google",
                "models": [
                    {"model_id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "input_cost": 0.0001, "output_cost": 0.0004},
                    {"model_id": "gemini-2.0-pro", "name": "Gemini 2.0 Pro", "input_cost": 0.0025, "output_cost": 0.01},
                ]
            },
            {
                "name": "deepseek",
                "models": [
                    {"model_id": "deepseek-chat", "name": "DeepSeek Chat", "input_cost": 0.00014, "output_cost": 0.00028},
                    {"model_id": "deepseek-reasoner", "name": "DeepSeek Reasoner", "input_cost": 0.0014, "output_cost": 0.0028},
                ]
            }
        ]
        
        for provider_data in providers:
            # Insert provider
            self.cursor.execute("""
            INSERT OR IGNORE INTO providers (name, config_json)
            VALUES (?, ?)
            """, (provider_data["name"], json.dumps({"source": "default"})))
            
            provider_id = self.cursor.lastrowid
            if provider_id == 0:
                # Provider already exists, get its ID
                self.cursor.execute("SELECT id FROM providers WHERE name = ?", (provider_data["name"],))
                provider_id = self.cursor.fetchone()[0]
            
            # Insert models
            for model_data in provider_data["models"]:
                self.cursor.execute("""
                INSERT OR IGNORE INTO models 
                (provider_id, model_id, name, input_cost, output_cost)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    provider_id,
                    model_data["model_id"],
                    model_data["name"],
                    model_data["input_cost"],
                    model_data["output_cost"]
                ))
        
        self.conn.commit()
        self.close()
    
    def _create_default_budgets(self):
        """Create default budget configurations"""
        self.connect()
        
        # Get all provider IDs
        self.cursor.execute("SELECT id FROM providers")
        provider_ids = [row[0] for row in self.cursor.fetchall()]
        
        for provider_id in provider_ids:
            # Daily budget: $10
            self.cursor.execute("""
            INSERT OR IGNORE INTO budgets (provider_id, period, amount, alert_threshold)
            VALUES (?, 'daily', 10.0, 0.8)
            """, (provider_id,))
            
            # Monthly budget: $100
            self.cursor.execute("""
            INSERT OR IGNORE INTO budgets (provider_id, period, amount, alert_threshold)
            VALUES (?, 'monthly', 100.0, 0.9)
            """, (provider_id,))
        
        # Global daily budget: $20
        self.cursor.execute("""
        INSERT OR IGNORE INTO budgets (provider_id, period, amount, alert_threshold)
        VALUES (NULL, 'daily', 20.0, 0.8)
        """)
        
        # Global monthly budget: $200
        self.cursor.execute("""
        INSERT OR IGNORE INTO budgets (provider_id, period, amount, alert_threshold)
        VALUES (NULL, 'monthly', 200.0, 0.9)
        """)
        
        self.conn.commit()
        self.close()