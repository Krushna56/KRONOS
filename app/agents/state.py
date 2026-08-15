class AgentState:
    def __init__(self):
        self.current_step_index = 0
        self.steps = []
        self.results = {}
        self.is_completed = False

    def reset(self):
        self.current_step_index = 0
        self.steps = []
        self.results = {}
        self.is_completed = False
