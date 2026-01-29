"""
Parser module for AI Usage Tracker
Parses Clawdbot session logs to extract usage data
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Dict, List, Optional, Tuple

class SessionParser:
    """Parser for Clawdbot session logs"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Connect to database"""
        if self.db_path:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
        return self.conn
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def parse_session_file(self, file_path: str, incremental: bool = True, 
                          last_processed_line: int = 0) -> Tuple[int, List[Dict]]:
        """
        Parse a session JSONL file
        
        Args:
            file_path: Path to session file
            incremental: Whether to parse incrementally
            last_processed_line: Last line processed (for incremental parsing)
            
        Returns:
            Tuple of (entries_processed, list of usage entries)
        """
        if not os.path.exists(file_path):
            return 0, []
        
        entries = []
        current_line = 0
        entries_processed = 0
        
        try:
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    # Skip already processed lines for incremental parsing
                    if incremental and line_num <= last_processed_line:
                        continue
                    
                    current_line = line_num
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        usage_entry = self._extract_usage_from_line(data)
                        
                        if usage_entry:
                            entries.append(usage_entry)
                            entries_processed += 1
                            
                    except json.JSONDecodeError as e:
                        print(f"  Line {line_num}: JSON decode error: {e}")
                        continue
                    except Exception as e:
                        print(f"  Line {line_num}: Error processing: {e}")
                        continue
                        
        except Exception as e:
            print(f"  Error reading file {file_path}: {e}")
        
        return entries_processed, entries
    
    def _extract_usage_from_line(self, data: Dict) -> Optional[Dict]:
        """
        Extract usage data from a session log line
        
        Args:
            data: Parsed JSON data from session log
            
        Returns:
            Usage entry dict or None if no usage data
        """
        # Check if this is a message with usage data
        if data.get('type') != 'message':
            return None
        
        message = data.get('message', {})
        
        # Check if this is an assistant message with usage data
        if message.get('role') != 'assistant':
            return None
        
        # Look for usage data in different possible locations
        usage_data = None
        
        # Check for usage in message.usage
        if 'usage' in message:
            usage_data = message['usage']
        
        # Check for usage in message.metadata
        elif 'metadata' in message and 'usage' in message['metadata']:
            usage_data = message['metadata']['usage']
        
        # Check for usage in custom fields
        elif 'custom' in message and 'usage' in message['custom']:
            usage_data = message['custom']['usage']
        
        if not usage_data:
            return None
        
        # Extract provider and model
        provider = message.get('provider')
        model = message.get('model')
        
        # If not in message, check metadata
        if not provider and 'metadata' in message:
            metadata = message['metadata']
            provider = metadata.get('provider')
            model = metadata.get('model')
        
        # If still not found, try to extract from model field
        if not provider and model:
            # Try to infer provider from model name
            provider = self._infer_provider_from_model(model)
        
        # Extract token counts
        input_tokens = usage_data.get('input_tokens', 0)
        output_tokens = usage_data.get('output_tokens', 0)
        total_tokens = usage_data.get('total_tokens', 0)
        
        # If total_tokens is not provided, calculate it
        if total_tokens == 0 and (input_tokens > 0 or output_tokens > 0):
            total_tokens = input_tokens + output_tokens
        
        # Extract costs if available
        input_cost = usage_data.get('input_cost', 0.0)
        output_cost = usage_data.get('output_cost', 0.0)
        total_cost = usage_data.get('total_cost', 0.0)
        
        # If total_cost is not provided, we'll calculate it later
        if total_cost == 0.0 and (input_cost > 0 or output_cost > 0):
            total_cost = input_cost + output_cost
        
        # Get timestamp
        timestamp = data.get('timestamp')
        if not timestamp:
            timestamp = datetime.now().isoformat()
        
        # Create usage entry
        entry = {
            'session_id': data.get('id'),
            'provider': provider,
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': total_cost,
            'timestamp': timestamp,
            'raw_data': json.dumps(data)  # Store raw data for debugging
        }
        
        return entry
    
    def _infer_provider_from_model(self, model: str) -> str:
        """
        Infer provider from model name
        
        Args:
            model: Model name or ID
            
        Returns:
            Inferred provider name
        """
        model_lower = model.lower()
        
        # OpenAI models
        if any(prefix in model_lower for prefix in ['gpt-', 'o1-', 'text-', 'dall-e']):
            return 'openai'
        
        # Anthropic models
        elif any(prefix in model_lower for prefix in ['claude-', 'anthropic']):
            return 'anthropic'
        
        # Google models
        elif any(prefix in model_lower for prefix in ['gemini-', 'palm-', 'google']):
            return 'google'
        
        # DeepSeek models
        elif any(prefix in model_lower for prefix in ['deepseek-']):
            return 'deepseek'
        
        # Cohere models
        elif any(prefix in model_lower for prefix in ['command-', 'cohere']):
            return 'cohere'
        
        # Mistral models
        elif any(prefix in model_lower for prefix in ['mistral-', 'mixtral']):
            return 'mistral'
        
        # Default to unknown
        return 'unknown'
    
    def save_usage_entries(self, entries: List[Dict]) -> int:
        """
        Save usage entries to database
        
        Args:
            entries: List of usage entry dicts
            
        Returns:
            Number of entries saved
        """
        if not entries:
            return 0
        
        if not self.conn:
            self.connect()
        
        if not self.conn:
            print("Error: Could not connect to database")
            return 0
        
        saved_count = 0
        
        for entry in entries:
            try:
                # Get or create provider
                provider_id = self._get_or_create_provider(entry['provider'])
                
                # Get or create model
                model_id = self._get_or_create_model(provider_id, entry['model'])
                
                # Get or create session
                session_id = self._get_or_create_session(entry.get('session_id'), entry['timestamp'])
                
                # Calculate costs if not provided
                input_cost = entry['input_cost']
                output_cost = entry['output_cost']
                total_cost = entry['total_cost']
                
                if total_cost == 0.0 and (entry['input_tokens'] > 0 or entry['output_tokens'] > 0):
                    # Try to get model pricing from database
                    model_pricing = self._get_model_pricing(model_id)
                    if model_pricing:
                        input_cost = entry['input_tokens'] * model_pricing['input_cost']
                        output_cost = entry['output_tokens'] * model_pricing['output_cost']
                        total_cost = input_cost + output_cost
                
                # Insert usage entry
                self.cursor.execute("""
                INSERT INTO usage_entries 
                (session_id, model_id, input_tokens, output_tokens, 
                 cache_read_tokens, cache_write_tokens, input_cost, output_cost,
                 cache_read_cost, cache_write_cost, total_cost, timestamp, metadata_json)
                VALUES (?, ?, ?, ?, 0, 0, ?, ?, 0, 0, ?, ?, ?)
                """, (
                    session_id,
                    model_id,
                    entry['input_tokens'],
                    entry['output_tokens'],
                    input_cost,
                    output_cost,
                    total_cost,
                    entry['timestamp'],
                    entry['raw_data']
                ))
                
                saved_count += 1
                
            except Exception as e:
                print(f"Error saving entry: {e}")
                continue
        
        self.conn.commit()
        return saved_count
    
    def _get_or_create_provider(self, provider_name: str) -> int:
        """Get or create provider in database"""
        if not provider_name:
            provider_name = 'unknown'
        
        # Check if provider exists
        self.cursor.execute("SELECT id FROM providers WHERE name = ?", (provider_name,))
        result = self.cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create new provider
        self.cursor.execute("""
        INSERT INTO providers (name, config_json)
        VALUES (?, ?)
        """, (provider_name, json.dumps({"source": "parsed_from_session"})))
        
        return self.cursor.lastrowid
    
    def _get_or_create_model(self, provider_id: int, model_name: str) -> int:
        """Get or create model in database"""
        if not model_name:
            model_name = 'unknown'
        
        # Create model_id from name (simplified)
        model_id = re.sub(r'[^a-zA-Z0-9_-]', '-', model_name.lower())
        
        # Check if model exists
        self.cursor.execute("""
        SELECT id FROM models 
        WHERE provider_id = ? AND model_id = ?
        """, (provider_id, model_id))
        
        result = self.cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create new model
        self.cursor.execute("""
        INSERT INTO models (provider_id, model_id, name)
        VALUES (?, ?, ?)
        """, (provider_id, model_id, model_name))
        
        return self.cursor.lastrowid
    
    def _get_or_create_session(self, session_key: Optional[str], timestamp: str) -> int:
        """Get or create session in database"""
        if not session_key:
            # Generate a session key from timestamp
            session_key = f"session-{hash(timestamp) % 1000000}"
        
        # Check if session exists
        self.cursor.execute("SELECT id FROM sessions WHERE session_key = ?", (session_key,))
        result = self.cursor.fetchone()
        
        if result:
            return result[0]
        
        # Parse timestamp
        try:
            started_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            started_at = datetime.now()
        
        # Create new session
        self.cursor.execute("""
        INSERT INTO sessions (session_key, started_at)
        VALUES (?, ?)
        """, (session_key, started_at.isoformat()))
        
        return self.cursor.lastrowid
    
    def _get_model_pricing(self, model_id: int) -> Optional[Dict]:
        """Get model pricing from database"""
        self.cursor.execute("""
        SELECT input_cost, output_cost 
        FROM models 
        WHERE id = ?
        """, (model_id,))
        
        result = self.cursor.fetchone()
        if result and result[0] is not None and result[1] is not None:
            return {'input_cost': result[0], 'output_cost': result[1]}
        
        return None
    
    def parse_directory(self, directory_path: str, recursive: bool = True) -> Tuple[int, int]:
        """
        Parse all session files in a directory
        
        Args:
            directory_path: Path to directory containing session files
            recursive: Whether to search recursively
            
        Returns:
            Tuple of (files_processed, entries_processed)
        """
        if not os.path.exists(directory_path):
            print(f"Directory not found: {directory_path}")
            return 0, 0
        
        files_processed = 0
        total_entries = 0
        
        # Find session files
        pattern = "*.jsonl"
        if recursive:
            session_files = list(Path(directory_path).rglob(pattern))
        else:
            session_files = list(Path(directory_path).glob(pattern))
        
        print(f"Found {len(session_files)} session files")
        
        for session_file in session_files:
            print(f"Processing: {session_file}")
            
            entries_processed, entries = self.parse_session_file(str(session_file))
            
            if entries:
                saved = self.save_usage_entries(entries)
                print(f"  Saved {saved} usage entries")
                total_entries += saved
            
            files_processed += 1
        
        return files_processed, total_entries