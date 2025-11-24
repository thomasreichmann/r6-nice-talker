"""
Standalone Vision/OCR Testing Tool
Test OCR and vision processing without running the bot.
"""
import argparse
import sys
import time
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vision import TesseractProvider, EasyOCRProvider
from src.config import Config
from src.logging_config import setup_logging
import logging
import numpy as np
import cv2
import mss

logger = logging.getLogger(__name__)


def test_vision(
    engine: str = "easyocr",
    roi_name: str = None,
    show_preview: bool = True,
    save_output: bool = False,
    compare_engines: bool = False
) -> None:
    """
    Test OCR on screen regions.
    
    Args:
        engine: OCR engine to use ('easyocr' or 'tesseract')
        roi_name: Specific ROI to test (or None for all)
        show_preview: Show OpenCV preview windows
        save_output: Save captured and processed images
        compare_engines: Test both engines side-by-side
    """
    # Load ROIs
    if not Config.VISION_ROIS:
        logger.error("No ROIs configured in rois.json")
        logger.info("Run debug_rois.py to configure ROIs first")
        return
    
    # Filter ROIs if specific one requested
    if roi_name:
        if roi_name not in Config.VISION_ROIS:
            logger.error(f"ROI '{roi_name}' not found in rois.json")
            logger.info(f"Available ROIs: {', '.join(Config.VISION_ROIS.keys())}")
            return
        rois_to_test = {roi_name: Config.VISION_ROIS[roi_name]}
    else:
        rois_to_test = Config.VISION_ROIS
    
    logger.info(f"Testing {len(rois_to_test)} ROI(s)")
    
    # Initialize OCR provider(s)
    providers = []
    if compare_engines:
        logger.info("Comparison mode: Testing both EasyOCR and Tesseract")
        providers = [
            ("EasyOCR", EasyOCRProvider()),
            ("Tesseract", TesseractProvider())
        ]
    else:
        if engine == "easyocr":
            providers = [("EasyOCR", EasyOCRProvider())]
        else:
            providers = [("Tesseract", TesseractProvider())]
    
    # Capture and process each ROI
    with mss.mss() as sct:
        for roi_name, roi_region in rois_to_test.items():
            logger.info("-" * 60)
            logger.info(f"Testing ROI: {roi_name}")
            logger.info(f"Region: {roi_region}")
            
            try:
                # Capture
                screenshot = sct.grab(roi_region)
                img_np = np.array(screenshot)
                
                logger.info(f"Captured: {img_np.shape} ({img_np.dtype})")
                
                # Test with each provider
                for provider_name, provider in providers:
                    logger.info(f"\n[{provider_name}]")
                    
                    # Preprocess
                    start_preprocess = time.time()
                    processed = provider.preprocess_image(img_np)
                    preprocess_time = (time.time() - start_preprocess) * 1000
                    
                    logger.info(f"Preprocessing: {preprocess_time:.2f}ms")
                    
                    # Extract text
                    start_ocr = time.time()
                    text = provider.extract_text(processed)
                    ocr_time = (time.time() - start_ocr) * 1000
                    
                    logger.info(f"OCR Processing: {ocr_time:.2f}ms")
                    logger.info(f"Total Time: {preprocess_time + ocr_time:.2f}ms")
                    
                    if text and text.strip():
                        logger.info(f"✓ Detected Text: '{text.strip()}'")
                    else:
                        logger.warning("✗ No text detected")
                    
                    # Show preview if requested
                    if show_preview:
                        # Original
                        cv2.imshow(f"{roi_name} - Original", img_np)
                        # Processed
                        cv2.imshow(f"{roi_name} - Processed ({provider_name})", processed)
                    
                    # Save output if requested
                    if save_output:
                        output_dir = Path("vision_output")
                        output_dir.mkdir(exist_ok=True)
                        
                        orig_path = output_dir / f"{roi_name}_original.png"
                        proc_path = output_dir / f"{roi_name}_processed_{provider_name.lower()}.png"
                        
                        cv2.imwrite(str(orig_path), img_np)
                        cv2.imwrite(str(proc_path), processed)
                        
                        logger.info(f"✓ Saved: {orig_path} and {proc_path}")
                        
            except Exception as e:
                logger.error(f"Error processing ROI '{roi_name}': {e}", exc_info=True)
                continue
    
    # Wait for user to close preview windows
    if show_preview:
        logger.info("\nPress any key in preview window to continue...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    logger.info("\n" + "=" * 60)
    logger.info("Vision test complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Test OCR/vision without running the bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/test_vision.py --engine easyocr --roi killfeed
  python tools/test_vision.py --compare --save
  python tools/test_vision.py --list-rois
  python tools/test_vision.py --no-preview --save
        """
    )
    
    parser.add_argument(
        "--engine",
        choices=["easyocr", "tesseract"],
        default="easyocr",
        help="OCR engine to use (default: easyocr)"
    )
    
    parser.add_argument(
        "--roi",
        type=str,
        help="Test specific ROI only"
    )
    
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare both OCR engines side-by-side"
    )
    
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save captured and processed images to vision_output/"
    )
    
    parser.add_argument(
        "--no-preview",
        action="store_true",
        help="Don't show OpenCV preview windows"
    )
    
    parser.add_argument(
        "--list-rois",
        action="store_true",
        help="List all configured ROIs and exit"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    
    # List ROIs if requested
    if args.list_rois:
        try:
            with open("rois.json", "r") as f:
                rois = json.load(f)
            
            print("\nConfigured ROIs:")
            print("-" * 60)
            for name, region in rois.items():
                print(f"{name}:")
                print(f"  left={region['left']}, top={region['top']}")
                print(f"  width={region['width']}, height={region['height']}")
                print()
        except Exception as e:
            logger.error(f"Could not load ROIs: {e}")
        return
    
    # Run test
    try:
        test_vision(
            engine=args.engine,
            roi_name=args.roi,
            show_preview=not args.no_preview,
            save_output=args.save,
            compare_engines=args.compare
        )
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        cv2.destroyAllWindows()
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()

