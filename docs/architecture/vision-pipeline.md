# Vision/OCR Pipeline

The vision pipeline captures screen regions and extracts text to provide game context for message generation.

## End-to-End Flow

1. **Context Request**
   - The bot asks the context observer for the current game context (e.g. before generating a message).

2. **ROI Configuration Check**
   - The observer checks whether any Regions of Interest (ROIs) are configured in `rois.json`.
   - **If no ROIs are configured**: it immediately returns an empty string as context.
   - **If ROIs are configured**: it proceeds to capture each region.

3. **Screen Capture per ROI**
   - For every configured ROI (e.g. `killfeed`, `score`, ...), the observer uses `mss.grab` to capture a screenshot of just that rectangle.
   - Each ROI produces a separate screenshot image in memory.

4. **Conversion to Arrays**
   - Each screenshot is converted into a NumPy array so it can be processed efficiently by OpenCV and the OCR engines.

5. **Preprocessing**
   - Each array passes through a preprocessing step that prepares it for OCR:
     - Convert from BGRA to grayscale.
     - Apply a binary (inverse) threshold with value 150 so game UI text becomes high contrast against the background.
   - Additional filters (blur, morphology, etc.) can be plugged in if needed.

6. **OCR Engine Selection and Text Extraction**
   - For each preprocessed ROI image, an OCR engine is invoked:
     - **EasyOCR** (default): deep-learning based, GPU-accelerated.
     - **Tesseract**: traditional OCR, typically run in `psm 7` mode for single-line text.
   - The engine returns extracted text for each ROI (e.g. `"Player eliminated Enemy"` for the killfeed region).

7. **Validation and Filtering**
   - Extracted text from each ROI is validated (e.g. non-empty, looks like plausible game data).
   - Invalid or empty results are skipped; valid ones move to the formatting step.

8. **Context String Assembly**
   - All valid ROI texts are combined into a single, human-readable context string, for example:
     - `"KILLFEED: Player eliminated Enemy | SCORE: 3-2"`.

9. **Analytics Tracking**
   - Timing and performance metrics for OCR are recorded so you can monitor how long each engine and ROI takes.

10. **Result Returned**
    - The final context string is returned to the bot and passed along to the message provider so generated messages can react to what just happened in-game.

## Configuration (rois.json)

```json
{
  "killfeed": {
    "left": 1500,
    "top": 100,
    "width": 400,
    "height": 300
  },
  "score": {
    "left": 800,
    "top": 50,
    "width": 200,
    "height": 50
  }
}
```

Use `debug_rois.py` to visually configure ROIs.

## OCR Engines

### EasyOCR (Default)
- **Pros**: More accurate, handles multiple languages, no external dependencies
- **Cons**: Slower initialization, requires more RAM, needs GPU for best performance
- **Use case**: Complex text, multiple languages, better accuracy needed

### Tesseract
- **Pros**: Faster, lightweight, well-tested
- **Cons**: Requires external binary installation, less accurate on complex text
- **Use case**: Simple UI text, controlled environments

## Preprocessing Pipeline

1. **Color Conversion**: BGRA → Grayscale
2. **Thresholding**: Binary inverse threshold (value: 150)
   - White text on dark background becomes black on white
   - Improves OCR accuracy for game UI
3. **Custom filters** (optional): Can add blur, morphology, etc.

## Performance Optimization

- **ROI Selection**: Only capture essential regions (not full screen)
- **Caching**: Vision results not cached (game state changes frequently)
- **Analytics**: Track processing time per engine
- **Async**: Vision runs in thread executor to avoid blocking

## Testing

```bash
# Test vision standalone
python tools/test_vision.py --engine easyocr --roi killfeed

# Compare engines
python tools/test_vision.py --compare --save

# List configured ROIs
python tools/test_vision.py --list-rois
```

## Integration with Message Generation

Vision context is passed to message provider:

```python
# Bot controller
context = await self.context_observer.get_context()
# context = "KILLFEED: Player eliminated Enemy"

# Provider receives context
message = await provider.get_message(
    mode="text",
    context_override=context
)
# Generates message relevant to killfeed event
```

## Future Enhancements

- **Template matching**: Detect icons, UI elements
- **Object detection**: Identify operators, gadgets
- **Confidence scores**: Only use high-confidence OCR results
- **Multi-monitor support**: Specify monitor per ROI

