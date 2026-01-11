"""
P8s Error Pages - Django-style error page rendering.

In DEBUG mode: Shows detailed error info with stack traces.
In PRODUCTION mode: Shows generic, styled error pages.
"""

import html
import traceback
from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse

# P8s Color Palette
P8S_COLORS = {
    "primary": "#f97316",
    "primary_hover": "#ea580c",
    "bg_dark": "#0a0a0a",
    "bg_secondary": "#141414",
    "bg_tertiary": "#1f1f1f",
    "bg_card": "#181818",
    "text_primary": "#fafafa",
    "text_secondary": "#a1a1aa",
    "text_muted": "#71717a",
    "border": "#27272a",
    "danger": "#ef4444",
    "danger_bg": "#450a0a",
    "success": "#22c55e",
}


def _get_base_styles() -> str:
    """Get base CSS styles with P8s palette."""
    return f"""
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: {P8S_COLORS["bg_dark"]};
            color: {P8S_COLORS["text_primary"]};
            min-height: 100vh;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        .error-header {{
            background: linear-gradient(135deg, {P8S_COLORS["danger"]}, {P8S_COLORS["primary"]});
            padding: 2rem;
            border-radius: 1rem 1rem 0 0;
        }}
        .error-code {{
            font-size: 4rem;
            font-weight: 800;
            opacity: 0.3;
            margin-bottom: 0.5rem;
        }}
        .error-title {{
            font-size: 1.5rem;
            font-weight: 700;
        }}
        .error-message {{
            font-size: 1.1rem;
            opacity: 0.9;
            margin-top: 0.5rem;
        }}
        .error-body {{
            background: {P8S_COLORS["bg_secondary"]};
            border: 1px solid {P8S_COLORS["border"]};
            border-top: none;
            border-radius: 0 0 1rem 1rem;
            padding: 2rem;
        }}
        .section {{
            margin-bottom: 2rem;
        }}
        .section-title {{
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: {P8S_COLORS["primary"]};
            margin-bottom: 1rem;
            font-weight: 600;
        }}
        .traceback {{
            background: {P8S_COLORS["bg_dark"]};
            border: 1px solid {P8S_COLORS["border"]};
            border-radius: 0.5rem;
            overflow: hidden;
        }}
        .frame {{
            border-bottom: 1px solid {P8S_COLORS["border"]};
            padding: 1rem;
        }}
        .frame:last-child {{
            border-bottom: none;
        }}
        .frame.current {{
            background: {P8S_COLORS["danger_bg"]};
        }}
        .frame-location {{
            font-size: 0.875rem;
            color: {P8S_COLORS["text_secondary"]};
            margin-bottom: 0.5rem;
        }}
        .frame-file {{
            color: {P8S_COLORS["primary"]};
        }}
        .frame-line {{
            color: {P8S_COLORS["text_muted"]};
        }}
        .frame-function {{
            color: {P8S_COLORS["success"]};
            font-weight: 600;
        }}
        .code-block {{
            background: {P8S_COLORS["bg_tertiary"]};
            border-radius: 0.25rem;
            padding: 0.75rem 1rem;
            font-family: 'Fira Code', 'Monaco', monospace;
            font-size: 0.875rem;
            overflow-x: auto;
            color: {P8S_COLORS["text_primary"]};
        }}
        .info-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .info-table th,
        .info-table td {{
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid {P8S_COLORS["border"]};
        }}
        .info-table th {{
            background: {P8S_COLORS["bg_tertiary"]};
            color: {P8S_COLORS["text_secondary"]};
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 600;
        }}
        .info-table td {{
            font-family: 'Fira Code', monospace;
            font-size: 0.875rem;
        }}
        .info-table td:first-child {{
            color: {P8S_COLORS["primary"]};
            white-space: nowrap;
            width: 200px;
        }}
        .home-link {{
            display: inline-block;
            margin-top: 1.5rem;
            padding: 0.75rem 1.5rem;
            background: {P8S_COLORS["primary"]};
            color: white;
            text-decoration: none;
            border-radius: 0.5rem;
            font-weight: 600;
            transition: 0.2s;
        }}
        .home-link:hover {{
            background: {P8S_COLORS["primary_hover"]};
        }}
        .footer {{
            text-align: center;
            padding: 2rem;
            color: {P8S_COLORS["text_muted"]};
            font-size: 0.875rem;
        }}
        .logo {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }}
        .logo img {{
            height: 32px;
        }}
        .logo span {{
            font-weight: 700;
            font-size: 1.25rem;
        }}
        
        /* Production page specific */
        .production-error {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            text-align: center;
            padding: 2rem;
        }}
        .production-code {{
            font-size: 8rem;
            font-weight: 800;
            background: linear-gradient(135deg, {P8S_COLORS["primary"]}, {P8S_COLORS["danger"]});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1;
            margin-bottom: 1rem;
        }}
        .production-title {{
            font-size: 1.5rem;
            color: {P8S_COLORS["text_primary"]};
            margin-bottom: 0.5rem;
        }}
        .production-message {{
            color: {P8S_COLORS["text_secondary"]};
            margin-bottom: 2rem;
            max-width: 400px;
        }}
    </style>
    """


def render_debug_error(
    request: Request,
    exc: Exception,
    status_code: int = 500,
) -> HTMLResponse:
    """
    Render a detailed debug error page (Django-style).

    Shows full stack trace, request info, and local variables.
    Only use when DEBUG=True.
    """
    # Get exception info
    exc_type = type(exc).__name__
    exc_message = str(exc)

    # Get formatted traceback
    tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)

    # Parse traceback for structured display
    frames_html = ""
    tb = exc.__traceback__
    frame_list = []

    while tb is not None:
        frame = tb.tb_frame
        frame_list.append(
            {
                "filename": frame.f_code.co_filename,
                "lineno": tb.tb_lineno,
                "name": frame.f_code.co_name,
                "locals": {
                    k: repr(v)[:200]
                    for k, v in frame.f_locals.items()
                    if not k.startswith("__")
                },
            }
        )
        tb = tb.tb_next

    # Reverse to show most recent first
    for i, frame in enumerate(reversed(frame_list)):
        is_current = i == 0
        locals_html = ""
        if frame["locals"]:
            locals_items = "".join(
                f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>"
                for k, v in list(frame["locals"].items())[:10]
            )
            locals_html = f"""
            <div style="margin-top: 0.75rem;">
                <table class="info-table">
                    <thead><tr><th>Variable</th><th>Value</th></tr></thead>
                    <tbody>{locals_items}</tbody>
                </table>
            </div>
            """

        frames_html += f"""
        <div class="frame {"current" if is_current else ""}">
            <div class="frame-location">
                <span class="frame-file">{html.escape(frame["filename"])}</span>
                <span class="frame-line">line {frame["lineno"]}</span>
                in <span class="frame-function">{html.escape(frame["name"])}</span>
            </div>
            {locals_html}
        </div>
        """

    # Request info
    request_info = f"""
    <table class="info-table">
        <thead><tr><th>Key</th><th>Value</th></tr></thead>
        <tbody>
            <tr><td>Method</td><td>{html.escape(request.method)}</td></tr>
            <tr><td>URL</td><td>{html.escape(str(request.url))}</td></tr>
            <tr><td>Path</td><td>{html.escape(request.url.path)}</td></tr>
            <tr><td>Client</td><td>{html.escape(str(request.client.host) if request.client else "Unknown")}</td></tr>
        </tbody>
    </table>
    """

    # Headers
    headers_html = "".join(
        f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>"
        for k, v in request.headers.items()
    )
    headers_table = f"""
    <table class="info-table">
        <thead><tr><th>Header</th><th>Value</th></tr></thead>
        <tbody>{headers_html}</tbody>
    </table>
    """

    # Query params
    query_html = ""
    if request.query_params:
        query_items = "".join(
            f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>"
            for k, v in request.query_params.items()
        )
        query_html = f"""
        <div class="section">
            <h3 class="section-title">Query Parameters</h3>
            <table class="info-table">
                <thead><tr><th>Key</th><th>Value</th></tr></thead>
                <tbody>{query_items}</tbody>
            </table>
        </div>
        """

    content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>P8s Debugger | {status_code} - {exc_type}</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fira+Code&display=swap" rel="stylesheet">
        {_get_base_styles()}
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <img src="/p8s.svg" alt="P8s" onerror="this.style.display='none'">
                <span>P8s Debug</span>
            </div>
            
            <div class="error-header">
                <div class="error-code">{status_code}</div>
                <h1 class="error-title">{html.escape(exc_type)}</h1>
                <p class="error-message">{html.escape(exc_message)}</p>
            </div>
            
            <div class="error-body">
                <div class="section">
                    <h3 class="section-title">Traceback (most recent call first)</h3>
                    <div class="traceback">
                        {frames_html}
                    </div>
                </div>
                
                <div class="section">
                    <h3 class="section-title">Request Information</h3>
                    {request_info}
                </div>
                
                {query_html}
                
                <div class="section">
                    <h3 class="section-title">Headers</h3>
                    {headers_table}
                </div>
                
                <div class="section">
                    <h3 class="section-title">Full Traceback</h3>
                    <pre class="code-block">{html.escape("".join(tb_lines))}</pre>
                </div>
            </div>
        </div>
        
        <div class="footer">
            P8s Framework • Debug Mode
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=content, status_code=status_code)


def render_production_error(
    request: Request,
    status_code: int,
    title: str | None = None,
    message: str | None = None,
    templates_dir: Path | None = None,
) -> HTMLResponse:
    """
    Render a generic production error page.

    Checks for user override in templates/errors/{status_code}.html first.
    """
    # Default messages
    error_info = {
        400: ("Bad Request", "The request could not be understood by the server."),
        401: ("Unauthorized", "You need to log in to access this resource."),
        403: ("Forbidden", "You don't have permission to access this resource."),
        404: ("Not Found", "The page you're looking for doesn't exist."),
        405: ("Method Not Allowed", "This method is not allowed for this resource."),
        500: (
            "Internal Server Error",
            "Something went wrong on our end. We're working on it.",
        ),
        502: ("Bad Gateway", "The server received an invalid response."),
        503: ("Service Unavailable", "The service is temporarily unavailable."),
    }

    default_title, default_message = error_info.get(
        status_code, ("Error", "An error occurred.")
    )
    title = title or default_title
    message = message or default_message

    # Check for user override template
    if templates_dir:
        user_template = templates_dir / "errors" / f"{status_code}.html"
        if user_template.exists():
            try:
                content = user_template.read_text()
                # Simple template variable replacement
                content = content.replace("{{ status_code }}", str(status_code))
                content = content.replace("{{ title }}", title)
                content = content.replace("{{ message }}", message)
                content = content.replace("{{ path }}", request.url.path)
                return HTMLResponse(content=content, status_code=status_code)
            except Exception:
                pass  # Fall back to default

    content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{status_code} - {html.escape(title)}</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        {_get_base_styles()}
    </head>
    <body>
        <div class="production-error">
            <img src="/p8s.svg" alt="P8s" style="height: 48px; margin-bottom: 2rem;" onerror="this.style.display='none'">
            <div class="production-code">{status_code}</div>
            <h1 class="production-title">{html.escape(title)}</h1>
            <p class="production-message">{html.escape(message)}</p>
            <a href="/" class="home-link">← Back to Home</a>
        </div>
        
        <div class="footer">
            Powered by P8s Framework
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=content, status_code=status_code)


def render_debug_404(request: Request) -> HTMLResponse:
    """Render a debug 404 page with request details."""
    content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>P8s Debugger | 404 - Not Found</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        {_get_base_styles()}
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <img src="/p8s.svg" alt="P8s" onerror="this.style.display='none'">
                <span>P8s Debug</span>
            </div>
            
            <div class="error-header">
                <div class="error-code">404</div>
                <h1 class="error-title">Page Not Found</h1>
                <p class="error-message">The path <code>{html.escape(request.url.path)}</code> was not found on this server.</p>
            </div>
            
            <div class="error-body">
                <div class="section">
                    <h3 class="section-title">Request Details</h3>
                    <table class="info-table">
                        <thead><tr><th>Key</th><th>Value</th></tr></thead>
                        <tbody>
                            <tr><td>Method</td><td>{html.escape(request.method)}</td></tr>
                            <tr><td>URL</td><td>{html.escape(str(request.url))}</td></tr>
                            <tr><td>Path</td><td>{html.escape(request.url.path)}</td></tr>
                        </tbody>
                    </table>
                </div>
                
                <a href="/" class="home-link">← Back to Home</a>
            </div>
        </div>
        
        <div class="footer">
            P8s Framework • Debug Mode
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=content, status_code=404)
