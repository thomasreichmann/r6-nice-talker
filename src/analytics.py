"""
Usage analytics and cost tracking system.
Tracks API calls, TTS usage, OCR processing, and calculates costs.
"""
import sqlite3
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from src.config import Config

logger = logging.getLogger(__name__)


class Analytics:
    """
    Analytics tracking system using SQLite.
    Tracks API calls, TTS usage, OCR processing, and errors with cost calculation.
    """
    
    _instance: Optional['Analytics'] = None
    _lock = threading.Lock()
    
    def __init__(self, db_path: str = None):
        """
        Initialize analytics database.
        
        Args:
            db_path: Path to SQLite database file (default: from config)
        """
        self.enabled = Config.ANALYTICS_ENABLED
        self.db_path = db_path or Config.ANALYTICS_DB_PATH
        self.retention_days = Config.ANALYTICS_RETENTION_DAYS
        self.current_session_id: Optional[int] = None
        
        if self.enabled:
            self._init_database()
            logger.debug(f"Analytics initialized: db={self.db_path}")
        else:
            logger.debug("Analytics disabled")
    
    @classmethod
    def get_instance(cls) -> 'Analytics':
        """Get or create the singleton analytics instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _init_database(self):
        """Create database schema if not exists."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        persona_count INTEGER DEFAULT 0
                    )
                """)
                
                # API calls table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS api_calls (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER,
                        provider TEXT NOT NULL,
                        model TEXT,
                        tokens_input INTEGER,
                        tokens_output INTEGER,
                        tokens_total INTEGER,
                        cost REAL,
                        latency_ms INTEGER,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions (id)
                    )
                """)
                
                # TTS usage table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tts_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER,
                        provider TEXT NOT NULL,
                        char_count INTEGER,
                        cost REAL,
                        latency_ms INTEGER,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions (id)
                    )
                """)
                
                # OCR usage table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ocr_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER,
                        engine TEXT NOT NULL,
                        processing_time_ms INTEGER,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions (id)
                    )
                """)
                
                # Errors table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS errors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER,
                        component TEXT NOT NULL,
                        error_msg TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions (id)
                    )
                """)
                
                conn.commit()
                
            logger.info("Analytics database initialized")
            
            # Clean up old records
            self._cleanup_old_records()
            
        except Exception as e:
            logger.error(f"Failed to initialize analytics database: {e}")
            self.enabled = False
    
    def _cleanup_old_records(self):
        """Remove records older than retention period."""
        if not self.enabled or self.retention_days <= 0:
            return
        
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get sessions to delete
                cursor.execute("""
                    SELECT id FROM sessions 
                    WHERE start_time < ?
                """, (cutoff_date,))
                
                old_sessions = [row[0] for row in cursor.fetchall()]
                
                if old_sessions:
                    # Delete related records
                    for table in ['api_calls', 'tts_usage', 'ocr_usage', 'errors']:
                        cursor.execute(f"""
                            DELETE FROM {table}
                            WHERE session_id IN ({','.join('?' * len(old_sessions))})
                        """, old_sessions)
                    
                    # Delete sessions
                    cursor.execute(f"""
                        DELETE FROM sessions
                        WHERE id IN ({','.join('?' * len(old_sessions))})
                    """, old_sessions)
                    
                    conn.commit()
                    logger.info(f"Cleaned up {len(old_sessions)} old session(s)")
                    
        except Exception as e:
            logger.warning(f"Error cleaning up old records: {e}")
    
    def start_session(self) -> Optional[int]:
        """
        Start a new analytics session.
        
        Returns:
            Session ID or None if disabled
        """
        if not self.enabled:
            return None
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO sessions DEFAULT VALUES")
                conn.commit()
                self.current_session_id = cursor.lastrowid
                logger.info(f"Started analytics session {self.current_session_id}")
                return self.current_session_id
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            return None
    
    def end_session(self, session_id: int = None):
        """
        End an analytics session.
        
        Args:
            session_id: Session to end (default: current session)
        """
        if not self.enabled:
            return
        
        session_id = session_id or self.current_session_id
        if not session_id:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sessions 
                    SET end_time = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (session_id,))
                conn.commit()
                logger.info(f"Ended analytics session {session_id}")
                
                if session_id == self.current_session_id:
                    self.current_session_id = None
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
    
    def track_api_call(
        self,
        provider: str,
        model: str = None,
        tokens_input: int = 0,
        tokens_output: int = 0,
        latency_ms: int = 0,
        session_id: int = None
    ):
        """
        Track an API call with cost calculation.
        
        Args:
            provider: API provider name (e.g., 'openai')
            model: Model name
            tokens_input: Input tokens used
            tokens_output: Output tokens used
            latency_ms: Request latency in milliseconds
            session_id: Session ID (default: current session)
        """
        if not self.enabled:
            return
        
        session_id = session_id or self.current_session_id
        tokens_total = tokens_input + tokens_output
        
        # Calculate cost
        cost = self._calculate_api_cost(provider, tokens_input, tokens_output)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO api_calls 
                    (session_id, provider, model, tokens_input, tokens_output, tokens_total, cost, latency_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (session_id, provider, model, tokens_input, tokens_output, tokens_total, cost, latency_ms))
                conn.commit()
                
                if cost > 0:
                    logger.debug(f"Tracked API call: {provider} ({tokens_total} tokens, ${cost:.6f})")
        except Exception as e:
            logger.error(f"Failed to track API call: {e}")
    
    def track_tts(
        self,
        provider: str,
        char_count: int,
        latency_ms: int = 0,
        session_id: int = None
    ):
        """
        Track TTS usage with cost calculation.
        
        Args:
            provider: TTS provider name (e.g., 'elevenlabs', 'pyttsx3')
            char_count: Number of characters synthesized
            latency_ms: Synthesis latency in milliseconds
            session_id: Session ID (default: current session)
        """
        if not self.enabled:
            return
        
        session_id = session_id or self.current_session_id
        cost = self._calculate_tts_cost(provider, char_count)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO tts_usage 
                    (session_id, provider, char_count, cost, latency_ms)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, provider, char_count, cost, latency_ms))
                conn.commit()
                
                if cost > 0:
                    logger.debug(f"Tracked TTS: {provider} ({char_count} chars, ${cost:.6f})")
        except Exception as e:
            logger.error(f"Failed to track TTS: {e}")
    
    def track_ocr(
        self,
        engine: str,
        processing_time_ms: int,
        session_id: int = None
    ):
        """
        Track OCR processing.
        
        Args:
            engine: OCR engine name (e.g., 'easyocr', 'tesseract')
            processing_time_ms: Processing time in milliseconds
            session_id: Session ID (default: current session)
        """
        if not self.enabled:
            return
        
        session_id = session_id or self.current_session_id
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ocr_usage 
                    (session_id, engine, processing_time_ms)
                    VALUES (?, ?, ?)
                """, (session_id, engine, processing_time_ms))
                conn.commit()
                
                logger.debug(f"Tracked OCR: {engine} ({processing_time_ms}ms)")
        except Exception as e:
            logger.error(f"Failed to track OCR: {e}")
    
    def track_error(
        self,
        component: str,
        error_msg: str,
        session_id: int = None
    ):
        """
        Track an error occurrence.
        
        Args:
            component: Component where error occurred
            error_msg: Error message
            session_id: Session ID (default: current session)
        """
        if not self.enabled:
            return
        
        session_id = session_id or self.current_session_id
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO errors 
                    (session_id, component, error_msg)
                    VALUES (?, ?, ?)
                """, (session_id, component, error_msg))
                conn.commit()
                
                logger.debug(f"Tracked error: {component}")
        except Exception as e:
            logger.error(f"Failed to track error: {e}")
    
    def _calculate_api_cost(self, provider: str, tokens_input: int, tokens_output: int) -> float:
        """Calculate cost for API call."""
        if provider.lower() == "openai":
            input_cost = (tokens_input / 1000.0) * Config.OPENAI_COST_PER_1K_TOKENS_INPUT
            output_cost = (tokens_output / 1000.0) * Config.OPENAI_COST_PER_1K_TOKENS_OUTPUT
            return input_cost + output_cost
        return 0.0
    
    def _calculate_tts_cost(self, provider: str, char_count: int) -> float:
        """Calculate cost for TTS."""
        if provider.lower() == "elevenlabs":
            return (char_count / 1000.0) * Config.ELEVENLABS_COST_PER_1K_CHARS
        return 0.0  # pyttsx3 is free
    
    def get_session_stats(self, session_id: int = None) -> Dict[str, Any]:
        """
        Get statistics for a session.
        
        Args:
            session_id: Session ID (default: current session)
        
        Returns:
            Dictionary with session statistics
        """
        if not self.enabled:
            return {}
        
        session_id = session_id or self.current_session_id
        if not session_id:
            return {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # API call stats
                cursor.execute("""
                    SELECT 
                        COUNT(*) as call_count,
                        SUM(tokens_total) as total_tokens,
                        SUM(cost) as total_api_cost,
                        AVG(latency_ms) as avg_latency
                    FROM api_calls
                    WHERE session_id = ?
                """, (session_id,))
                api_stats = cursor.fetchone()
                
                # TTS stats
                cursor.execute("""
                    SELECT 
                        COUNT(*) as tts_count,
                        SUM(char_count) as total_chars,
                        SUM(cost) as total_tts_cost
                    FROM tts_usage
                    WHERE session_id = ?
                """, (session_id,))
                tts_stats = cursor.fetchone()
                
                # OCR stats
                cursor.execute("""
                    SELECT 
                        COUNT(*) as ocr_count,
                        AVG(processing_time_ms) as avg_processing_time
                    FROM ocr_usage
                    WHERE session_id = ?
                """, (session_id,))
                ocr_stats = cursor.fetchone()
                
                # Error count
                cursor.execute("""
                    SELECT COUNT(*) FROM errors WHERE session_id = ?
                """, (session_id,))
                error_count = cursor.fetchone()[0]
                
                total_cost = (api_stats[2] or 0.0) + (tts_stats[2] or 0.0)
                
                return {
                    'session_id': session_id,
                    'api_call_count': api_stats[0] or 0,
                    'total_tokens': api_stats[1] or 0,
                    'api_cost': api_stats[2] or 0.0,
                    'avg_latency_ms': api_stats[3] or 0.0,
                    'tts_count': tts_stats[0] or 0,
                    'total_chars': tts_stats[1] or 0,
                    'tts_cost': tts_stats[2] or 0.0,
                    'ocr_count': ocr_stats[0] or 0,
                    'avg_ocr_time_ms': ocr_stats[1] or 0.0,
                    'error_count': error_count,
                    'total_cost': total_cost
                }
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {}
    
    def export_csv(self, output_path: str, start_date: datetime = None, end_date: datetime = None):
        """
        Export analytics to CSV files.
        
        Args:
            output_path: Directory to save CSV files
            start_date: Filter start date (optional)
            end_date: Filter end date (optional)
        """
        if not self.enabled:
            logger.warning("Analytics disabled, cannot export")
            return
        
        import csv
        
        output_dir = Path(output_path)
        output_dir.mkdir(exist_ok=True)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Export each table
                for table in ['sessions', 'api_calls', 'tts_usage', 'ocr_usage', 'errors']:
                    query = f"SELECT * FROM {table}"
                    params = []
                    
                    if start_date and table != 'sessions':
                        query += " WHERE timestamp >= ?"
                        params.append(start_date)
                    
                    if end_date and table != 'sessions':
                        if 'WHERE' in query:
                            query += " AND timestamp <= ?"
                        else:
                            query += " WHERE timestamp <= ?"
                        params.append(end_date)
                    
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    
                    if rows:
                        csv_path = output_dir / f"{table}.csv"
                        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                            writer.writeheader()
                            writer.writerows([dict(row) for row in rows])
                        
                        logger.info(f"Exported {len(rows)} rows to {csv_path}")
                
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
    
    @contextmanager
    def session(self):
        """Context manager for analytics session."""
        session_id = self.start_session()
        try:
            yield session_id
        finally:
            self.end_session(session_id)


# Global analytics instance
def get_analytics() -> Analytics:
    """Get the global analytics instance."""
    return Analytics.get_instance()

