from app.core.logger import logger

class AgentPlanner:
    @staticmethod
    def generate_plan(task_description: str) -> list:
        logger.info(f"Generating steps for: {task_description}")
        return [
            f"Step 1: Analyze user request '{task_description}'",
            "Step 2: Access context and memories",
            "Step 3: Generate result and respond"
        ]
