import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from src.vision import BaseOCRProvider

# Concrete implementation for testing abstract base class
class MockOCRProvider(BaseOCRProvider):
    def extract_text(self, image: np.ndarray) -> str:
        return "MOCKED_TEXT"

@pytest.fixture
def mock_ocr_provider():
    # Patch Config to provide ROIs
    with patch("src.vision.Config") as MockConfig:
        MockConfig.VISION_ROIS = {
            "roi1": {"top": 0, "left": 0, "width": 100, "height": 100},
            "roi2": {"top": 100, "left": 100, "width": 50, "height": 50}
        }
        # Also need to patch mss in __init__
        with patch("src.vision.mss.mss"):
            provider = MockOCRProvider()
            yield provider

def test_get_context_formats_correctly(mock_ocr_provider):
    """
    Test that get_context iterates ROIs, extracts text, and formats the result string.
    """
    # Mock the grab method of mss
    mock_ocr_provider.sct.grab = MagicMock(return_value=np.zeros((100, 100, 3), dtype=np.uint8))
    
    # Mock extract_text to return specific values based on calls if we wanted, 
    # but our MockOCRProvider just returns "MOCKED_TEXT".
    
    context = mock_ocr_provider.get_context()
    
    # We expect: "ROI1: 'MOCKED_TEXT' | ROI2: 'MOCKED_TEXT'"
    # Order might vary depending on dictionary order, but usually stable in modern python
    assert "ROI1: 'MOCKED_TEXT'" in context
    assert "ROI2: 'MOCKED_TEXT'" in context
    assert " | " in context

def test_get_context_empty_rois():
    """
    Test that it returns empty string if no ROIs configured.
    """
    with patch("src.vision.Config") as MockConfig:
        MockConfig.VISION_ROIS = {}
        with patch("src.vision.mss.mss"):
            provider = MockOCRProvider()
            assert provider.get_context() == ""

def test_get_context_handles_exceptions(mock_ocr_provider):
    """
    Test that it returns empty string if exception occurs during capture.
    """
    mock_ocr_provider.sct.grab = MagicMock(side_effect=Exception("Capture failed"))
    assert mock_ocr_provider.get_context() == ""

