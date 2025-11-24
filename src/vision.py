"""
Vision module for capturing and analyzing game state.
"""
import logging
import mss
import numpy as np
import cv2
import time
from src.config import Config
from src.interfaces import IContextObserver
import pytesseract
import easyocr

logger = logging.getLogger(__name__)

class BaseOCRProvider(IContextObserver):
    """
    Base class for OCR-based game state providers.
    Handles screen capture and ROI management.
    """
    def __init__(self) -> None:
        # Don't create mss instance here - create per-capture to avoid threading issues
        self.sct = None
        # ROIs will be loaded from Config
        self.rois = getattr(Config, "VISION_ROIS", {})

    def extract_text(self, image: np.ndarray) -> str:
        """
        Extract text from a preprocessed image.
        """
        raise NotImplementedError

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Basic preprocessing for OCR: Grayscale, Thresholding.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        # Simple binary thresholding often works best for game UI high contrast text
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        return thresh

    def get_context(self) -> str:
        """
        Captures specific ROIs and attempts to extract text.
        Returns a formatted string of what was found.
        """
        context_parts = []
        
        # If no ROIs defined, we can't do anything
        if not self.rois:
            return ""

        try:
            # Create mss instance per capture to avoid threading issues on Windows
            with mss.mss() as sct:
                # mss grab returns a raw object we can convert to numpy
                # We need to iterate over configured ROIs
                
                for name, region in self.rois.items():
                    # Capture
                    screenshot = sct.grab(region)
                    img_np = np.array(screenshot)
                
                # Preprocess
                processed_img = self.preprocess_image(img_np)
                
                # Extract with timing
                start_time = time.time()
                text = self.extract_text(processed_img)
                elapsed_ms = int((time.time() - start_time) * 1000)
                
                # Track analytics
                try:
                    from src.analytics import get_analytics
                    analytics = get_analytics()
                    analytics.track_ocr(
                        engine=self.__class__.__name__.replace('Provider', '').lower(),
                        processing_time_ms=elapsed_ms
                    )
                except Exception as e:
                    logger.debug(f"Analytics tracking failed: {e}")
                
                if text and len(text.strip()) > 2: # Filter noise
                    clean_text = text.strip().replace("\n", " ")
                    context_parts.append(f"{name.upper()}: '{clean_text}'")
                    logger.debug(f"Vision detected [{name}]: {clean_text}")

        except Exception as e:
            logger.error(f"Error during vision capture: {e}")
            return ""

        if not context_parts:
            return ""
            
        return " | ".join(context_parts)

class TesseractProvider(BaseOCRProvider):
    """
    OCR Provider using Google's Tesseract (requires external binary installation).
    """
    def __init__(self) -> None:
        super().__init__()
        # Set tesseract path from config or default to standard Windows path
        tess_path = getattr(Config, "TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        pytesseract.pytesseract.tesseract_cmd = tess_path
        
    def extract_text(self, image: np.ndarray) -> str:
        try:
            # psm 7 = Treat the image as a single text line.
            return pytesseract.image_to_string(image, config='--psm 7')
        except Exception as e:
            logger.error(f"Tesseract Error: {e}")
            return ""

class EasyOCRProvider(BaseOCRProvider):
    """
    OCR Provider using EasyOCR (Deep Learning based, heavier but easier setup).
    """
    def __init__(self) -> None:
        super().__init__()
        logger.info("Initializing EasyOCR... (this may take a moment)")
        # Initialize for English and Portuguese
        # gpu=True for better performance
        self.reader = easyocr.Reader(['en', 'pt'], gpu=True) 
        
    def extract_text(self, image: np.ndarray) -> str:
        try:
            # detail=0 returns just the list of text strings
            result = self.reader.readtext(image, detail=0)
            return " ".join(result)
        except Exception as e:
            logger.error(f"EasyOCR Error: {e}")
            return ""
