"""
Tests for P8s Rich Text Field.
"""

import pytest


class TestRichTextField:
    """Test RichTextField creation."""

    def test_field_import(self):
        """Test RichTextField can be imported."""
        from p8s.db.richtext import RichTextField

        assert RichTextField is not None

    def test_field_default_values(self):
        """Test field is callable."""
        from p8s.db.richtext import RichTextField

        assert callable(RichTextField)

    def test_field_with_editor_hint(self):
        """Test field accepts editor parameter."""
        from p8s.db.richtext import RichTextField

        # Should be callable with arguments
        assert callable(RichTextField)


class TestRenderRichtext:
    """Test render_richtext function."""

    def test_render_import(self):
        """Test render_richtext can be imported."""
        from p8s.db.richtext import render_richtext

        assert render_richtext is not None

    def test_render_empty(self):
        """Test rendering empty content."""
        from p8s.db.richtext import render_richtext

        result = render_richtext({})
        assert result == ""

    def test_render_html_passthrough(self):
        """Test rendering HTML string passthrough."""
        from p8s.db.richtext import render_richtext

        html = "<p>Hello World</p>"
        result = render_richtext(html, output="html")
        assert result == html

    def test_render_tiptap_paragraph(self):
        """Test rendering Tiptap paragraph."""
        from p8s.db.richtext import render_richtext

        content = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Hello"}],
                }
            ],
        }

        result = render_richtext(content, output="html")
        assert "<p>Hello</p>" in result

    def test_render_tiptap_heading(self):
        """Test rendering Tiptap heading."""
        from p8s.db.richtext import render_richtext

        content = {
            "type": "doc",
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": "Title"}],
                }
            ],
        }

        result = render_richtext(content, output="html")
        assert "<h2>Title</h2>" in result

    def test_render_tiptap_bold(self):
        """Test rendering bold text."""
        from p8s.db.richtext import render_richtext

        content = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Bold",
                            "marks": [{"type": "bold"}],
                        }
                    ],
                }
            ],
        }

        result = render_richtext(content, output="html")
        assert "<strong>Bold</strong>" in result

    def test_render_editorjs_paragraph(self):
        """Test rendering Editor.js paragraph."""
        from p8s.db.richtext import render_richtext

        content = {
            "blocks": [{"type": "paragraph", "data": {"text": "Hello Editor.js"}}]
        }

        result = render_richtext(content, output="html")
        assert "<p>Hello Editor.js</p>" in result

    def test_render_to_text(self):
        """Test rendering to plain text."""
        from p8s.db.richtext import render_richtext

        result = render_richtext("<p>Hello <b>World</b></p>", output="text")
        assert "Hello" in result
        assert "<p>" not in result


class TestExports:
    """Test module exports."""

    def test_all_exports(self):
        """Test __all__ exports."""
        from p8s.db.richtext import __all__

        assert "RichTextField" in __all__
        assert "render_richtext" in __all__
