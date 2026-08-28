#!/usr/bin/env python3
"""
Test script for the LSB steganography functionality.
"""

import os
import tempfile
from PIL import Image
from steg_app import hide_message, extract_message

def create_test_image(width=200, height=200):
    """Create a simple test PNG image."""
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    return img

def test_encode_decode():
    """Test the encode/decode cycle."""
    print("Testing LSB steganography...")

    # Create test image
    test_img = create_test_image()
    test_message = "Hello, this is a secret message!"

    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = os.path.join(tmpdir, "test.png")
        encoded_path = os.path.join(tmpdir, "test_encoded.png")

        # Save test image
        test_img.save(img_path)

        # Test encoding
        print(f"Encoding message: '{test_message}'")
        hide_message(img_path, test_message, encoded_path)

        # Verify encoded file exists
        if not os.path.exists(encoded_path):
            print("FAIL: Encoded file was not created")
            return False

        # Test decoding
        print("Decoding message...")
        decoded_message = extract_message(encoded_path)

        # Verify decoded message matches original
        if decoded_message == test_message:
            print("PASS: Message encoded and decoded successfully!")
            print(f"Original: {test_message}")
            print(f"Decoded:  {decoded_message}")
            return True
        else:
            print("FAIL: Decoded message does not match original")
            print(f"Original: {test_message}")
            print(f"Decoded:  {decoded_message}")
            return False

def test_capacity_limits():
    """Test capacity limits."""
    print("\nTesting capacity limits...")

    # Small image (10x10 = 300 bits capacity)
    small_img = Image.new("RGB", (10, 10), color=(100, 150, 200))
    long_message = "A" * 100  # 800 bits needed

    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = os.path.join(tmpdir, "small.png")
        encoded_path = os.path.join(tmpdir, "small_encoded.png")
        small_img.save(img_path)

        try:
            hide_message(img_path, long_message, encoded_path)
            print("FAIL: Should have raised error for small image")
            return False
        except ValueError as e:
            print(f"PASS: Correctly rejected oversized message: {e}")
            return True

def test_utf8_support():
    """Test UTF-8 character support."""
    print("\nTesting UTF-8 support...")

    test_img = create_test_image()
    test_message = "Hello 世界! 🌍 こんにちは"

    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = os.path.join(tmpdir, "utf8.png")
        encoded_path = os.path.join(tmpdir, "utf8_encoded.png")
        test_img.save(img_path)

        hide_message(img_path, test_message, encoded_path)
        decoded_message = extract_message(encoded_path)

        if decoded_message == test_message:
            print("PASS: UTF-8 characters handled correctly")
            return True
        else:
            print("FAIL: UTF-8 decoding failed")
            print(f"Original: {test_message}")
            print(f"Decoded:  {decoded_message}")
            return False

def test_multiple_images():
    """Test with different image sizes."""
    print("\nTesting different image sizes...")

    test_message = "Test message"
    sizes = [(50, 50), (100, 100), (500, 500)]

    for width, height in sizes:
        img = Image.new("RGB", (width, height), color=(100, 150, 200))
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = os.path.join(tmpdir, f"test_{width}x{height}.png")
            encoded_path = os.path.join(tmpdir, f"test_{width}x{height}_encoded.png")
            img.save(img_path)

            try:
                hide_message(img_path, test_message, encoded_path)
                decoded = extract_message(encoded_path)
                if decoded == test_message:
                    print(f"PASS: {width}x{height} image works correctly")
                else:
                    print(f"FAIL: {width}x{height} image failed")
                    return False
            except Exception as e:
                print(f"FAIL: {width}x{height} image raised error: {e}")
                return False

    return True

if __name__ == "__main__":
    print("=" * 50)
    print("LSB Steganography Test Suite")
    print("=" * 50)

    tests = [
        test_encode_decode,
        test_capacity_limits,
        test_utf8_support,
        test_multiple_images,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"ERROR in {test.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 50)

    exit(0 if failed == 0 else 1)