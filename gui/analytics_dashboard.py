"""
Analytics Dashboard - Visualize costs and usage statistics.
Run with: python gui/analytics_dashboard.py
"""
import dearpygui.dearpygui as dpg
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analytics import get_analytics
from gui.components import setup_theme, create_cost_card, create_stat_row, create_button_row, COLORS
from datetime import datetime, timedelta
import sqlite3


class AnalyticsDashboard:
    """Analytics dashboard GUI."""
    
    def __init__(self):
        self.analytics = get_analytics()
        self.refresh_rate = 5  # seconds
    
    def refresh_data(self):
        """Refresh dashboard data."""
        stats = self.analytics.get_session_stats()
        
        if not stats:
            # Show all-time stats if no current session
            stats = self._get_all_time_stats()
        
        # Update cost cards
        if dpg.does_item_exist("total_cost_value"):
            dpg.set_value("total_cost_value", f"${stats.get('total_cost', 0):.4f}")
        
        if dpg.does_item_exist("api_cost_value"):
            dpg.set_value("api_cost_value", f"${stats.get('api_cost', 0):.4f}")
        
        if dpg.does_item_exist("tts_cost_value"):
            dpg.set_value("tts_cost_value", f"${stats.get('tts_cost', 0):.4f}")
        
        # Update stats
        if dpg.does_item_exist("stat_API Calls"):
            dpg.set_value("stat_API Calls", str(stats.get('api_call_count', 0)))
        
        if dpg.does_item_exist("stat_TTS Generations"):
            dpg.set_value("stat_TTS Generations", str(stats.get('tts_count', 0)))
        
        if dpg.does_item_exist("stat_Total Tokens"):
            dpg.set_value("stat_Total Tokens", str(stats.get('total_tokens', 0)))
        
        if dpg.does_item_exist("stat_Avg Latency"):
            dpg.set_value("stat_Avg Latency", f"{stats.get('avg_latency_ms', 0):.0f}ms")
    
    def _get_all_time_stats(self):
        """Get all-time statistics."""
        try:
            with sqlite3.connect(self.analytics.db_path) as conn:
                cursor = conn.cursor()
                
                # API stats
                cursor.execute("""
                    SELECT 
                        COUNT(*) as call_count,
                        SUM(tokens_total) as total_tokens,
                        SUM(cost) as total_api_cost,
                        AVG(latency_ms) as avg_latency
                    FROM api_calls
                """)
                api_stats = cursor.fetchone()
                
                # TTS stats
                cursor.execute("""
                    SELECT 
                        COUNT(*) as tts_count,
                        SUM(char_count) as total_chars,
                        SUM(cost) as total_tts_cost
                    FROM tts_usage
                """)
                tts_stats = cursor.fetchone()
                
                total_cost = (api_stats[2] or 0.0) + (tts_stats[2] or 0.0)
                
                return {
                    'api_call_count': api_stats[0] or 0,
                    'total_tokens': api_stats[1] or 0,
                    'api_cost': api_stats[2] or 0.0,
                    'avg_latency_ms': api_stats[3] or 0.0,
                    'tts_count': tts_stats[0] or 0,
                    'total_chars': tts_stats[1] or 0,
                    'tts_cost': tts_stats[2] or 0.0,
                    'total_cost': total_cost
                }
        except Exception as e:
            print(f"Error getting all-time stats: {e}")
            return {}
    
    def export_csv(self):
        """Export analytics to CSV."""
        try:
            output_dir = Path("analytics_export")
            self.analytics.export_csv(str(output_dir))
            print(f"✓ Exported to {output_dir}")
        except Exception as e:
            print(f"✗ Export failed: {e}")
    
    def create_ui(self):
        """Create the dashboard UI."""
        with dpg.window(label="Analytics Dashboard", tag="main_window", width=800, height=600):
            # Header
            dpg.add_text("R6 Nice Talker - Analytics Dashboard", color=COLORS['accent'])
            dpg.add_separator()
            
            # Cost Summary Cards
            with dpg.group(horizontal=True):
                with dpg.child_window(height=120, width=250):
                    dpg.add_text("Total Cost", color=COLORS['text_dim'])
                    dpg.add_text("$0.0000", tag="total_cost_value", color=COLORS['accent'])
                
                with dpg.child_window(height=120, width=250):
                    dpg.add_text("API Cost", color=COLORS['text_dim'])
                    dpg.add_text("$0.0000", tag="api_cost_value", color=COLORS['success'])
                
                with dpg.child_window(height=120, width=250):
                    dpg.add_text("TTS Cost", color=COLORS['text_dim'])
                    dpg.add_text("$0.0000", tag="tts_cost_value", color=COLORS['warning'])
            
            dpg.add_separator()
            
            # Statistics
            dpg.add_text("Usage Statistics", color=COLORS['accent'])
            
            with dpg.child_window(height=200, width=-1):
                create_stat_row("stats_group", "API Calls", "0")
                create_stat_row("stats_group", "TTS Generations", "0")
                create_stat_row("stats_group", "Total Tokens", "0")
                create_stat_row("stats_group", "Avg Latency", "0ms")
            
            dpg.add_separator()
            
            # Recent Activity
            dpg.add_text("Recent API Calls", color=COLORS['accent'])
            
            with dpg.table(header_row=True, tag="recent_calls_table",
                          borders_innerH=True, borders_outerH=True,
                          borders_innerV=True, borders_outerV=True):
                dpg.add_table_column(label="Time")
                dpg.add_table_column(label="Provider")
                dpg.add_table_column(label="Tokens")
                dpg.add_table_column(label="Cost")
                dpg.add_table_column(label="Latency")
                
                # Populate with recent data
                self._populate_recent_calls()
            
            dpg.add_separator()
            
            # Action Buttons
            create_button_row("button_row", [
                ("Refresh", self.refresh_data),
                ("Export CSV", self.export_csv),
                ("Clear Old Data", self._clear_old_data)
            ])
    
    def _populate_recent_calls(self):
        """Populate recent API calls table."""
        try:
            with sqlite3.connect(self.analytics.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT timestamp, provider, tokens_total, cost, latency_ms
                    FROM api_calls
                    ORDER BY timestamp DESC
                    LIMIT 10
                """)
                
                for row in cursor.fetchall():
                    with dpg.table_row(parent="recent_calls_table"):
                        timestamp = datetime.fromisoformat(row[0]).strftime("%H:%M:%S")
                        dpg.add_text(timestamp)
                        dpg.add_text(row[1])
                        dpg.add_text(str(row[2] or 0))
                        dpg.add_text(f"${row[3]:.6f}")
                        dpg.add_text(f"{row[4] or 0}ms")
        except Exception as e:
            print(f"Error populating table: {e}")
    
    def _clear_old_data(self):
        """Clear old analytics data."""
        try:
            removed = self.analytics._cleanup_old_records()
            print(f"✓ Cleaned up {removed} old records")
            self.refresh_data()
        except Exception as e:
            print(f"✗ Cleanup failed: {e}")
    
    def run(self):
        """Run the dashboard."""
        dpg.create_context()
        setup_theme()
        
        self.create_ui()
        
        # Initial data load
        self.refresh_data()
        
        dpg.create_viewport(title="Analytics Dashboard", width=850, height=650)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
        dpg.start_dearpygui()
        dpg.destroy_context()


def main():
    """Main entry point."""
    dashboard = AnalyticsDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()

