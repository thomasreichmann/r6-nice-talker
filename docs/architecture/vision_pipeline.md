# Vision/OCR Pipeline

The vision pipeline captures screen regions and extracts text to provide game context for message generation.

```mermaid
graph TB
    Start[Bot requests context] --> Check{ROIs configured?}
    Check -->|No| Empty[Return empty string]
    Check -->|Yes| Capture[Capture screen regions]
    
    Capture --> ROI1[ROI: killfeed<br/>top: 100, left: 1500<br/>width: 400, height: 300]
    Capture --> ROI2[ROI: score<br/>top: 50, left: 800<br/>width: 200, height: 50]
    Capture --> ROIN[ROI: ...]
    
    ROI1 --> Screenshot1[mss.grab region]
    ROI2 --> Screenshot2[mss.grab region]
    ROIN --> ScreenshotN[mss.grab region]
    
    Screenshot1 --> Convert1[Convert to numpy array]
    Screenshot2 --> Convert2[Convert to numpy array]
    ScreenshotN --> ConvertN[Convert to numpy array]
    
    Convert1 --> Pre1[Preprocess]
    Convert2 --> Pre2[Preprocess]
    ConvertN --> PreN[Preprocess]
    
    subgraph "Preprocessing Steps"
        Pre1 --> Gray1[Convert to grayscale]
        Gray1 --> Thresh1[Binary threshold<br/>value: 150]
    end
    
    Thresh1 --> OCR1{OCR Engine}
    Pre2 --> OCR2{OCR Engine}
    PreN --> OCRN{OCR Engine}
    
    OCR1 -->|EasyOCR| Easy1[Deep learning model<br/>GPU accelerated]
    OCR1 -->|Tesseract| Tess1[Traditional OCR<br/>psm 7 mode]
    
    Easy1 --> Text1[Extracted text:<br/>'Player eliminated Enemy']
    Tess1 --> Text1
    
    OCR2 --> Text2[Extracted text]
    OCRN --> TextN[Extracted text]
    
    Text1 --> Filter{Text valid?}
    Text2 --> Filter
    TextN --> Filter
    
    Filter -->|Yes| Format[Format context string]
    Filter -->|No| Skip[Skip this ROI]
    
    Format --> Analytics[Track OCR timing]
    Analytics --> Result[Return context:<br/>'KILLFEED: Player eliminated Enemy | SCORE: 3-2']
    
    Skip --> Result
    
    style Pre1 fill:#e1f5ff
    style Easy1 fill:#ffe1e1
    style Tess1 fill:#ffe1e1
```

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

