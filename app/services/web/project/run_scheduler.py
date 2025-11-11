import os
import sys

# Add the parent directory to sys.path so 'project' package is importable
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.insert(0, parent)

from project.app import create_app, scheduler

app = create_app()

with app.app_context():
    print("Starting dedicated APScheduler process...")
    scheduler.start()
    print("Scheduler running...")

    # keep process alive
    import time
    while True:
        time.sleep(3600)
