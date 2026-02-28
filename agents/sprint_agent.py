"""
Sprint Agent - Creates focused study sprints and schedules
"""
import json


class SprintAgent:
    """Agent for managing study sprints and time blocks"""
    
    def __init__(self, state_manager):
        self.state_manager = state_manager
    
    def generate_sprint(self, topic, llm_client):
        """
        Generate sprint content for a topic using LLM
        
        Args:
            topic: Topic name to generate sprint for
            llm_client: Callable that takes prompt and returns LLM response
        
        Returns:
            dict: Sprint content with summary, questions, and MCQs
        """
        # Build prompt for LLM
        prompt = f"""Generate exam preparation content for the topic: {topic}

Create a focused study sprint with the following components:

1. A concise 2-minute summary explaining the key concepts
2. Four active recall questions to test understanding
3. One scenario-based application question
4. Three multiple-choice questions (MCQs) with 4 options each

Return ONLY a JSON object in this exact format:
{{
  "summary": "2-minute concise explanation of the topic",
  "active_recall_questions": ["Question 1", "Question 2", "Question 3", "Question 4"],
  "application_question": "One scenario-based question that tests practical application",
  "mcqs": [
    {{
      "question": "MCQ question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"
    }},
    {{
      "question": "MCQ question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option B"
    }},
    {{
      "question": "MCQ question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option C"
    }}
  ]
}}

Ensure the content is exam-focused and concise."""
        
        try:
            # Call LLM
            llm_response = llm_client(prompt)
            
            # Parse JSON from response - handle markdown code blocks
            response_text = llm_response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            sprint_content = json.loads(response_text)
            
            # Add topic to sprint content
            sprint_content["topic"] = topic
            
            # Store in state
            self.state_manager.set('sprints.active_sprint', sprint_content)
            
            return sprint_content
            
        except (json.JSONDecodeError, KeyError, AttributeError, IndexError):
            # Safe fallback on parsing errors
            fallback_content = {
                "topic": topic,
                "summary": "",
                "active_recall_questions": [],
                "application_question": "",
                "mcqs": []
            }
            self.state_manager.set('sprints.active_sprint', fallback_content)
            return fallback_content
    
    def create_sprint(self, duration, topic):
        """
        Create a focused study sprint
        
        Args:
            duration: Sprint duration in minutes
            topic: Topic to focus on
        
        Returns:
            dict: Sprint configuration
        """
        pass
    
    def generate_schedule(self, available_hours):
        """Generate optimized study schedule"""
        pass
    
    def track_progress(self, sprint_id):
        """Track progress for a specific sprint"""
        pass
