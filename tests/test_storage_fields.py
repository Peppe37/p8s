"""
Tests for P8s storage fields: resize_image and validate_mime_type.
"""

import pytest
from io import BytesIO


class TestResizeImage:
    """Test image resize functionality."""

    def test_resize_image_import(self):
        """Test resize_image can be imported."""
        from p8s.storage.fields import resize_image

        assert resize_image is not None

    def test_resize_small_image_unchanged(self):
        """Test that small images are not resized."""
        from p8s.storage.fields import resize_image

        # Create a small test image (requires Pillow)
        try:
            from PIL import Image

            # Create 100x100 test image
            img = Image.new("RGB", (100, 100), color="red")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            # Resize with max_size larger than image
            result = resize_image(buffer.read(), max_size=(800, 600))

            # Verify output is BytesIO
            assert isinstance(result, BytesIO)

            # Check dimensions unchanged
            result_img = Image.open(result)
            assert result_img.size == (100, 100)
        except ImportError:
            pytest.skip("Pillow not installed")

    def test_resize_large_image(self):
        """Test that large images are resized."""
        try:
            from PIL import Image
            from p8s.storage.fields import resize_image

            # Create 1000x800 test image
            img = Image.new("RGB", (1000, 800), color="blue")
            buffer = BytesIO()
            img.save(buffer, format="JPEG")
            buffer.seek(0)

            # Resize to max 500x500
            result = resize_image(buffer.read(), max_size=(500, 500))

            # Check image was resized
            result_img = Image.open(result)
            width, height = result_img.size

            # Should fit within 500x500 maintaining aspect ratio
            assert width <= 500
            assert height <= 500
        except ImportError:
            pytest.skip("Pillow not installed")

    def test_resize_with_max_width_only(self):
        """Test resize with only max_width specified."""
        try:
            from PIL import Image
            from p8s.storage.fields import resize_image

            img = Image.new("RGB", (1000, 500), color="green")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            result = resize_image(buffer.read(), max_width=400)

            result_img = Image.open(result)
            assert result_img.size[0] == 400
            # Height should scale proportionally: 500 * (400/1000) = 200
            assert result_img.size[1] == 200
        except ImportError:
            pytest.skip("Pillow not installed")

    def test_resize_with_max_height_only(self):
        """Test resize with only max_height specified."""
        try:
            from PIL import Image
            from p8s.storage.fields import resize_image

            img = Image.new("RGB", (500, 1000), color="yellow")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            result = resize_image(buffer.read(), max_height=400)

            result_img = Image.open(result)
            assert result_img.size[1] == 400
            # Width should scale: 500 * (400/1000) = 200
            assert result_img.size[0] == 200
        except ImportError:
            pytest.skip("Pillow not installed")


class TestValidateMimeType:
    """Test MIME type validation functionality."""

    def test_validate_mime_type_import(self):
        """Test validate_mime_type can be imported."""
        from p8s.storage.fields import validate_mime_type

        assert validate_mime_type is not None

    def test_detect_jpeg(self):
        """Test JPEG detection from magic bytes."""
        from p8s.storage.fields import validate_mime_type

        # JPEG magic bytes
        jpeg_bytes = b"\xff\xd8\xff" + b"\x00" * 100

        mime = validate_mime_type(jpeg_bytes)
        assert mime == "image/jpeg"

    def test_detect_png(self):
        """Test PNG detection from magic bytes."""
        from p8s.storage.fields import validate_mime_type

        # PNG magic bytes
        png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        mime = validate_mime_type(png_bytes)
        assert mime == "image/png"

    def test_detect_gif(self):
        """Test GIF detection from magic bytes."""
        from p8s.storage.fields import validate_mime_type

        # GIF87a magic bytes
        gif_bytes = b"GIF87a" + b"\x00" * 100

        mime = validate_mime_type(gif_bytes)
        assert mime == "image/gif"

    def test_detect_pdf(self):
        """Test PDF detection from magic bytes."""
        from p8s.storage.fields import validate_mime_type

        # PDF magic bytes
        pdf_bytes = b"%PDF-1.4" + b"\x00" * 100

        mime = validate_mime_type(pdf_bytes)
        assert mime == "application/pdf"

    def test_validate_allowed_type(self):
        """Test validation with allowed types list."""
        from p8s.storage.fields import validate_mime_type

        jpeg_bytes = b"\xff\xd8\xff" + b"\x00" * 100

        mime = validate_mime_type(jpeg_bytes, allowed_types=["image/jpeg", "image/png"])
        assert mime == "image/jpeg"

    def test_validate_disallowed_type_raises(self):
        """Test that disallowed type raises ValueError."""
        from p8s.storage.fields import validate_mime_type

        jpeg_bytes = b"\xff\xd8\xff" + b"\x00" * 100

        with pytest.raises(ValueError, match="not allowed"):
            validate_mime_type(jpeg_bytes, allowed_types=["image/png"])

    def test_unknown_type_raises(self):
        """Test that unknown file type raises ValueError when allowed_types specified."""
        from p8s.storage.fields import validate_mime_type

        random_bytes = b"\x00\x01\x02\x03" + b"\x00" * 100

        with pytest.raises(ValueError, match="Unknown file type"):
            validate_mime_type(random_bytes, allowed_types=["image/jpeg"])

    def test_bytesio_input(self):
        """Test that BytesIO input works correctly."""
        from p8s.storage.fields import validate_mime_type

        jpeg_bytes = b"\xff\xd8\xff" + b"\x00" * 100
        buffer = BytesIO(jpeg_bytes)

        mime = validate_mime_type(buffer)
        assert mime == "image/jpeg"


class TestMimeSignatures:
    """Test MIME signatures dictionary."""

    def test_mime_signatures_exist(self):
        """Test MIME_SIGNATURES dict is exported."""
        from p8s.storage.fields import MIME_SIGNATURES

        assert MIME_SIGNATURES is not None
        assert len(MIME_SIGNATURES) > 0

    def test_common_image_formats_supported(self):
        """Test common image formats are in signatures."""
        from p8s.storage.fields import MIME_SIGNATURES

        mimes = set(MIME_SIGNATURES.values())
        assert "image/jpeg" in mimes
        assert "image/png" in mimes
        assert "image/gif" in mimes
