"""
CramClutch - Multi-Agent Exam Preparation System
Main Streamlit Application
"""
import streamlit as st
from datetime import datetime, date
from state_manager import StateManager
from agents.crisis_agent import CrisisAgent
from agents.exam_pattern_agent import ExamPatternAgent
from agents.prioritization_agent import PrioritizationAgent
from agents.sprint_agent import SprintAgent
from agents.retention_agent import RetentionAgent
from llm_client import generate_response


# Page configuration
st.set_page_config(
    page_title="CramClutch - Exam Prep Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Initialize session state
if 'state_manager' not in st.session_state:
    st.session_state.state_manager = StateManager()
    st.session_state.crisis_agent = CrisisAgent(st.session_state.state_manager)
    st.session_state.pattern_agent = ExamPatternAgent(st.session_state.state_manager)
    st.session_state.priority_agent = PrioritizationAgent(st.session_state.state_manager)
    st.session_state.sprint_agent = SprintAgent(st.session_state.state_manager)
    st.session_state.retention_agent = RetentionAgent(st.session_state.state_manager)
    
    # Initialize sprint cache
    st.session_state.state_manager.set('sprints.generated_sprints', {})


def render_sidebar():
    """Render sidebar with user inputs and configuration"""
    with st.sidebar:
        st.title("📚 CramClutch")
        st.markdown("---")
        
        # User configuration
        st.subheader("Configuration")
        name = st.text_input("Your Name", placeholder="Enter your name")
        university = st.selectbox("University", ["JNTU", "Osmania"])
        subject = st.text_input("Subject", placeholder="e.g., Data Structures")
        exam_date = st.date_input("Exam Date")
        syllabus_topics = st.text_input(
            "Syllabus Topics",
            placeholder="e.g., Arrays, Trees, Graphs, Sorting",
            help="Enter topics separated by commas"
        )
        
        if st.button("Start Planning", type="primary"):
            if name and subject and syllabus_topics:
                state_manager = st.session_state.state_manager
                
                # Store basic user data
                state_manager.set('user.name', name)
                state_manager.set('user.university', university)
                state_manager.set('exam.subject', subject)
                state_manager.set('user.exam_date', exam_date.isoformat())
                
                # Calculate time remaining hours
                today = date.today()
                time_delta = exam_date - today
                time_remaining_hours = time_delta.total_seconds() / 3600
                state_manager.set('user.time_remaining_hours', time_remaining_hours)
                
                # Initialize syllabus topics
                topics = [topic.strip() for topic in syllabus_topics.split(',') if topic.strip()]
                state_manager.set('intelligence.topics', topics)
                
                # Initialize confidence scores (default 0.5 for each topic)
                confidence_scores = {topic: 0.5 for topic in topics}
                state_manager.set('intelligence.confidence_scores', confidence_scores)
                
                # Run crisis analysis
                crisis_agent = st.session_state.crisis_agent
                crisis_result = crisis_agent.analyze_crisis()
                
                # Display results
                st.success("✅ Configuration saved!")
                st.markdown("---")
                st.subheader("📊 Crisis Analysis")
                st.metric("PSI Score", f"{crisis_result['psi']:.2f}")
                st.metric("Crisis Level", crisis_result['crisis_level'].upper())
                st.info(f"💡 {crisis_result['recommendation']}")
            else:
                st.warning("⚠️ Please fill in all required fields")
        
        st.markdown("---")
        
        # Agent status indicators
        st.subheader("Agent Status")
        st.info("🚨 Crisis Agent: Ready")
        st.info("📊 Pattern Agent: Ready")
        st.info("🎯 Priority Agent: Ready")
        st.info("⚡ Sprint Agent: Ready")
        st.info("🧠 Retention Agent: Ready")


def render_main_content():
    """Render main content area"""
    st.title("Multi-Agent Exam Preparation System")
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard",
        "🎯 Prioritization",
        "⚡ Sprint Planning",
        "🧠 Retention",
        "🚨 Crisis Mode"
    ])
    
    with tab1:
        st.header("Dashboard")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Syllabus Coverage", "0%")
        with col2:
            st.metric("Study Hours", "0h")
        with col3:
            st.metric("Topics Completed", "0")
        
        st.info("Configure your exam details in the sidebar to get started!")
        
        # Test Gemini LLM connection
        st.markdown("---")
        st.subheader("🧪 Test LLM Connection")
        if st.button("Test Gemini", type="secondary"):
            try:
                with st.spinner("Connecting to Gemini..."):
                    response = generate_response("Say hello in one sentence.")
                st.success("✅ Gemini API connected successfully!")
                st.write(response)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    with tab2:
        st.header("Topic Prioritization")
        st.write("Load historical exam patterns and analyze topic probabilities")
        
        if st.button("Load University Pattern", type="primary"):
            state_manager = st.session_state.state_manager
            university = state_manager.get('user.university')
            
            if university:
                try:
                    pattern_agent = st.session_state.pattern_agent
                    
                    # Load university data and compute probabilities
                    pattern_agent.load_university_data(university)
                    pattern_agent.compute_historical_probabilities()
                    
                    # Retrieve probability map from state
                    exam_probability_map = state_manager.get('intelligence.exam_probability_map')
                    
                    if exam_probability_map:
                        # Set topics from probability map
                        state_manager.set('intelligence.topics', list(exam_probability_map.keys()))
                        
                        # Reset confidence scores for all topics
                        confidence_scores = {topic: 0.5 for topic in exam_probability_map.keys()}
                        state_manager.set('intelligence.confidence_scores', confidence_scores)
                        
                        st.success(f"✅ Loaded {university} exam patterns!")
                        st.info("📌 Topics aligned with university exam pattern.")
                        st.markdown("---")
                        st.subheader("📊 Topic Probability Analysis")
                        
                        # Create table data
                        table_data = []
                        for topic, probability in exam_probability_map.items():
                            table_data.append({
                                "Topic": topic,
                                "Probability %": f"{probability * 100:.1f}%"
                            })
                        
                        # Display as table
                        st.table(table_data)
                    else:
                        st.warning("⚠️ No probability data available")
                        
                except Exception as e:
                    st.error(f"❌ Error loading pattern data: {str(e)}")
            else:
                st.warning("⚠️ Please configure university in sidebar first")
        
        st.markdown("---")
        
        if st.button("Generate Priority Ranking"):
            state_manager = st.session_state.state_manager
            exam_probability_map = state_manager.get('intelligence.exam_probability_map')
            
            if exam_probability_map:
                try:
                    priority_agent = st.session_state.priority_agent
                    
                    # Generate priority ranking
                    priority_agent.generate_priority_ranking()
                    
                    # Retrieve ranked topics and scores
                    ranked_topics = state_manager.get('priorities.ranked_topics')
                    priority_scores = state_manager.get('intelligence.priority_scores')
                    
                    if ranked_topics and priority_scores:
                        st.success("✅ Priority ranking generated!")
                        st.markdown("---")
                        st.subheader("🎯 Priority Ranking")
                        
                        # Display ranked topics
                        for rank, topic in enumerate(ranked_topics, 1):
                            score = priority_scores.get(topic, 0.0)
                            display_text = f"**Rank {rank}** | {topic} | Priority Score: {score:.2f}"
                            
                            # Highlight top 3 with success, others with info
                            if rank <= 3:
                                st.success(display_text)
                            else:
                                st.info(display_text)
                    else:
                        st.warning("⚠️ No ranking data available")
                        
                except Exception as e:
                    st.error(f"❌ Error generating priorities: {str(e)}")
            else:
                st.warning("⚠️ Please load university pattern first")
    
    with tab3:
        st.header("Sprint Planning")
        st.write("Generate focused study sprints with AI-generated content")
        
        state_manager = st.session_state.state_manager
        ranked_topics = state_manager.get('priorities.ranked_topics')
        
        if ranked_topics:
            # Topic selection dropdown
            selected_topic = st.selectbox(
                "Select Topic for Sprint",
                options=ranked_topics,
                help="Topics are ordered by priority. Top priority topics appear first."
            )
            
            if st.button("Start Sprint", type="primary"):
                sprint_cache = state_manager.get('sprints.generated_sprints') or {}
                
                # Check if sprint exists in cache
                if selected_topic in sprint_cache:
                    st.info("♻️ Using cached sprint (no API call made)")
                    sprint_content = sprint_cache[selected_topic]
                else:
                    # Generate new sprint with API call
                    try:
                        with st.spinner(f"Generating sprint for {selected_topic}..."):
                            sprint_agent = st.session_state.sprint_agent
                            sprint_content = sprint_agent.generate_sprint(selected_topic, generate_response)
                        
                        # Cache the result
                        sprint_cache[selected_topic] = sprint_content
                        state_manager.set('sprints.generated_sprints', sprint_cache)
                        
                        st.success("✅ Sprint generated successfully!")
                    
                    except Exception as e:
                        # Fallback: check if cached version exists
                        if selected_topic in sprint_cache:
                            st.warning("⚠️ API error. Using cached version.")
                            sprint_content = sprint_cache[selected_topic]
                        else:
                            st.error("❌ Sprint generation temporarily unavailable. Please retry.")
                            st.error(f"Error: {str(e)}")
                            sprint_content = None
                
                # Display sprint content
                if sprint_content:
                    st.markdown("---")
                    st.subheader(f"⚡ Sprint: {selected_topic}")
                    
                    # Section 1: Summary
                    st.markdown("### 📝 Summary")
                    st.write(sprint_content.get('summary', 'No summary available'))
                    
                    st.markdown("---")
                    
                    # Section 2: Active Recall Questions
                    st.markdown("### 🧠 Active Recall Questions")
                    active_recall = sprint_content.get('active_recall_questions', [])
                    if active_recall:
                        for i, question in enumerate(active_recall, 1):
                            st.write(f"{i}. {question}")
                    else:
                        st.write("No active recall questions available")
                    
                    st.markdown("---")
                    
                    # Section 3: Application Question
                    st.markdown("### 📊 Application Question")
                    app_question = sprint_content.get('application_question', 'No application question available')
                    st.write(app_question)
                    
                    st.markdown("---")
                    
                    # Section 4: MCQs
                    st.markdown("### ✅ Multiple Choice Questions")
                    mcqs = sprint_content.get('mcqs', [])
                    if mcqs:
                        for i, mcq in enumerate(mcqs, 1):
                            st.markdown(f"**Question {i}:** {mcq.get('question', 'N/A')}")
                            options = mcq.get('options', [])
                            for idx, option in enumerate(options):
                                st.write(f"  {chr(65 + idx)}. {option}")
                            st.markdown(f"<small style='color: gray;'>Correct Answer: {mcq.get('answer', 'N/A')}</small>", unsafe_allow_html=True)
                            st.write("")
                    else:
                        st.write("No MCQs available")
        else:
            st.warning("⚠️ Generate priority ranking first.")
    
    with tab4:
        st.header("Retention Optimization")
        st.write("Optimize memory retention with spaced repetition")
        st.button("Generate Revision Schedule")
    
    with tab5:
        st.header("Crisis Mode")
        st.write("Emergency planning for last-minute preparation")
        st.button("Activate Crisis Mode")


def main():
    """Main application entry point"""
    render_sidebar()
    render_main_content()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "CramClutch v0.1 | Multi-Agent Exam Preparation System"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
