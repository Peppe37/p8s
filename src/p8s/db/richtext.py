"""
P8s Rich Text Field - WYSIWYG content storage field.

Provides a field for storing rich text content that can be edited
with modern block-based or WYSIWYG editors in the admin.

Content is stored as structured JSON (compatible with Tiptap/Editor.js)
or sanitized HTML.

Example:
    ```python
    from p8s.db.richtext import RichTextField

    class Article(Model, table=True):
        title: str
        content: dict = RichTextField(editor="tiptap")
    ```
"""

from typing import Any

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field


def RichTextField(
    editor: str = "tiptap",
    output_format: str = "json",
    max_length: int | None = None,
    **kwargs: Any,
) -> Any:
    """
    Create a rich text field for storing formatted content.

    The field stores structured JSON content that can be rendered
    by frontend editors like Tiptap or Editor.js.

    Args:
        editor: Editor type hint for admin UI ("tiptap", "editorjs", "markdown")
        output_format: Storage format ("json" or "html")
        max_length: Maximum content length (for HTML format)
        **kwargs: Additional Field arguments

    Returns:
        SQLModel Field configured for rich text storage

    Example:
        ```python
        class BlogPost(Model, table=True):
            title: str
            body: dict = RichTextField(editor="tiptap")

        # Access content
        post.body  # {"type": "doc", "content": [...]}
        ```
    """
    # Store editor hint in field metadata for admin UI
    json_schema_extra = kwargs.pop("json_schema_extra", {})
    json_schema_extra.update({
        "x-richtext": True,
        "x-editor": editor,
        "x-format": output_format,
    })

    if output_format == "html":
        # Store as HTML string
        if max_length:
            return Field(
                default="",
                sa_column=Column(Text),
                json_schema_extra=json_schema_extra,
                **kwargs,
            )
        return Field(
            default="",
            sa_column=Column(Text),
            json_schema_extra=json_schema_extra,
            **kwargs,
        )

    # Store as JSON (default for structured editors)
    return Field(
        default={},
        sa_column=Column(JSON),
        json_schema_extra=json_schema_extra,
        **kwargs,
    )


def render_richtext(
    content: dict | str,
    output: str = "html",
) -> str:
    """
    Render rich text content to HTML or plain text.

    Supports Tiptap JSON format conversion.

    Args:
        content: Rich text content (JSON dict or HTML string)
        output: Output format ("html", "text", "markdown")

    Returns:
        Rendered content string
    """
    if isinstance(content, str):
        # Already HTML or text
        if output == "text":
            return _strip_html(content)
        return content

    if not content or not isinstance(content, dict):
        return ""

    # Handle Tiptap JSON format
    if content.get("type") == "doc":
        return _render_tiptap_nodes(content.get("content", []), output)

    # Handle Editor.js format
    if "blocks" in content:
        return _render_editorjs_blocks(content.get("blocks", []), output)

    return str(content)


def _render_tiptap_nodes(nodes: list, output: str) -> str:
    """Render Tiptap nodes to output format."""
    result = []

    for node in nodes:
        node_type = node.get("type", "")
        content = node.get("content", [])
        text = node.get("text", "")

        if node_type == "paragraph":
            inner = _render_tiptap_nodes(content, output)
            if output == "html":
                result.append(f"<p>{inner}</p>")
            else:
                result.append(inner + "\n")

        elif node_type == "heading":
            level = node.get("attrs", {}).get("level", 1)
            inner = _render_tiptap_nodes(content, output)
            if output == "html":
                result.append(f"<h{level}>{inner}</h{level}>")
            elif output == "markdown":
                result.append(f"{'#' * level} {inner}\n")
            else:
                result.append(inner + "\n")

        elif node_type == "text":
            marks = node.get("marks", [])
            formatted = text

            for mark in marks:
                mark_type = mark.get("type")
                if mark_type == "bold" and output == "html":
                    formatted = f"<strong>{formatted}</strong>"
                elif mark_type == "italic" and output == "html":
                    formatted = f"<em>{formatted}</em>"
                elif mark_type == "code" and output == "html":
                    formatted = f"<code>{formatted}</code>"
                elif mark_type == "link" and output == "html":
                    href = mark.get("attrs", {}).get("href", "")
                    formatted = f'<a href="{href}">{formatted}</a>'

            result.append(formatted)

        elif node_type == "bulletList":
            items = _render_tiptap_nodes(content, output)
            if output == "html":
                result.append(f"<ul>{items}</ul>")
            else:
                result.append(items)

        elif node_type == "orderedList":
            items = _render_tiptap_nodes(content, output)
            if output == "html":
                result.append(f"<ol>{items}</ol>")
            else:
                result.append(items)

        elif node_type == "listItem":
            inner = _render_tiptap_nodes(content, output)
            if output == "html":
                result.append(f"<li>{inner}</li>")
            else:
                result.append(f"- {inner}")

        elif node_type == "codeBlock":
            code = _render_tiptap_nodes(content, "text")
            lang = node.get("attrs", {}).get("language", "")
            if output == "html":
                result.append(f"<pre><code>{code}</code></pre>")
            elif output == "markdown":
                result.append(f"```{lang}\n{code}\n```\n")
            else:
                result.append(code)

        elif node_type == "blockquote":
            inner = _render_tiptap_nodes(content, output)
            if output == "html":
                result.append(f"<blockquote>{inner}</blockquote>")
            elif output == "markdown":
                lines = inner.split("\n")
                result.append("\n".join(f"> {line}" for line in lines))
            else:
                result.append(inner)

        elif node_type == "image":
            attrs = node.get("attrs", {})
            src = attrs.get("src", "")
            alt = attrs.get("alt", "")
            if output == "html":
                result.append(f'<img src="{src}" alt="{alt}" />')
            elif output == "markdown":
                result.append(f"![{alt}]({src})")

        elif node_type == "horizontalRule":
            if output == "html":
                result.append("<hr />")
            else:
                result.append("---\n")

    return "".join(result)


def _render_editorjs_blocks(blocks: list, output: str) -> str:
    """Render Editor.js blocks to output format."""
    result = []

    for block in blocks:
        block_type = block.get("type", "")
        data = block.get("data", {})

        if block_type == "paragraph":
            text = data.get("text", "")
            if output == "html":
                result.append(f"<p>{text}</p>")
            else:
                result.append(text + "\n")

        elif block_type == "header":
            text = data.get("text", "")
            level = data.get("level", 1)
            if output == "html":
                result.append(f"<h{level}>{text}</h{level}>")
            elif output == "markdown":
                result.append(f"{'#' * level} {text}\n")
            else:
                result.append(text + "\n")

        elif block_type == "list":
            items = data.get("items", [])
            style = data.get("style", "unordered")
            tag = "ol" if style == "ordered" else "ul"
            if output == "html":
                items_html = "".join(f"<li>{item}</li>" for item in items)
                result.append(f"<{tag}>{items_html}</{tag}>")
            else:
                for item in items:
                    result.append(f"- {item}\n")

        elif block_type == "code":
            code = data.get("code", "")
            if output == "html":
                result.append(f"<pre><code>{code}</code></pre>")
            else:
                result.append(f"```\n{code}\n```\n")

        elif block_type == "image":
            url = data.get("file", {}).get("url", data.get("url", ""))
            caption = data.get("caption", "")
            if output == "html":
                result.append(f'<figure><img src="{url}" /><figcaption>{caption}</figcaption></figure>')
            elif output == "markdown":
                result.append(f"![{caption}]({url})")

        elif block_type == "quote":
            text = data.get("text", "")
            caption = data.get("caption", "")
            if output == "html":
                result.append(f"<blockquote><p>{text}</p><cite>{caption}</cite></blockquote>")
            elif output == "markdown":
                result.append(f"> {text}\n> — {caption}\n")
            else:
                result.append(f'"{text}" — {caption}\n')

    return "".join(result)


def _strip_html(html: str) -> str:
    """Strip HTML tags from string."""
    import re
    clean = re.sub(r"<[^>]+>", "", html)
    return clean.strip()


__all__ = [
    "RichTextField",
    "render_richtext",
]
