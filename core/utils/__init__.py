# use try-except to avoid error when installing
try:
    from .ask_gpt import ask_gpt
    from .decorator import except_handler, check_file_exists
    from .config_utils import load_key, load_key_or, update_key, get_joiner, get_source_language
    from rich import print as rprint
except ImportError:
    pass


def check_cancel():
    """Cooperative cancellation hook for long-running core loops.

    Imports lazily to avoid coupling core scripts to the Streamlit-side
    TaskRunner. Becomes a no-op when no runner is active (CLI usage).
    """
    try:
        from core.st_utils.task_runner import TaskRunner
    except Exception:
        return
    TaskRunner.check_cancel()


__all__ = [
    "ask_gpt",
    "except_handler",
    "check_file_exists",
    "load_key",
    "load_key_or",
    "update_key",
    "rprint",
    "get_joiner",
    "get_source_language",
    "check_cancel",
]
