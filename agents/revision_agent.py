"""
Revision Agent - Generates concise revision notes for high-priority topics
"""
import json
import re


class RevisionAgent:
    """Agent for generating ultra-concise revision notes"""
    
    def __init__(self, state_manager):
        self.state_manager = state_manager
    
    def generate_revision_notes(self, llm_client):
        """
        Generate ultra-concise revision notes for top priority topics
        
        Args:
            llm_client: LLM client function for generating content
        
        Returns:
            dict: Revision notes by topic or cached result
        """
        # Retrieve exam probability map and ranked topics
        exam_probability_map = self.state_manager.get('intelligence.exam_probability_map') or {}
        ranked_topics = self.state_manager.get('priorities.ranked_topics') or []
        
        # Fallback: if ranked_topics not available, use topics from intelligence
        if not ranked_topics:
            ranked_topics = list(exam_probability_map.keys()) if exam_probability_map else []
            # Sort by probability
            if exam_probability_map:
                ranked_topics = sorted(
                    ranked_topics,
                    key=lambda t: exam_probability_map.get(t, 0),
                    reverse=True
                )
        
        if not ranked_topics:
            return {
                'status': 'error',
                'message': 'No topics available. Please configure topics first.'
            }
        
        # Select top 3-5 topics (minimum 3, maximum 5)
        num_topics = min(5, max(3, len(ranked_topics)))
        selected_topics = ranked_topics[:num_topics]
        
        # Calculate topics hash for cache validation
        topics_hash = hash(tuple(sorted(selected_topics)))
        
        # Check cache with hash validation
        cached_notes = self.state_manager.get('revision_notes')
        cached_meta = self.state_manager.get('revision_cache_meta')
        
        if cached_notes and cached_meta:
            cached_hash = cached_meta.get('topics_hash')
            if cached_hash == topics_hash:
                return {
                    'status': 'cached',
                    'notes': cached_notes
                }
        
        # Build efficient prompt for all topics in one call
        topics_list = "\n".join([f"- {topic}" for topic in selected_topics])
        
        prompt = f"""Generate ultra concise revision notes for the following topics.

Topics:
{topics_list}

Rules:
- Bullet points only
- No paragraphs or explanations
- Maximum 6 bullets per topic
- Focus on concepts frequently asked in exams
- Each bullet must be one line maximum
- Prioritize high-yield points only

Format your response as valid JSON:
{{
  "Topic Name 1": ["point1", "point2", "point3"],
  "Topic Name 2": ["point1", "point2"],
  ...
}}

Return ONLY the JSON object, no additional text."""

        try:
            # Single API call for all topics
            response = llm_client(prompt)
            
            # Parse JSON response
            revision_notes = self._parse_response(response, selected_topics)
            
            if revision_notes:
                # Store in state with cache metadata
                self.state_manager.set('revision_notes', revision_notes)
                self.state_manager.set('revision_cache_meta', {
                    'topics_hash': topics_hash
                })
                
                return {
                    'status': 'success',
                    'notes': revision_notes
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Failed to parse revision notes from LLM response'
                }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error generating revision notes: {str(e)}'
            }
    
    def _parse_response(self, response, expected_topics):
        """
        Safely parse LLM response to extract revision notes
        
        Args:
            response: Raw LLM response
            expected_topics: List of topics we requested
        
        Returns:
            dict: Parsed revision notes or None if parsing fails
        """
        try:
            # Try direct JSON parsing first
            revision_notes = json.loads(response)
            
            # Validate structure
            if isinstance(revision_notes, dict):
                # Ensure all values are lists
                for topic, points in revision_notes.items():
                    if not isinstance(points, list):
                        # Try to convert string to list
                        if isinstance(points, str):
                            revision_notes[topic] = [points]
                        else:
                            revision_notes[topic] = []
                
                return revision_notes
        
        except json.JSONDecodeError:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    revision_notes = json.loads(json_match.group(0))
                    
                    # Validate structure
                    if isinstance(revision_notes, dict):
                        for topic, points in revision_notes.items():
                            if not isinstance(points, list):
                                if isinstance(points, str):
                                    revision_notes[topic] = [points]
                                else:
                                    revision_notes[topic] = []
                        
                        return revision_notes
                
                except json.JSONDecodeError:
                    pass
            
            # Fallback: try to parse manually
            return self._manual_parse(response, expected_topics)
        
        except Exception:
            return None
    
    def _manual_parse(self, response, expected_topics):
        """
        Manually parse response if JSON parsing fails
        
        Args:
            response: Raw LLM response
            expected_topics: List of topics we requested
        
        Returns:
            dict: Manually parsed notes or None
        """
        try:
            notes = {}
            current_topic = None
            
            lines = response.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if line is a topic (matches one of expected topics)
                is_topic = False
                for topic in expected_topics:
                    if topic.lower() in line.lower() and ':' in line:
                        current_topic = topic
                        notes[topic] = []
                        is_topic = True
                        break
                
                # If not a topic and we have a current topic, it's a bullet point
                if not is_topic and current_topic:
                    # Remove bullet markers
                    clean_line = re.sub(r'^[-*•]\s*', '', line)
                    if clean_line:
                        notes[current_topic].append(clean_line)
            
            return notes if notes else None
        
        except Exception:
            return None
    
    def clear_cache(self):
        """Clear cached revision notes to force regeneration"""
        self.state_manager.set('revision_notes', None)
        return {'status': 'success', 'message': 'Revision notes cache cleared'}
