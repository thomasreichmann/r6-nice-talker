"""
Reusable DearPyGui components and themes for consistent GUI design.
"""
import dearpygui.dearpygui as dpg
from datetime import datetime, timedelta
from typing import Callable, Optional, List


# Theme Colors (Dark Mode)
COLORS = {
    'bg': (30, 30, 30),
    'bg_light': (45, 45, 45),
    'accent': (0, 188, 212),
    'success': (76, 175, 80),
    'warning': (255, 152, 0),
    'error': (244, 67, 54),
    'text': (220, 220, 220),
    'text_dim': (150, 150, 150),
}


def setup_theme():
    """Setup global dark theme for DearPyGui."""
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, COLORS['bg'], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, COLORS['bg_light'], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, COLORS['bg_light'], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Text, COLORS['text'], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Button, COLORS['accent'], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0, 150, 170), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 130, 150), category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 4, category=dpg.mvThemeCat_Core)
    
    dpg.bind_theme(global_theme)


def create_cost_card(parent, label: str, value: float, delta: Optional[float] = None) -> int:
    """
    Create a cost display card with optional trend indicator.
    
    Args:
        parent: Parent container ID
        label: Card label
        value: Cost value
        delta: Change amount (optional)
    
    Returns:
        Group ID
    """
    with dpg.group(parent=parent, horizontal=False) as group:
        with dpg.child_window(height=100, width=200):
            dpg.add_text(label, color=COLORS['text_dim'])
            dpg.add_text(f"${value:.4f}", tag=f"{label}_value")
            
            if delta is not None:
                color = COLORS['success'] if delta >= 0 else COLORS['error']
                dpg.add_text(f"${abs(delta):.4f}", color=color)
    
    return group


def create_provider_selector(parent, callback: Callable, providers: List[str], default: str = None) -> int:
    """
    Create a provider selection combo box.
    
    Args:
        parent: Parent container ID
        callback: Function to call on selection
        providers: List of provider names
        default: Default selection
    
    Returns:
        Combo ID
    """
    combo = dpg.add_combo(
        items=providers,
        default_value=default or providers[0],
        callback=callback,
        parent=parent,
        width=200
    )
    return combo


def create_date_range_picker(parent, callback: Callable) -> tuple:
    """
    Create start/end date pickers.
    
    Args:
        parent: Parent container ID
        callback: Function to call on date change
    
    Returns:
        Tuple of (start_picker_id, end_picker_id)
    """
    with dpg.group(parent=parent, horizontal=True):
        dpg.add_text("From:")
        start_picker = dpg.add_input_text(
            default_value=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            width=120,
            callback=callback
        )
        
        dpg.add_text("To:")
        end_picker = dpg.add_input_text(
            default_value=datetime.now().strftime("%Y-%m-%d"),
            width=120,
            callback=callback
        )
    
    return start_picker, end_picker


def create_log_viewer(parent, max_lines: int = 100) -> int:
    """
    Create a scrollable log viewer with filtering.
    
    Args:
        parent: Parent container ID
        max_lines: Maximum lines to display
    
    Returns:
        Child window ID
    """
    with dpg.child_window(parent=parent, height=-50) as child:
        log_text = dpg.add_text("", wrap=0, tag=f"log_viewer_{parent}")
    
    return child


def create_export_dialog(title: str, export_fn: Callable) -> int:
    """
    Create an export dialog window.
    
    Args:
        title: Dialog title
        export_fn: Function to call for export (receives format as arg)
    
    Returns:
        Window ID
    """
    with dpg.window(label=title, modal=True, show=False, width=400, height=200) as window:
        dpg.add_text("Select export format:")
        dpg.add_radio_button(
            items=["CSV", "JSON"],
            default_value="CSV",
            tag=f"export_format_{window}"
        )
        
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Export",
                callback=lambda: export_fn(dpg.get_value(f"export_format_{window}"))
            )
            dpg.add_button(
                label="Cancel",
                callback=lambda: dpg.configure_item(window, show=False)
            )
    
    return window


def create_test_output_panel(parent) -> int:
    """
    Create a code-styled output panel for test results.
    
    Args:
        parent: Parent container ID
    
    Returns:
        Child window ID
    """
    with dpg.child_window(parent=parent, height=-1) as child:
        output_text = dpg.add_text(
            "",
            wrap=0,
            tag=f"test_output_{parent}"
        )
    
    return child


def create_stat_row(parent, label: str, value: str, color: Optional[tuple] = None):
    """
    Create a labeled statistic row.
    
    Args:
        parent: Parent container ID
        label: Stat label
        value: Stat value
        color: Optional text color
    """
    with dpg.group(parent=parent, horizontal=True):
        dpg.add_text(f"{label}:", color=COLORS['text_dim'])
        dpg.add_text(value, color=color or COLORS['text'], tag=f"stat_{label}_{parent}")


def create_button_row(parent, buttons: List[tuple]):
    """
    Create a horizontal row of buttons.
    
    Args:
        parent: Parent container ID
        buttons: List of (label, callback) tuples
    """
    with dpg.group(parent=parent, horizontal=True):
        for label, callback in buttons:
            dpg.add_button(label=label, callback=callback)


def update_text(tag: str, text: str):
    """
    Update text in a text widget.
    
    Args:
        tag: Widget tag
        text: New text
    """
    if dpg.does_item_exist(tag):
        dpg.set_value(tag, text)


def show_notification(message: str, duration: int = 3):
    """
    Show a temporary notification popup.
    
    Args:
        message: Notification message
        duration: Duration in seconds
    """
    with dpg.window(
        label="Notification",
        modal=False,
        no_title_bar=True,
        no_resize=True,
        no_move=True,
        pos=(10, 10)
    ) as notif:
        dpg.add_text(message)
        
        # Auto-close after duration
        def close_notification():
            if dpg.does_item_exist(notif):
                dpg.delete_item(notif)
        
        # Schedule close (DearPyGui doesn't have native timers, so use frame count)
        # This is a simplified approach - proper implementation would use threading or frame callbacks

