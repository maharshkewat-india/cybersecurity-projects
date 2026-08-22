# Usage Guide

## Quick Start

### 1. Encoding a Message

1. **Select a PNG image**: Use the "Browse..." button in the Encode tab to choose your cover image.
2. **Enter your secret**: Type the message you want to hide in the text box.
3. **Encode and Save**: Click "Encode → Save" to create the steganographic image.
4. **Verify success**: A confirmation message will show the filename of the saved image.

### 2. Decoding a Message

1. **Select an image**: Use "Browse..." in the Decode tab to choose the image containing hidden data.
2. **Extract the message**: Click "Decode → Show" to retrieve the hidden text.
3. **View the result**: The decoded message will appear in the text area below.

## Best Practices

### Image Selection
- **Format**: PNG images work best due to their lossless compression
- **Size**: Larger images provide more storage capacity
- **Avoid**: JPEG, GIF, and other lossy formats (data will be corrupted)

### Message Length Guidelines
- **Small images** (100×100): ~373 characters
- **Medium images** (500×500): ~18,700 characters  
- **Large images** (1000×1000): ~75,000 characters

## Troubleshooting

### "Image is too small" Error
- **Solution**: Use a larger image or shorten your message
- **Tip**: Try splitting large messages across multiple images

### "Only PNG images are supported" Error
- **Solution**: Convert your image to PNG format
- **Tools**: Use any image editor or command-line tools

### No Message Extracted
- **Cause**: Image wasn't encoded with this application
- **Fix**: Re-encode or try a different image

### Visual Integrity
The steganographic changes are visually imperceptible - you won't notice any difference in the image appearance.