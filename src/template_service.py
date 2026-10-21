"""Production-ready Jinja2 template rendering and validation service."""

from typing import Any, Dict, Tuple, Optional
from jinja2 import Environment, BaseLoader, select_autoescape, TemplateSyntaxError, UndefinedError


class TemplateService:
    """Manages string-based dynamic Jinja2 template rendering with validation."""

    def __init__(self) -> None:
        self.env = Environment(
            loader=BaseLoader(),
            autoescape=select_autoescape(["html", "xml"]),
            enable_async=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(
        self,
        subject_template: str,
        body_template: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str]:
        """
        Renders subject and body template strings with the provided context dictionary.
        Returns (rendered_subject, rendered_body).
        """
        ctx = context or {}
        try:
            subject_tmpl = self.env.from_string(subject_template)
            body_tmpl = self.env.from_string(body_template)

            rendered_subject = subject_tmpl.render(**ctx)
            rendered_body = body_tmpl.render(**ctx)

            return rendered_subject.strip(), rendered_body.strip()
        except (TemplateSyntaxError, UndefinedError) as exc:
            raise ValueError(f"Template rendering failed: {str(exc)}") from exc

    def render_string(self, template_str: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Renders an isolated single template string."""
        ctx = context or {}
        tmpl = self.env.from_string(template_str)
        return tmpl.render(**ctx).strip()

    def validate_template_syntax(self, template_str: str) -> Tuple[bool, Optional[str]]:
        """
        Validates the syntax of a Jinja2 template string before persisting.
        Returns (is_valid: bool, error_message: Optional[str]).
        """
        try:
            self.env.parse(template_str)
            return True, None
        except TemplateSyntaxError as err:
            return False, f"Syntax error at line {err.lineno}: {err.message}"
