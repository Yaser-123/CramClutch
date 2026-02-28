"""
Prioritization Agent - Prioritizes topics and study materials
"""


class PrioritizationAgent:
    """Agent for prioritizing study topics and resources"""
    
    def __init__(self, state_manager):
        self.state_manager = state_manager
    
    def generate_priority_ranking(self):
        """
        Generate priority ranking for topics based on multiple factors
        
        Returns:
            list: Ranked topics with scores, sorted by priority (descending)
        """
        # Read data from state
        exam_probability_map = self.state_manager.get('intelligence.exam_probability_map') or {}
        confidence_scores = self.state_manager.get('intelligence.confidence_scores') or {}
        psi = self.state_manager.get('intelligence.psi') or 0.0
        time_remaining_hours = self.state_manager.get('user.time_remaining_hours') or 24
        
        if not exam_probability_map:
            return []
        
        # Determine time boost based on remaining hours
        time_boost = 1.0 if time_remaining_hours <= 8 else 0.5
        
        # Calculate priority scores for each topic
        priority_scores = {}
        
        for topic, exam_prob in exam_probability_map.items():
            # Get confidence (default 0.5 if not available)
            confidence = confidence_scores.get(topic, 0.5)
            weakness = 1 - confidence
            
            # Calculate priority score
            priority_score = (
                (exam_prob * 0.4) +
                (weakness * 0.3) +
                (time_boost * 0.2) +
                (psi * 0.1)
            )
            
            priority_scores[topic] = priority_score
        
        # Store priority scores in state
        self.state_manager.set('intelligence.priority_scores', priority_scores)
        
        # Create ranked list sorted by score (descending)
        ranked_list = [
            {"topic": topic, "score": score}
            for topic, score in sorted(priority_scores.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # Store ranked topics list in state
        ranked_topics = [item["topic"] for item in ranked_list]
        self.state_manager.set('priorities.ranked_topics', ranked_topics)
        
        return ranked_list
    
    def calculate_roi(self, topic):
        """Calculate return on investment for studying a topic"""
        pass
    
    def filter_low_priority(self, threshold=0.3):
        """Filter out low-priority topics below threshold"""
        pass
