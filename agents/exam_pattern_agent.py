"""
Exam Pattern Agent - Analyzes and predicts exam patterns
"""
import json
import os
import re
import pdfplumber


class ExamPatternAgent:
    """Agent for analyzing exam patterns and trends"""
    
    def __init__(self, state_manager):
        self.state_manager = state_manager
    
    def load_university_data(self, university_name):
        """
        Load exam patterns for specified university
        
        Args:
            university_name: Name of the university (e.g., 'JNTU', 'Osmania')
        
        Returns:
            dict: Exam pattern data
        """
        # Determine file path based on university name
        filename = f"{university_name.lower()}_mock.json"
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, "data", filename)
        
        # Load JSON data with safe fallback
        try:
            with open(file_path, 'r') as f:
                pattern_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Fallback to empty structure if file missing or invalid
            pattern_data = {"university": university_name, "topics": {}, "total_marks": 100}
        
        # Store in state
        self.state_manager.set('exam.pattern_data', pattern_data)
        
        return pattern_data
    
    def compute_historical_probabilities(self):
        """
        Calculate probability per topic based on historical marks
        
        Returns:
            dict: Topic probability map
        """
        # Read pattern data from state
        pattern_data = self.state_manager.get('exam.pattern_data')
        
        if not pattern_data:
            return {}
        
        topics = pattern_data.get('topics', {})
        total_marks = pattern_data.get('total_marks', 100)
        
        # Calculate probability for each topic
        probability_map = {}
        for topic, marks in topics.items():
            probability_map[topic] = marks / total_marks
        
        # Store in state
        self.state_manager.set('intelligence.exam_probability_map', probability_map)
        
        return probability_map
    
    def process_uploaded_paper(self, file_path):
        """
        Extract questions from uploaded exam paper PDF
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            list: Extracted questions
        """
        try:
            # Extract text from PDF
            full_text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
            
            # Improved regex split - handles first question and requires whitespace
            questions = re.split(r"\n?\d+\.\s", full_text)
            
            # Clean empty entries and strip whitespace
            cleaned_questions = [q.strip() for q in questions if q.strip()]
            
            return cleaned_questions
            
        except Exception:
            # Return empty list if processing fails
            return []
    
    def classify_questions_with_llm(self, questions, syllabus_topics, llm_client):
        """
        Classify questions to syllabus topics using LLM
        
        Args:
            questions: List of question strings
            syllabus_topics: List of topic names
            llm_client: Callable that takes prompt and returns LLM response text
        
        Returns:
            dict: Contains topic_counts and mapping
        """
        if not questions or not syllabus_topics:
            return {"topic_counts": {}, "mapping": {}}
        
        # Build prompt for LLM
        topics_str = ", ".join(syllabus_topics)
        questions_str = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        
        prompt = f"""You are analyzing exam questions. Classify each question to one of the given syllabus topics.

Syllabus Topics: {topics_str}

Questions:
{questions_str}

Return ONLY a JSON object mapping each question NUMBER to its topic:
{{
  "1": "Topic Name",
  "2": "Topic Name",
  ...
}}

Ensure each question number is mapped to exactly one topic from the syllabus list."""
        
        try:
            # Call LLM
            llm_response = llm_client(prompt)
            
            # Parse JSON from response
            # Try to extract JSON if wrapped in markdown code blocks
            response_text = llm_response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            index_mapping = json.loads(response_text)
            
            # Initialize counters
            topic_counts = {}
            for topic in syllabus_topics:
                topic_counts[topic] = 0
            
            # Convert index-based mapping to question-text mapping
            question_mapping = {}
            for idx_str, topic in index_mapping.items():
                try:
                    idx = int(idx_str) - 1  # Convert to 0-based index
                    if 0 <= idx < len(questions):
                        question_text = questions[idx]
                        question_mapping[question_text] = topic
                        
                        # Count topic frequency
                        if topic in topic_counts:
                            topic_counts[topic] += 1
                except (ValueError, IndexError):
                    # Skip invalid indices
                    continue
            
            return {
                "topic_counts": topic_counts,
                "mapping": question_mapping
            }
            
        except (json.JSONDecodeError, KeyError, AttributeError, IndexError):
            # Safe fallback on parsing errors
            return {"topic_counts": {}, "mapping": {}}
    
    def generate_final_exam_probability_map(self, uploaded_topic_counts=None):
        """
        Generate final exam probability map by merging historical and uploaded data
        
        Args:
            uploaded_topic_counts: Optional dict of topic counts from uploaded papers
        
        Returns:
            dict: Final probability map
        """
        # Read historical probabilities from state
        historical_prob = self.state_manager.get('intelligence.exam_probability_map') or {}
        
        # If no uploaded data, use historical directly
        if not uploaded_topic_counts:
            self.state_manager.set('intelligence.exam_probability_map', historical_prob)
            return historical_prob
        
        # Calculate total uploaded questions
        total_uploaded = sum(uploaded_topic_counts.values())
        
        if total_uploaded == 0:
            self.state_manager.set('intelligence.exam_probability_map', historical_prob)
            return historical_prob
        
        # Compute uploaded probabilities
        uploaded_prob = {}
        for topic, count in uploaded_topic_counts.items():
            uploaded_prob[topic] = count / total_uploaded
        
        # Merge probabilities
        final_prob = {}
        
        # Get all unique topics from both sources
        all_topics = set(historical_prob.keys()) | set(uploaded_prob.keys())
        
        for topic in all_topics:
            hist_p = historical_prob.get(topic, 0.0)
            upload_p = uploaded_prob.get(topic, 0.0)
            
            if topic in uploaded_prob and topic in historical_prob:
                # Merge: 60% uploaded, 40% historical
                final_prob[topic] = (upload_p * 0.6) + (hist_p * 0.4)
            elif topic in uploaded_prob:
                # Only in uploaded
                final_prob[topic] = upload_p
            else:
                # Only in historical
                final_prob[topic] = hist_p
        
        # Store final result back to state
        self.state_manager.set('intelligence.exam_probability_map', final_prob)
        
        return final_prob
    
    def predict_important_topics(self):
        """Predict high-priority topics based on historical data"""
        pass
    
    def get_question_distribution(self):
        """Get distribution of question types and marks"""
        pass
