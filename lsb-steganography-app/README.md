# LSB Steganography Mini-App

A simple desktop application built with Python Tkinter that allows you to hide text messages inside PNG images using Least Significant Bit (LSB) steganography, and later recover them.

## Features

- **Encode Tab**: Select a PNG image, enter a secret message, and save a new image with the hidden message
- **Decode Tab**: Select an image that contains a hidden message and extract the text
- **User-Friendly Interface**: Clean, simple layout suitable for beginners
- **Feedback System**: Clear status messages for success and error conditions
- **PNG Optimized**: Works best with PNG images (lossless format preserves hidden data)

## Requirements

- Python 3.x
- Pillow library (PIL fork)

## Installation

1. Clone or download this repository
2. Install the required dependency:
   ```bash
   pip install -r requirements.txt
   ```
   or manually:
   ```bash
   pip install pillow
   ```

## Usage

1. Run the application:
   ```bash
   python steg_app.py
   ```

2. **To Encode a Message**:
   - Go to the "Encode" tab
   - Click "Browse..." to select a PNG image
   - Type your secret message in the text box
   - Click "Encode → Save"
   - The application will save a new image with "_encoded" suffix containing your hidden message

3. **To Decode a Message**:
   - Go to the "Decode" tab
   - Click "Browse..." to select an image that contains a hidden message
   - Click "Decode → Show"
   - The hidden message will appear in the text box below

## How It Works

This application uses Least Significant Bit (LSB) steganography:
- It modifies the least significant bit of each color channel (Red, Green, Blue) in the image pixels
- These changes are visually imperceptible but can store binary data
- A 32-bit length prefix is added to know where the message ends
- The message is encoded in UTF-8 format

## Capacity Calculation

Each pixel can store 3 bits (one per color channel):
- Maximum message length in bits = (image_width × image_height × 3) - 32
- Maximum message length in characters = floor(max_bits / 8)

For example, a 100×100 pixel image can store approximately:
- (100 × 100 × 3 - 32) / 8 = 373 characters

## Notes

- **PNG Recommended**: Use PNG format as it's lossless and won't compress away the hidden data
- **JPEG Warning**: JPEG compression will destroy the hidden data due to its lossy nature
- **File Size**: The encoded image will be the same size as the original
- **Security**: This is for educational purposes only - not suitable for serious cryptographic security

## Troubleshooting

- **"Image is too small" error**: Try a larger image or a shorter message
- **"Only PNG images are supported"**: Convert your image to PNG format first
- **No message extracted**: Make sure you're using an image that was actually encoded with this application

## License

This project is open source and available for personal and educational use.

---

*Built with Python Tkinter and Pillow*