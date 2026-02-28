"""
Shared State Manager - Central state management for all agents
"""
import json
import os
from datetime import datetime


class StateManager:
    """Centralized state management for the exam preparation system"""
    
    def __init__(self):
        self.file_path = "state_backup.json"
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
                "generated_sprints": {},
                "schedule": [],
                "submission_history": {},
                "submission_locked": {}
            },
            
            # Intelligence and analytics
            "intelligence": {
                "topics": [],
                "confidence_scores": {},
                "exam_probability_map": {},
                "priority_scores": {},
                "psi": 0.0,
                "preparedness_score": 0.0
            },
            
            # Notes and revision
            "notes_chunks": None,
            "notes_index": None,
            "notes_file_name": None,
            "revision_notes": None,
            "revision_cache_meta": None
        }
        
        # Load persisted state if available
        self.load_from_file()
    
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
        self.save_to_file()
    
    def update(self, category, updates):
        """
        Update multiple fields in a category
        
        Args:
            category: Top-level category (e.g., 'user', 'progress')
            updates: Dictionary of updates
        """
        if category in self.state:
            self.state[category].update(updates)
        self.save_to_file()
    
    def reset(self):
        """Reset state to initial values"""
        self.__init__()
    
    def get_state(self):
        """Get entire state dictionary"""
        return self.state
    
    def save_to_file(self):
        """Save state to JSON file"""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save state: {str(e)}")  # Don't crash, just warn
    
    def load_from_file(self):
        """Load state from JSON file if it exists"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    loaded_state = json.load(f)
                    self.state = loaded_state
        except Exception:
            pass  # Keep default state on error
