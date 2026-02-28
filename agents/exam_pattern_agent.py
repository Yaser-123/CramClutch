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
    
    def process_text_to_questions(self, text):
        """
        Extract questions from text (from PDF or manual paste)
        
        Args:
            text: Raw text containing questions
        
        Returns:
            list: Extracted questions
        """
        # Clean up common noise patterns
        lines = text.split('\n')
        cleaned_lines = []
        
        # Noise patterns to skip
        noise_patterns = [
            r'^Page \d+',
            r'^\*+$',
            r'^Code No:',
            r'COLLEGE|UNIVERSITY|ENGINEERING',
            r'Autonomous.*Institution',
            r'B\.Tech.*Semester',
            r'Examinations.*\d{4}',
            r'^\s*R\d+\s*$',
            r'^Time:.*Marks',
            r'Note:.*'
        ]
        
        for line in lines:
            line = line.strip()
            # Skip empty lines
            if not line:
                continue
            # Skip noise patterns
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in noise_patterns):
                continue
            cleaned_lines.append(line)
        
        # Rejoin cleaned text
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Split by question numbers - multiple patterns
        # Pattern: "1." or "Q1." or "Question 1."
        questions = re.split(r'\n(?:Q(?:uestion)?\s*)?(\d+)[.)]\s+', cleaned_text)
        
        # The split creates alternating question numbers and content
        # Combine them properly
        cleaned_questions = []
        for i in range(1, len(questions), 2):
            if i + 1 <= len(questions):
                question_text = questions[i + 1].strip()
                # Only keep substantial questions (more than 20 chars)
                if len(question_text) > 20:
                    cleaned_questions.append(question_text)
        
        # If no questions found with numbered pattern, try alternative method
        if not cleaned_questions:
            # Look for lines that seem like questions (contain "?" or end with certain keywords)
            question_indicators = [
                r'\?',  # Contains question mark
                r'\bexplain\b',
                r'\bdescribe\b',
                r'\bcompare\b',
                r'\bdiscuss\b',
                r'\bwrite\b',
                r'\bdefine\b',
                r'\blist\b'
            ]
            
            for line in cleaned_lines:
                if any(re.search(pattern, line, re.IGNORECASE) for pattern in question_indicators):
                    if len(line) > 20:
                        cleaned_questions.append(line)
        
        return cleaned_questions
    
    def process_uploaded_paper(self, file_path):
        """
        Extract questions from uploaded exam paper PDF
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            dict or list: If error, returns {"error": "message"}, otherwise list of questions
        """
        try:
            # Extract text from PDF with better layout preservation
            full_text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    # Use layout extraction for better quality
                    page_text = page.extract_text(layout=True)
                    if page_text:
                        full_text += page_text + "\n"
            
            # Check if PDF appears to be scanned or unreadable
            if len(full_text.strip()) < 200:
                return {
                    "error": "PDF appears to be scanned or unreadable. Please paste questions manually."
                }
            
            # Process the text to extract questions
            cleaned_questions = self.process_text_to_questions(full_text)
            
            return cleaned_questions
            
        except Exception:
            # Return error dict if processing fails
            return {
                "error": "Failed to process PDF. Please paste questions manually."
            }
    
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
    
    def generate_dynamic_topics_from_questions(self, questions, llm_client):
        """
        Dynamically identify exam units/themes from questions using LLM clustering
        
        Args:
            questions: List of question strings
            llm_client: Callable that takes prompt and returns LLM response text
        
        Returns:
            dict: Contains topic_counts and mapping
        """
        if not questions:
            return {"topic_counts": {}, "mapping": {}}
        
        # Build numbered question list
        questions_str = "\n".join([f"{i+1}. {q[:200]}" for i, q in enumerate(questions)])
        
        prompt = f"""Analyze these exam questions and identify 5-8 major exam units or themes.
Group related questions together under meaningful unit names.

Questions:
{questions_str}

Return ONLY a JSON object mapping unit names to question numbers:
{{
  "units": {{
    "Unit Name 1": [1, 3, 5],
    "Unit Name 2": [2, 4, 6],
    ...
  }}
}}

Requirements:
- Create 5-8 distinct units
- Use clear, descriptive unit names
- Assign each question to exactly one unit
- Cover all {len(questions)} questions"""
        
        try:
            # Call LLM
            llm_response = llm_client(prompt)
            
            # Parse JSON from response
            response_text = llm_response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(response_text)
            units = data.get("units", {})
            
            # Initialize topic counts
            topic_counts = {}
            question_mapping = {}
            
            # Process each unit
            for unit_name, question_numbers in units.items():
                count = len(question_numbers)
                topic_counts[unit_name] = count
                
                # Map question text to unit name
                for q_num in question_numbers:
                    try:
                        idx = int(q_num) - 1  # Convert to 0-based index
                        if 0 <= idx < len(questions):
                            question_text = questions[idx]
                            question_mapping[question_text] = unit_name
                    except (ValueError, IndexError):
                        continue
            
            return {
                "topic_counts": topic_counts,
                "mapping": question_mapping
            }
            
        except (json.JSONDecodeError, KeyError, AttributeError, ValueError):
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
