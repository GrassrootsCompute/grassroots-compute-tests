class ReportError(Exception):
    """Raised by report modules for bad input. `code` is a short machine-readable string (CONVENTIONS.md section 3)."""

    def __init__(self, code, message):
        super().__init__(f"[{code}] {message}")
        self.code = code
