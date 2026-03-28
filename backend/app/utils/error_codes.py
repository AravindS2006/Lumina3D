from __future__ import annotations


def map_failure_code(exc: Exception) -> str:
    message = str(exc).lower()
    if "out of memory" in message or "cuda oom" in message:
        return "oom"
    if "no module named" in message or "import" in message:
        return "runtime_bootstrap_failed"
    if "open video" in message or "video" in message:
        return "video_input_error"
    if "timeout" in message:
        return "timeout"
    return "pipeline_failed"
