from app.core.logger import logger

class TaskScheduler:
    def __init__(self):
        logger.info("Task Scheduler system initialized")

    def schedule_cron_job(self, cron_expr: str, func) -> str:
        logger.info(f"Scheduled cron job '{func.__name__}' with expression: '{cron_expr}'")
        return "job_id_123"
