# --- keep your existing imports above ---
import time
from typing import Optional
# Add these imports
try:
    from app.sse import notify, manager
    from app.task_control import task_manager
except Exception:
    from ..app.sse import notify, manager  # adjust if necessary
    from ..app.task_control import task_manager

def run(config_path: str, manager=None):
    """
    Training entrypoint. Emits progress via notify() (safe from sync code).
    Replace the sleep placeholders with your real training calls and keep notify() calls
    at major milestones or inside loops to stream progress to connected clients.
    """
    use_manager = manager
    task_id = None

    notify({"type": "progress", "task": "train", "pct": 0, "msg": "starting training", "task_id": task_id})

    # Model 1: Logistic Regression
    notify({"type": "progress", "task": "train", "pct": 10, "msg": "training logistic regression", "task_id": task_id})
    # Replace with real training call
    time.sleep(1.0)
    notify({"type": "progress", "task": "train", "pct": 30, "msg": "logistic regression done", "task_id": task_id})

    # Model 2: Decision Tree
    notify({"type": "progress", "task": "train", "pct": 35, "msg": "training decision tree", "task_id": task_id})
    time.sleep(1.0)
    notify({"type": "progress", "task": "train", "pct": 60, "msg": "decision tree done", "task_id": task_id})

    # Model 3: XGBoost
    notify({"type": "progress", "task": "train", "pct": 65, "msg": "training xgboost", "task_id": task_id})
    time.sleep(1.0)
    notify({"type": "progress", "task": "train", "pct": 90, "msg": "xgboost done", "task_id": task_id})

    # Evaluation / save metrics
    notify({"type": "progress", "task": "train", "pct": 95, "msg": "evaluating and saving metrics", "task_id": task_id})
    # save_metrics(...)
    notify({"type": "progress", "task": "train", "pct": 100, "msg": "training finished", "task_id": task_id, "result": {"metrics_path": "artifacts/metrics_sklearn.json"}})

    return