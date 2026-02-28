"""
Shared State Manager - Central state management for all agents
"""
from datetime import datetime


class StateManager:
    """Centralized state management for the exam preparation system"""
    
    def __init__(self):
        self.state = {
            # User profile
            "user": {
                "name": None,
                "university": None,
                "exam_date": None,
                "time_remaining_hours": None
            },
            
            # Exam configuration
            "exam": {
                "subject": None,
                "total_units": 5,
                "total_marks": 100,
                "pattern_data": None
            },
            
            # Study progress
            "progress": {
                "completed_topics": [],
                "current_sprint": None,
                "total_study_time": 0,
                "syllabus_coverage": 0.0
            },
            
            # Prioritization data
            "priorities": {
                "ranked_topics": [],
                "high_priority_count": 0,
                "excluded_topics": []
            },
            
            # Crisis status
            "crisis": {
                "level": "normal",  # normal, moderate, high, critical
                "emergency_mode": False,
                "last_assessment": None
            },
            
            # Retention tracking
            "retention": {
                "revision_schedule": {},
                "mastery_levels": {},
                "weak_areas": []
            },
            
            # Sprint management
            "sprints": {
                "active_sprint": None,
                "completed_sprints": [],
                "schedule": []
            },
            
            # Intelligence and analytics
            "intelligence": {
                "topics": [],
                "confidence_scores": {},
                "exam_probability_map": {},
                "priority_scores": {},
                "psi": 0.0,
                "preparedness_score": 0.0
            }
        }
    
    def get(self, key_path):
        """
        Get value from state using dot notation
        
        Args:
            key_path: String path like 'user.name' or 'progress.completed_topics'
        
        Returns:
            Value at the specified path
        """
        keys = key_path.split('.')
        value = self.state
        for key in keys:
            value = value.get(key)
            if value is None:
                return None
        return value
    
    def set(self, key_path, value):
        """
        Set value in state using dot notation
        
        Args:
            key_path: String path like 'user.name'
            value: Value to set
        """
        keys = key_path.split('.')
        target = self.state
        for key in keys[:-1]:
            target = target[key]
        target[keys[-1]] = value
    
    def update(self, category, updates):
        """
        Update multiple fields in a category
        
        Args:
            category: Top-level category (e.g., 'user', 'progress')
            updates: Dictionary of updates
        """
        if category in self.state:
            self.state[category].update(updates)
    
    def reset(self):
        """Reset state to initial values"""
        self.__init__()
    
    def get_state(self):
        """Get entire state dictionary"""
        return self.state
