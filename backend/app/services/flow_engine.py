"""
FlowEngine - Core conversation flow management.

This is a D1 stub that implements basic stage transitions.
Full LLM integration will be added in D2.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.session import Session
    from app.models.message import Message
    from app.models.student import Student


# Conversation stages for the reflective agent
STAGES = {
    "greeting": {
        "description": "Initial greeting and rapport building",
        "next": "context_gathering",
        "prompts": [
            "Hello! I'm here to help you reflect on your robotics project. What would you like to discuss today?"
        ],
    },
    "context_gathering": {
        "description": "Understanding the student's current situation",
        "next": "problem_exploration",
        "prompts": [
            "Can you tell me more about what you're working on?",
            "What stage are you at with your project?",
        ],
    },
    "problem_exploration": {
        "description": "Exploring challenges and issues",
        "next": "guided_reflection",
        "prompts": [
            "What challenges are you facing right now?",
            "What's been the most difficult part?",
        ],
    },
    "guided_reflection": {
        "description": "Socratic questioning to promote thinking",
        "next": "solution_brainstorm",
        "prompts": [
            "Why do you think that might be happening?",
            "What have you tried so far?",
            "What would happen if you approached it differently?",
        ],
    },
    "solution_brainstorm": {
        "description": "Collaborative solution exploration",
        "next": "action_planning",
        "prompts": [
            "What are some possible approaches you could try?",
            "Which option feels most promising to you?",
        ],
    },
    "action_planning": {
        "description": "Concrete next steps",
        "next": "wrap_up",
        "prompts": [
            "What's one thing you could try next?",
            "How will you know if it's working?",
        ],
    },
    "wrap_up": {
        "description": "Session summary and closing",
        "next": None,  # Terminal stage
        "prompts": [
            "Great conversation! To summarize what we discussed...",
            "Is there anything else you'd like to reflect on before we wrap up?",
        ],
    },
}


class FlowEngine:
    """
    Manages conversation flow through stages.
    
    D1 Implementation: Simple keyword-based stage transitions.
    D2 will add: LLM integration, safety checks, adaptive responses.
    """

    def __init__(
        self,
        session: "Session",
        history: list["Message"],
        student: "Student",
    ):
        self.session = session
        self.history = history
        self.student = student
        self.current_stage = session.current_stage

    def process(self, user_input: str) -> tuple[str, str, bool]:
        """
        Process user input and generate response.
        
        Args:
            user_input: The user's message
            
        Returns:
            tuple: (response_content, new_stage, is_complete)
        """
        # D1: Simple echo + stage info response
        # D2: This will call the LLM with proper prompting
        
        stage_config = STAGES.get(self.current_stage, STAGES["greeting"])
        
        # Check if user wants to move on (simple keyword detection)
        advance_keywords = ["next", "continue", "move on", "yes", "okay", "done"]
        should_advance = any(kw in user_input.lower() for kw in advance_keywords)
        
        # Determine new stage
        new_stage = self.current_stage
        if should_advance and stage_config["next"]:
            new_stage = stage_config["next"]
        
        # Check if session is complete
        is_complete = new_stage == "wrap_up" and should_advance
        
        # Generate response
        new_stage_config = STAGES.get(new_stage, STAGES["greeting"])
        
        if is_complete:
            response = (
                f"Thank you for this reflection session, {self._get_name()}! "
                f"You've made great progress thinking through your project. "
                f"Good luck with your next steps!"
            )
        elif new_stage != self.current_stage:
            # Stage transition response
            response = (
                f"Great, let's move on. "
                f"{new_stage_config['prompts'][0]}"
            )
        else:
            # Stay in current stage - acknowledge and probe deeper
            response = self._generate_in_stage_response(user_input, stage_config)
        
        return response, new_stage, is_complete

    def _get_name(self) -> str:
        """Get student's preferred name."""
        return self.student.display_name or self.student.username

    def _generate_in_stage_response(self, user_input: str, stage_config: dict) -> str:
        """
        Generate a response that stays within the current stage.
        D1: Simple template response. D2: LLM-generated.
        """
        prompts = stage_config["prompts"]
        
        # Rotate through prompts based on message count in this stage
        stage_message_count = sum(
            1 for m in self.history 
            if m.stage_id == self.current_stage and m.role.value == "assistant"
        )
        prompt_idx = stage_message_count % len(prompts)
        
        # Build response
        acknowledgments = [
            "I hear you.",
            "That's interesting.",
            "I understand.",
            "Thank you for sharing that.",
        ]
        ack_idx = len(self.history) % len(acknowledgments)
        
        return f"{acknowledgments[ack_idx]} {prompts[prompt_idx]}"


# Stage order for reference
STAGE_ORDER = [
    "greeting",
    "context_gathering", 
    "problem_exploration",
    "guided_reflection",
    "solution_brainstorm",
    "action_planning",
    "wrap_up",
]
