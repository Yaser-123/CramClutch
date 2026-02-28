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
                        st.success(f"✅ Loaded {university} exam patterns!")
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
    
    with tab3:
        st.header("Sprint Planning")
        st.write("Create focused study sprints")
        st.button("Create New Sprint")
    
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
