import json
import mss
import cv2
import numpy as np
import sys
import os
import ctypes
import time
import threading
import copy
from enum import Enum
from collections import deque

# Modern color palette
COLORS = {
    'bg_dark': (30, 30, 30),
    'bg_medium': (45, 45, 45),
    'accent': (212, 188, 0),  # Cyan/Teal BGR
    'success': (80, 175, 76),  # Green BGR
    'warning': (0, 152, 255),  # Orange BGR
    'error': (54, 67, 244),  # Red BGR
    'selected': (99, 30, 233),  # Purple/Magenta BGR
    'text': (255, 255, 255),
    'text_dim': (180, 180, 180),
    'handle': (255, 255, 0)  # Yellow BGR
}

class Mode(Enum):
    IDLE = "IDLE"
    DRAWING = "DRAWING"
    NAMING = "NAMING"
    MOVING = "MOVING"
    RESIZING = "RESIZING"

class Command:
    """Base class for undo/redo commands"""
    def execute(self, editor): pass
    def undo(self, editor): pass

class CreateROICommand(Command):
    def __init__(self, name, roi_data):
        self.name = name
        self.roi_data = roi_data
    
    def execute(self, editor):
        editor.rois[self.name] = self.roi_data.copy()
    
    def undo(self, editor):
        if self.name in editor.rois:
            del editor.rois[self.name]

class DeleteROICommand(Command):
    def __init__(self, name, roi_data):
        self.name = name
        self.roi_data = roi_data
    
    def execute(self, editor):
        if self.name in editor.rois:
            del editor.rois[self.name]
    
    def undo(self, editor):
        editor.rois[self.name] = self.roi_data.copy()

class MoveROICommand(Command):
    def __init__(self, name, old_pos, new_pos):
        self.name = name
        self.old_pos = old_pos
        self.new_pos = new_pos
    
    def execute(self, editor):
        if self.name in editor.rois:
            editor.rois[self.name]['left'] = self.new_pos[0]
            editor.rois[self.name]['top'] = self.new_pos[1]
    
    def undo(self, editor):
        if self.name in editor.rois:
            editor.rois[self.name]['left'] = self.old_pos[0]
            editor.rois[self.name]['top'] = self.old_pos[1]

class ResizeROICommand(Command):
    def __init__(self, name, old_bounds, new_bounds):
        self.name = name
        self.old_bounds = old_bounds
        self.new_bounds = new_bounds
    
    def execute(self, editor):
        if self.name in editor.rois:
            editor.rois[self.name].update(self.new_bounds)
    
    def undo(self, editor):
        if self.name in editor.rois:
            editor.rois[self.name].update(self.old_bounds)

def set_dpi_awareness():
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

def load_rois():
    try:
        with open('rois.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_rois(rois):
    with open('rois.json', 'w') as f:
        json.dump(rois, f, indent=4)

class ROIEditor:
    def __init__(self):
        self.rois = load_rois()
        self.mode = Mode.IDLE
        self.selected_roi = None
        self.drawing_start = None
        self.drawing_current = None
        self.scale_factor = 1.0
        self.sct = mss.mss()
        self.show_help = False
        self.feedback_message = ""
        self.feedback_timer = 0
        self.feedback_alpha = 0.0
        self.naming_buffer = ""
        self.temp_roi = None
        self.last_key = -1
        
        # Undo/Redo
        self.undo_stack = deque(maxlen=50)
        self.redo_stack = deque(maxlen=50)
        
        # Drag/Resize
        self.drag_start_pos = None
        self.drag_roi_original = None
        self.resize_handle = None  # 'tl', 'tr', 'bl', 'br', 'l', 'r', 't', 'b'
        
        # OCR Preview
        self.ocr_preview_enabled = False
        self.ocr_cache = {}
        self.ocr_lock = threading.Lock()
        self.ocr_thread = None
        self.ocr_running = False
        self.last_ocr_update = 0
        
        # Animation
        self.animation_time = 0
        self.roi_scale_animation = {}  # Track scale animations per ROI
        self.save_animation_timer = 0
        
    def execute_command(self, command):
        command.execute(self)
        self.undo_stack.append(command)
        self.redo_stack.clear()
    
    def undo(self):
        if self.undo_stack:
            command = self.undo_stack.pop()
            command.undo(self)
            self.redo_stack.append(command)
            self.show_feedback("Undo", 30)
    
    def redo(self):
        if self.redo_stack:
            command = self.redo_stack.pop()
            command.execute(self)
            self.undo_stack.append(command)
            self.show_feedback("Redo", 30)
    
    def get_handle_at(self, x, y, roi):
        """Check if mouse is over a resize handle"""
        left, top = roi['left'], roi['top']
        right, bottom = left + roi['width'], top + roi['height']
        threshold = 10
        
        handles = {
            'tl': (left, top),
            'tr': (right, top),
            'bl': (left, bottom),
            'br': (right, bottom),
            't': (left + roi['width']//2, top),
            'b': (left + roi['width']//2, bottom),
            'l': (left, top + roi['height']//2),
            'r': (right, top + roi['height']//2)
        }
        
        for handle_name, (hx, hy) in handles.items():
            if abs(x - hx) < threshold and abs(y - hy) < threshold:
                return handle_name
        return None
    
    def mouse_callback(self, event, x, y, flags, param):
        real_x = int(x / self.scale_factor)
        real_y = int(y / self.scale_factor)
        
        if self.mode == Mode.NAMING:
            return
        
        if event == cv2.EVENT_LBUTTONDOWN:
            # Check for resize handle first
            if self.selected_roi and self.selected_roi in self.rois:
                handle = self.get_handle_at(real_x, real_y, self.rois[self.selected_roi])
                if handle:
                    self.mode = Mode.RESIZING
                    self.resize_handle = handle
                    self.drag_start_pos = (real_x, real_y)
                    self.drag_roi_original = self.rois[self.selected_roi].copy()
                    return
            
            # Check if clicking inside ROI
            clicked_roi = None
            for name, roi in self.rois.items():
                rx, ry, rw, rh = roi['left'], roi['top'], roi['width'], roi['height']
                if rx <= real_x <= rx + rw and ry <= real_y <= ry + rh:
                    clicked_roi = name
                    break
            
            if clicked_roi:
                self.selected_roi = clicked_roi
                self.mode = Mode.MOVING
                self.drag_start_pos = (real_x, real_y)
                self.drag_roi_original = self.rois[clicked_roi].copy()
                self.show_feedback(f"Selected: {clicked_roi}", 30)
                # Trigger scale animation
                self.roi_scale_animation[clicked_roi] = 0
            else:
                self.mode = Mode.DRAWING
                self.drawing_start = (real_x, real_y)
                self.drawing_current = (real_x, real_y)
                self.selected_roi = None
        
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.mode == Mode.DRAWING:
                self.drawing_current = (real_x, real_y)
            elif self.mode == Mode.MOVING and self.selected_roi:
                dx = real_x - self.drag_start_pos[0]
                dy = real_y - self.drag_start_pos[1]
                self.rois[self.selected_roi]['left'] = max(0, self.drag_roi_original['left'] + dx)
                self.rois[self.selected_roi]['top'] = max(0, self.drag_roi_original['top'] + dy)
            elif self.mode == Mode.RESIZING and self.selected_roi:
                self.resize_roi(real_x, real_y)
        
        elif event == cv2.EVENT_LBUTTONUP:
            if self.mode == Mode.DRAWING:
                x1, y1 = self.drawing_start
                x2, y2 = (real_x, real_y)
                
                left = min(x1, x2)
                top = min(y1, y2)
                width = abs(x1 - x2)
                height = abs(y1 - y2)
                
                if width > 10 and height > 10:
                    self.temp_roi = {"top": top, "left": left, "width": width, "height": height}
                    self.mode = Mode.NAMING
                    self.naming_buffer = ""
                    self.show_feedback("Enter ROI name", 200)
                else:
                    self.show_feedback("ROI too small", 30)
                    self.mode = Mode.IDLE
                    
                self.drawing_start = None
                self.drawing_current = None
            
            elif self.mode == Mode.MOVING and self.selected_roi:
                # Create move command
                old_pos = (self.drag_roi_original['left'], self.drag_roi_original['top'])
                new_pos = (self.rois[self.selected_roi]['left'], self.rois[self.selected_roi]['top'])
                if old_pos != new_pos:
                    self.execute_command(MoveROICommand(self.selected_roi, old_pos, new_pos))
                self.mode = Mode.IDLE
            
            elif self.mode == Mode.RESIZING and self.selected_roi:
                # Create resize command
                if self.drag_roi_original != self.rois[self.selected_roi]:
                    self.execute_command(ResizeROICommand(self.selected_roi, 
                                                         self.drag_roi_original, 
                                                         self.rois[self.selected_roi].copy()))
                self.mode = Mode.IDLE
                self.resize_handle = None
    
    def resize_roi(self, x, y):
        """Handle ROI resizing based on which handle is being dragged"""
        roi = self.rois[self.selected_roi]
        orig = self.drag_roi_original
        handle = self.resize_handle
        
        if 'l' in handle:
            new_left = min(x, orig['left'] + orig['width'] - 10)
            roi['width'] = orig['left'] + orig['width'] - new_left
            roi['left'] = new_left
        elif 'r' in handle:
            roi['width'] = max(10, x - roi['left'])
        
        if 't' in handle:
            new_top = min(y, orig['top'] + orig['height'] - 10)
            roi['height'] = orig['top'] + orig['height'] - new_top
            roi['top'] = new_top
        elif 'b' in handle:
            roi['height'] = max(10, y - roi['top'])
    
    def show_feedback(self, message, duration=60):
        self.feedback_message = message
        self.feedback_timer = duration
        self.feedback_alpha = 1.0
    
    def draw_rounded_rect(self, img, pt1, pt2, color, thickness=2, radius=10):
        """Draw rectangle with rounded corners"""
        x1, y1 = pt1
        x2, y2 = pt2
        
        # Draw main rectangles
        cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, thickness)
        cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, thickness)
        
        # Draw circles at corners
        cv2.circle(img, (x1 + radius, y1 + radius), radius, color, thickness)
        cv2.circle(img, (x2 - radius, y1 + radius), radius, color, thickness)
        cv2.circle(img, (x1 + radius, y2 - radius), radius, color, thickness)
        cv2.circle(img, (x2 - radius, y2 - radius), radius, color, thickness)
    
    def draw_text_with_bg(self, img, text, pos, font_scale=0.6, color=COLORS['text'], 
                          bg_color=COLORS['bg_dark'], padding=5, alpha=0.9):
        font = cv2.FONT_HERSHEY_SIMPLEX
        (tw, th), baseline = cv2.getTextSize(text, font, font_scale, 1)
        
        x, y = pos
        overlay = img.copy()
        cv2.rectangle(overlay, (x - padding, y - th - padding),
                     (x + tw + padding, y + baseline + padding), bg_color, -1)
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
        
        cv2.putText(img, text, (x, y), font, font_scale, color, 1, cv2.LINE_AA)
    
    def draw_toolbar(self, img):
        """Draw top toolbar with save animation"""
        height, width = img.shape[:2]
        toolbar_height = 50
        
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (width, toolbar_height), COLORS['bg_medium'], -1)
        cv2.addWeighted(overlay, 0.95, img, 0.05, 0, img)
        
        # Title with subtle glow effect
        title_color = COLORS['accent']
        if self.animation_time % 100 < 50:
            glow = int(255 * (1.0 - abs((self.animation_time % 100) - 25) / 25.0 * 0.2))
            title_color = (min(255, title_color[0] + 20), title_color[1], title_color[2])
        
        cv2.putText(img, "ROI Editor", (15, 32), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.8, title_color, 2, cv2.LINE_AA)
        
        # Buttons/indicators
        buttons = [
            (f"Undo ({len(self.undo_stack)})", 200, bool(self.undo_stack)),
            (f"Redo ({len(self.redo_stack)})", 330, bool(self.redo_stack)),
            ("Save", 460, True),
            ("OCR" + (" ON" if self.ocr_preview_enabled else " OFF"), 560, True)
        ]
        
        for text, x, enabled in buttons:
            color = COLORS['text'] if enabled else COLORS['text_dim']
            
            # Save button animation
            if text == "Save" and self.save_animation_timer > 0:
                scale = 1.0 + 0.2 * (self.save_animation_timer / 30.0)
                color = COLORS['success']
                cv2.putText(img, text, (x, 32), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.5 * scale, color, 2, cv2.LINE_AA)
                self.save_animation_timer -= 1
            else:
                cv2.putText(img, text, (x, 32), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.5, color, 1, cv2.LINE_AA)
    
    def draw_status_bar(self, img):
        """Draw bottom status bar"""
        height, width = img.shape[:2]
        bar_height = 60
        
        overlay = img.copy()
        cv2.rectangle(overlay, (0, height - bar_height), (width, height), COLORS['bg_medium'], -1)
        cv2.addWeighted(overlay, 0.95, img, 0.05, 0, img)
        
        # Mode
        mode_text = f"Mode: {self.mode.value}"
        mode_color = COLORS['accent'] if self.mode != Mode.IDLE else COLORS['text_dim']
        cv2.putText(img, mode_text, (10, height - 35), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.6, mode_color, 1, cv2.LINE_AA)
        
        # Selected ROI
        if self.selected_roi and self.selected_roi in self.rois:
            roi = self.rois[self.selected_roi]
            info = f"{self.selected_roi}: ({roi['left']}, {roi['top']}) {roi['width']}x{roi['height']}"
            cv2.putText(img, info, (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.5, COLORS['success'], 1, cv2.LINE_AA)
        
        # Shortcuts
        shortcuts = "Ctrl+Z: Undo  |  Ctrl+Y: Redo  |  S: Save  |  D: Delete  |  H: Help  |  Q: Quit"
        cv2.putText(img, shortcuts, (width - 700, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.45, COLORS['text_dim'], 1, cv2.LINE_AA)
    
    def draw_feedback(self, img):
        """Draw animated feedback message with slide-in effect"""
        if self.feedback_timer > 0:
            height, width = img.shape[:2]
            
            # Fade and slide animation
            total_duration = 60
            if self.feedback_timer < 15:
                self.feedback_alpha = self.feedback_timer / 15.0
            else:
                progress = (total_duration - self.feedback_timer) / 10.0
                self.feedback_alpha = min(1.0, progress)
            
            # Slide from top
            slide_offset = int((1.0 - self.feedback_alpha) * 30)
            
            overlay = img.copy()
            msg_width = len(self.feedback_message) * 12 + 40
            msg_x = width // 2 - msg_width // 2
            msg_y = 70 - slide_offset
            
            cv2.rectangle(overlay, (msg_x, msg_y), (msg_x + msg_width, msg_y + 50), 
                         COLORS['success'], -1)
            alpha = 0.85 * self.feedback_alpha
            cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
            
            text_color = tuple([int(c * self.feedback_alpha) for c in COLORS['text']])
            cv2.putText(img, self.feedback_message, (msg_x + 20, msg_y + 32), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2, cv2.LINE_AA)
            
            self.feedback_timer -= 1
    
    def draw_ocr_panel(self, img):
        """Draw OCR preview panel on the right side"""
        if not self.ocr_preview_enabled:
            return
        
        height, width = img.shape[:2]
        
        panel_width = 350
        panel_x = width - panel_width - 10
        panel_y = 70
        
        # Calculate panel height based on ROIs
        line_height = 25
        header_height = 50
        roi_spacing = 10
        max_lines_per_roi = 4
        panel_height = header_height + len(self.rois) * (line_height * max_lines_per_roi + roi_spacing) + 20
        panel_height = min(panel_height, height - 150)  # Don't overlap status bar
        
        # Draw panel background
        overlay = img.copy()
        cv2.rectangle(overlay, (panel_x, panel_y), (panel_x + panel_width, panel_y + panel_height),
                     COLORS['bg_dark'], -1)
        cv2.addWeighted(overlay, 0.92, img, 0.08, 0, img)
        
        # Draw border
        cv2.rectangle(img, (panel_x, panel_y), (panel_x + panel_width, panel_y + panel_height),
                     COLORS['accent'], 2)
        
        # Header
        cv2.putText(img, "OCR Preview", (panel_x + 15, panel_y + 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLORS['accent'], 2, cv2.LINE_AA)
        
        # Show error if any
        with self.ocr_lock:
            if "error" in self.ocr_cache:
                error_text = self.ocr_cache["error"]
                y_pos = panel_y + 70
                
                # Wrap error text
                words = error_text.split()
                lines = []
                current_line = ""
                for word in words:
                    if len(current_line + word) < 35:
                        current_line += word + " "
                    else:
                        lines.append(current_line)
                        current_line = word + " "
                if current_line:
                    lines.append(current_line)
                
                for line in lines[:3]:
                    cv2.putText(img, line.strip(), (panel_x + 15, y_pos), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLORS['error'], 1, cv2.LINE_AA)
                    y_pos += 20
                return
        
        # Show OCR results for each ROI
        y_pos = panel_y + 65
        
        with self.ocr_lock:
            for name, roi in self.rois.items():
                if y_pos > panel_y + panel_height - 30:
                    break
                
                # ROI name
                cv2.putText(img, f"{name}:", (panel_x + 15, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLORS['success'], 1, cv2.LINE_AA)
                y_pos += line_height
                
                # OCR text
                ocr_text = self.ocr_cache.get(name, "Processing...")
                
                # Wrap text to fit panel
                if len(ocr_text) > 0:
                    words = ocr_text.split()
                    lines = []
                    current_line = ""
                    for word in words:
                        if len(current_line + word) < 38:
                            current_line += word + " "
                        else:
                            lines.append(current_line)
                            current_line = word + " "
                    if current_line:
                        lines.append(current_line)
                    
                    for line in lines[:3]:  # Max 3 lines per ROI
                        cv2.putText(img, f"  {line.strip()}", (panel_x + 15, y_pos), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLORS['text_dim'], 1, cv2.LINE_AA)
                        y_pos += 20
                else:
                    cv2.putText(img, "  [Empty]", (panel_x + 15, y_pos), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLORS['text_dim'], 1, cv2.LINE_AA)
                    y_pos += 20
                
                y_pos += roi_spacing
    
    def draw_help(self, img):
        """Draw help overlay"""
        if not self.show_help:
            return
        
        height, width = img.shape[:2]
        
        help_lines = [
            ("ROI Editor - Help", COLORS['accent'], 0.7),
            ("", COLORS['text'], 0.5),
            ("Mouse Actions:", COLORS['text'], 0.6),
            ("  Drag in empty space - Create new ROI", COLORS['text_dim'], 0.5),
            ("  Click ROI center - Select and move", COLORS['text_dim'], 0.5),
            ("  Drag ROI handles - Resize", COLORS['text_dim'], 0.5),
            ("", COLORS['text'], 0.5),
            ("Keyboard:", COLORS['text'], 0.6),
            ("  Ctrl+Z / Ctrl+Y - Undo / Redo", COLORS['text_dim'], 0.5),
            ("  S - Save to rois.json", COLORS['text_dim'], 0.5),
            ("  D - Delete selected ROI", COLORS['text_dim'], 0.5),
            ("  N - Rename selected ROI", COLORS['text_dim'], 0.5),
            ("  O - Toggle OCR preview", COLORS['text_dim'], 0.5),
            ("  H - Toggle this help", COLORS['text_dim'], 0.5),
            ("  Q - Quit", COLORS['text_dim'], 0.5)
        ]
        
        box_width = 400
        line_height = 28
        box_height = len(help_lines) * line_height + 40
        box_x = width - box_width - 20
        box_y = 70
        
        overlay = img.copy()
        cv2.rectangle(overlay, (box_x, box_y), (box_x + box_width, box_y + box_height),
                     COLORS['bg_dark'], -1)
        cv2.addWeighted(overlay, 0.95, img, 0.05, 0, img)
        
        cv2.rectangle(img, (box_x, box_y), (box_x + box_width, box_y + box_height),
                     COLORS['accent'], 2)
        
        for i, (text, color, scale) in enumerate(help_lines):
            y = box_y + 30 + i * line_height
            cv2.putText(img, text, (box_x + 15, y), cv2.FONT_HERSHEY_SIMPLEX,
                       scale, color, 1, cv2.LINE_AA)
    
    def draw_naming_prompt(self, img):
        """Draw naming prompt"""
        if self.mode != Mode.NAMING:
            return
        
        height, width = img.shape[:2]
        
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (width, height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)
        
        box_w, box_h = 600, 180
        box_x, box_y = width // 2 - box_w // 2, height // 2 - box_h // 2
        
        overlay2 = img.copy()
        cv2.rectangle(overlay2, (box_x, box_y), (box_x + box_w, box_y + box_h),
                     COLORS['bg_medium'], -1)
        cv2.addWeighted(overlay2, 1.0, img, 0.0, 0, img)
        
        cv2.rectangle(img, (box_x, box_y), (box_x + box_w, box_y + box_h),
                     COLORS['accent'], 3)
        
        cv2.putText(img, "Enter ROI Name:", (box_x + 20, box_y + 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, COLORS['text'], 2, cv2.LINE_AA)
        
        input_text = self.naming_buffer + "_"
        cv2.putText(img, input_text, (box_x + 20, box_y + 110),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, COLORS['success'], 2, cv2.LINE_AA)
        
        cv2.putText(img, "Enter: Confirm  |  Esc: Cancel", (box_x + 20, box_y + 155),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['text_dim'], 1, cv2.LINE_AA)
    
    def update_ocr_cache(self):
        """Update OCR cache for all ROIs in background"""
        if not self.ocr_preview_enabled or len(self.rois) == 0:
            return
        
        # Don't update during drag operations to prevent jittery behavior
        if self.mode in (Mode.MOVING, Mode.RESIZING, Mode.DRAWING):
            return
        
        current_time = time.time()
        if current_time - self.last_ocr_update < 1.0:  # Update every second
            return
        
        self.last_ocr_update = current_time
        
        try:
            import pytesseract
            # Configure Tesseract path for Windows
            if sys.platform == "win32":
                pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            
            monitor = self.sct.monitors[1]
            screenshot = self.sct.grab(monitor)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            for name, roi in self.rois.items():
                left, top = roi['left'], roi['top']
                width, height = roi['width'], roi['height']
                
                # Extract ROI
                roi_img = img[top:top+height, left:left+width]
                
                # Preprocess for OCR
                gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                # Run OCR
                text = pytesseract.image_to_string(thresh, config='--psm 6').strip()
                
                with self.ocr_lock:
                    self.ocr_cache[name] = text if text else "[No text detected]"
            
            # Clear error if successful
            with self.ocr_lock:
                if "error" in self.ocr_cache:
                    del self.ocr_cache["error"]
                    
        except ImportError:
            with self.ocr_lock:
                self.ocr_cache["error"] = "pytesseract not installed or configured"
        except Exception as e:
            with self.ocr_lock:
                self.ocr_cache["error"] = f"OCR Error: {str(e)}"
    
    def handle_key(self, key):
        if key == -1 or key == self.last_key:
            return False
        
        self.last_key = key
        
        if self.mode == Mode.NAMING:
            if key == 13:  # Enter
                if self.naming_buffer.strip():
                    cmd = CreateROICommand(self.naming_buffer.strip(), self.temp_roi)
                    self.execute_command(cmd)
                    self.selected_roi = self.naming_buffer.strip()
                    self.show_feedback(f"Created: {self.naming_buffer.strip()}", 40)
                    # Trigger scale animation
                    self.roi_scale_animation[self.naming_buffer.strip()] = 0
                else:
                    self.show_feedback("Cancelled", 30)
                self.temp_roi = None
                self.naming_buffer = ""
                self.mode = Mode.IDLE
            elif key == 27:  # Esc
                self.show_feedback("Cancelled", 30)
                self.temp_roi = None
                self.naming_buffer = ""
                self.mode = Mode.IDLE
            elif key == 8:  # Backspace
                self.naming_buffer = self.naming_buffer[:-1]
            elif 32 <= key <= 126:
                if len(self.naming_buffer) < 30:
                    self.naming_buffer += chr(key)
        else:
            # Check for Ctrl modifiers
            if key == 26:  # Ctrl+Z
                self.undo()
            elif key == 25:  # Ctrl+Y
                self.redo()
            elif key == ord('q'):
                self.ocr_running = False
                return True
            elif key == ord('s'):
                save_rois(self.rois)
                self.show_feedback("Saved!", 40)
                self.save_animation_timer = 30  # Trigger save animation
            elif key == ord('h'):
                self.show_help = not self.show_help
            elif key == ord('d'):
                if self.selected_roi and self.selected_roi in self.rois:
                    cmd = DeleteROICommand(self.selected_roi, self.rois[self.selected_roi].copy())
                    self.execute_command(cmd)
                    self.show_feedback(f"Deleted: {self.selected_roi}", 40)
                    self.selected_roi = None
            elif key == ord('o'):
                self.ocr_preview_enabled = not self.ocr_preview_enabled
                status = "enabled" if self.ocr_preview_enabled else "disabled"
                self.show_feedback(f"OCR preview {status}", 40)
                if self.ocr_preview_enabled:
                    self.last_ocr_update = 0  # Force immediate update
        
        return False
    
    def render(self):
        monitor = self.sct.monitors[1]
        screenshot = self.sct.grab(monitor)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        # Update OCR cache
        if self.ocr_preview_enabled:
            self.update_ocr_cache()
        
        # Draw ROIs
        for name, roi in self.rois.items():
            left, top = roi['left'], roi['top']
            width, height = roi['width'], roi['height']
            
            is_selected = (name == self.selected_roi)
            color = COLORS['selected'] if is_selected else COLORS['success']
            thickness = 3 if is_selected else 2
            
            # Scale animation on selection
            scale = 1.0
            if name in self.roi_scale_animation:
                anim_time = self.roi_scale_animation[name]
                if anim_time < 10:
                    # Pulse effect: grow then shrink back
                    scale = 1.0 + 0.05 * np.sin(anim_time * np.pi / 10)
                    self.roi_scale_animation[name] += 1
                else:
                    del self.roi_scale_animation[name]
            
            # Apply scale
            if scale != 1.0:
                center_x, center_y = left + width // 2, top + height // 2
                scaled_w, scaled_h = int(width * scale), int(height * scale)
                left = center_x - scaled_w // 2
                top = center_y - scaled_h // 2
                width, height = scaled_w, scaled_h
            
            # Pulse effect for selected ROI
            if is_selected and self.mode == Mode.IDLE:
                pulse = 1.0 + 0.03 * np.sin(self.animation_time * 0.1)
                thickness = int(3 * pulse)
            
            cv2.rectangle(img, (left, top), (left + width, top + height), color, thickness)
            
            # Label
            label_bg = img.copy()
            (tw, th), _ = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(label_bg, (left, top - 28), (left + tw + 12, top), color, -1)
            cv2.addWeighted(label_bg, 0.8, img, 0.2, 0, img)
            cv2.putText(img, name, (left + 6, top - 8), cv2.FONT_HERSHEY_SIMPLEX,
                       0.6, COLORS['text'], 2, cv2.LINE_AA)
            
            # Draw resize handles if selected
            if is_selected and self.mode == Mode.IDLE:
                handle_size = 8
                handles = [
                    (left, top), (left + width, top),
                    (left, top + height), (left + width, top + height),
                    (left + width//2, top), (left + width//2, top + height),
                    (left, top + height//2), (left + width, top + height//2)
                ]
                for hx, hy in handles:
                    cv2.circle(img, (hx, hy), handle_size, COLORS['handle'], -1)
                    cv2.circle(img, (hx, hy), handle_size, COLORS['bg_dark'], 2)
        
        # Draw temp ROI
        if self.temp_roi:
            roi = self.temp_roi
            cv2.rectangle(img, (roi['left'], roi['top']),
                         (roi['left'] + roi['width'], roi['top'] + roi['height']),
                         COLORS['accent'], 2)
        
        # Draw current drawing
        if self.mode == Mode.DRAWING and self.drawing_start and self.drawing_current:
            cv2.rectangle(img, self.drawing_start, self.drawing_current, 
                         COLORS['warning'], 2)
        
        # Draw UI
        self.draw_toolbar(img)
        self.draw_status_bar(img)
        self.draw_feedback(img)
        self.draw_ocr_panel(img)  # Draw OCR panel before help so help overlays it
        self.draw_help(img)
        self.draw_naming_prompt(img)
        
        # Scaling
        height, width = img.shape[:2]
        target_height = 900
        if height > target_height:
            self.scale_factor = target_height / height
            new_width = int(width * self.scale_factor)
            img = cv2.resize(img, (new_width, target_height))
        else:
            self.scale_factor = 1.0
        
        self.animation_time += 1
        return img
    
    def run(self):
        cv2.namedWindow('ROI Editor')
        cv2.setMouseCallback('ROI Editor', self.mouse_callback)
        
        print("ROI Editor Started - Press 'H' for help")
        
        while True:
            img = self.render()
            cv2.imshow('ROI Editor', img)
            
            key = cv2.waitKey(1) & 0xFF
            if self.handle_key(key):
                break
        
        cv2.destroyAllWindows()
        print("ROI Editor Closed")

def main():
    set_dpi_awareness()
    editor = ROIEditor()
    editor.run()

if __name__ == "__main__":
    main()
