# --- keep your existing imports above ---
import time
# Add these imports
try:
    # prefer app imports relative to your package layout
    from app.sse import notify, manager
    from app.task_control import task_manager
except Exception:
    # fallback if running in different import context
    from ..app.sse import notify, manager  # adjust if necessary
    from ..app.task_control import task_manager

def run(manager=None):
    """
    Existing preprocess entrypoint — now emits progress events via the notify helper.
    If an async manager instance is passed, the function can use that but the default notify()
    works from synchronous code (schedules broadcasts onto the running loop).
    """
    use_manager = manager
    task_id = None  # populated by HTTP endpoint; kept None for local runs

    # start
    notify({"type": "progress", "task": "preprocess", "pct": 0, "msg": "starting preprocessing", "task_id": task_id})

    # Replace the sleeps and placeholders below with your real preprocessing steps.
    # Example step: load CSVs / merging
    # (replace with your actual load code)
    time.sleep(0.2)
    notify({"type": "progress", "task": "preprocess", "pct": 10, "msg": "loaded CSVs", "task_id": task_id})

    # Cleaning / feature engineering (example loop; replace with your logic)
    steps = ["clean", "feature_engineering", "encode"]
    for i, step in enumerate(steps):
        # perform your step here
        time.sleep(0.3)
        pct = 10 + int((i + 1) / len(steps) * 60)
        notify({"type": "progress", "task": "preprocess", "pct": pct, "msg": f"{step} done", "task_id": task_id})

        # If you want cancellation checks (when run via /preprocess endpoint),
        # the HTTP endpoint can pass the task_id into this function and then:
        # if await task_manager.is_cancelled(task_id): notify({...cancelled...}); return

    # Save processed CSV (replace with your saving logic)
    time.sleep(0.2)
    notify({"type": "progress", "task": "preprocess", "pct": 90, "msg": "saving processed CSV", "task_id": task_id})

    # Finalize
    notify({"type": "progress", "task": "preprocess", "pct": 100, "msg": "preprocess finished", "task_id": task_id, "result": {"processed_path": "data/processed/train.csv"}})

    # keep original return behavior if any
    return