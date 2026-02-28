"""
Crisis Agent - Handles emergency study situations and time constraints
"""


class CrisisAgent:
    """Agent for managing crisis situations in exam preparation"""
    
    def __init__(self, state_manager):
        self.state_manager = state_manager
    
    def analyze_crisis(self):
        """
        Analyze the urgency level based on current state
        
        Returns:
            dict: Crisis analysis with psi, crisis_level, and recommendation
        """
        # Fetch data from state_manager
        time_remaining_hours = self.state_manager.get('user.time_remaining_hours') or 0
        syllabus_coverage = self.state_manager.get('progress.syllabus_coverage') or 0.0
        confidence_scores = self.state_manager.get('intelligence.confidence_scores') or {}
        
        # Calculate Time Pressure Score
        if time_remaining_hours <= 4:
            time_pressure = 1.0
        elif time_remaining_hours <= 8:
            time_pressure = 0.8
        elif time_remaining_hours <= 12:
            time_pressure = 0.6
        elif time_remaining_hours <= 24:
            time_pressure = 0.4
        else:
            time_pressure = 0.2
        
        # Calculate Coverage Gap
        coverage_gap = 1 - syllabus_coverage
        
        # Calculate Confidence Gap
        if confidence_scores:
            avg_confidence = sum(confidence_scores.values()) / len(confidence_scores)
            confidence_gap = 1 - avg_confidence
        else:
            confidence_gap = 0.5
        
        # Calculate PSI (Preparation Stress Index)
        psi = (time_pressure * 0.5) + (coverage_gap * 0.3) + (confidence_gap * 0.2)
        
        # Update state with PSI
        self.state_manager.set('intelligence.psi', psi)
        
        # Determine crisis level
        if psi >= 0.75:
            crisis_level = "critical"
            recommendation = "Emergency mode activated. Focus only on high-probability topics."
        elif psi >= 0.55:
            crisis_level = "high"
            recommendation = "High pressure. Prioritize core topics and skip low-value content."
        elif psi >= 0.35:
            crisis_level = "moderate"
            recommendation = "Moderate pressure. Maintain focus on prioritized topics."
        else:
            crisis_level = "normal"
            recommendation = "Good progress. Continue with planned schedule."
        
        # Update crisis state
        self.state_manager.set('crisis.level', crisis_level)
        
        return {
            "psi": psi,
            "crisis_level": crisis_level,
            "recommendation": recommendation
        }
    
    def generate_emergency_plan(self):
        """Generate emergency study plan for crisis situations"""
        pass
    
    def adjust_priorities(self):
        """Adjust study priorities based on crisis level"""
        pass
