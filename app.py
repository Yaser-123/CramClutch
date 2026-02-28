"""
CramClutch - Multi-Agent Exam Preparation System
Main Streamlit Application
"""
import streamlit as st
from datetime import datetime, date
import re
import pdfplumber
import tempfile
import os
from state_manager import StateManager
from agents.crisis_agent import CrisisAgent
from agents.exam_pattern_agent import ExamPatternAgent
from agents.prioritization_agent import PrioritizationAgent
from agents.sprint_agent import SprintAgent
from agents.retention_agent import RetentionAgent
from agents.revision_agent import RevisionAgent
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
    st.session_state.revision_agent = RevisionAgent(st.session_state.state_manager)

# Ensure revision_agent exists (backward compatibility)
if 'revision_agent' not in st.session_state:
    st.session_state.revision_agent = RevisionAgent(st.session_state.state_manager)


def generate_revision_pdf(revision_notes):
    """
    Generate a PDF file from revision notes
    
    Args:
        revision_notes: Dictionary of topics and bullet points
    
    Returns:
        str: Path to generated PDF file
    """
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf_path = temp_file.name
        temp_file.close()
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#2C3E50',
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        topic_style = ParagraphStyle(
            'TopicHeader',
            parent=styles['Heading2'],
            fontSize=16,
            textColor='#34495E',
            spaceAfter=12,
            spaceBefore=20
        )
        
        bullet_style = ParagraphStyle(
            'BulletPoint',
            parent=styles['Normal'],
            fontSize=11,
            leftIndent=20,
            spaceAfter=8
        )
        
        # Add title
        title = Paragraph("Quick Revision Notes", title_style)
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))
        
        # Add timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        timestamp_para = Paragraph(f"<i>Generated on {timestamp}</i>", styles['Normal'])
        story.append(timestamp_para)
        story.append(Spacer(1, 0.3 * inch))
        
        # Add revision notes
        for topic, points in revision_notes.items():
            # Add topic header
            topic_para = Paragraph(topic, topic_style)
            story.append(topic_para)
            
            # Add bullet points
            for point in points:
                # Escape special characters
                clean_point = point.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                bullet_para = Paragraph(f"• {clean_point}", bullet_style)
                story.append(bullet_para)
            
            story.append(Spacer(1, 0.2 * inch))
        
        # Build PDF
        doc.build(story)
        
        return pdf_path
    
    except ImportError:
        # Fallback to simple text-based PDF if reportlab not available
        raise Exception("reportlab library not installed. Please install it: pip install reportlab")


def render_sidebar():
    """Render sidebar with user inputs and configuration"""
    with st.sidebar:
        st.title("📚 CramClutch")
        
        # Show persistence indicator
        state_manager = st.session_state.state_manager
        if state_manager.get('user.name'):
            st.success("✅ Loaded saved session")
        
        st.markdown("---")
        
        # Get saved state
        saved_name = state_manager.get('user.name') or ""
        saved_university = state_manager.get('user.university') or "JNTU"
        saved_subject = state_manager.get('exam.subject') or ""
        saved_exam_date_str = state_manager.get('user.exam_date')
        saved_exam_datetime_str = state_manager.get('user.exam_datetime')
        saved_topics_list = state_manager.get('intelligence.topics') or []
        saved_topics = ", ".join(saved_topics_list) if saved_topics_list else ""
        
        # Parse saved exam date and time
        if saved_exam_date_str:
            try:
                saved_exam_date = datetime.fromisoformat(saved_exam_date_str).date()
            except:
                saved_exam_date = date.today()
        else:
            saved_exam_date = date.today()
        
        # Parse saved exam time
        from datetime import time as time_type
        if saved_exam_datetime_str:
            try:
                saved_exam_datetime = datetime.fromisoformat(saved_exam_datetime_str)
                saved_exam_time = saved_exam_datetime.time()
            except:
                saved_exam_time = time_type(9, 0)  # Default 9:00 AM
        else:
            saved_exam_time = time_type(9, 0)  # Default 9:00 AM
        
        # User configuration
        st.subheader("Configuration")
        name = st.text_input("Your Name", value=saved_name, placeholder="Enter your name")
        university_options = ["JNTU", "Osmania", "Custom"]
        
        # Determine if saved university is custom
        if saved_university in ["JNTU", "Osmania"]:
            university_index = university_options.index(saved_university)
            saved_custom_university = ""
        else:
            # Saved university is custom
            university_index = 2  # "Custom"
            saved_custom_university = saved_university
        
        university = st.selectbox("University", university_options, index=university_index)
        
        # Show custom university input if "Custom" is selected
        custom_university = ""
        if university == "Custom":
            custom_university = st.text_input(
                "Enter University Name",
                value=saved_custom_university,
                placeholder="e.g., Anna University"
            )
        
        subject = st.text_input("Subject", value=saved_subject, placeholder="e.g., Data Structures")
        exam_date = st.date_input("Exam Date", value=saved_exam_date)
        exam_time = st.time_input("Exam Start Time", value=saved_exam_time)
        syllabus_topics = st.text_input(
            "Syllabus Topics (Optional)",
            value=saved_topics,
            placeholder="e.g., Arrays, Trees, Graphs, Sorting",
            help="Optional. Leave empty if you plan to upload previous year papers for automatic topic detection."
        )
        
        if st.button("Start Planning", type="primary"):
            if name and subject:
                state_manager = st.session_state.state_manager
                
                # Determine which university name to save
                if university == "Custom":
                    if custom_university:
                        final_university = custom_university
                    else:
                        st.error("⚠️ Please enter a custom university name")
                        st.stop()
                else:
                    final_university = university
                
                # Store basic user data
                state_manager.set('user.name', name)
                state_manager.set('user.university', final_university)
                state_manager.set('exam.subject', subject)
                state_manager.set('user.exam_date', exam_date.isoformat())
                
                # Combine date and time for accurate calculation
                exam_datetime = datetime.combine(exam_date, exam_time)
                state_manager.set('user.exam_datetime', exam_datetime.isoformat())
                
                # Calculate time remaining hours
                time_remaining_hours = (exam_datetime - datetime.now()).total_seconds() / 3600
                
                # Handle negative time (exam already started/passed)
                if time_remaining_hours < 0:
                    time_remaining_hours = 0
                
                state_manager.set('user.time_remaining_hours', time_remaining_hours)
                
                # Initialize syllabus topics only if provided
                if syllabus_topics.strip():
                    topics = [topic.strip() for topic in syllabus_topics.split(',') if topic.strip()]
                    state_manager.set('intelligence.topics', topics)
                    
                    # Initialize confidence scores (default 0.5 for each topic)
                    confidence_scores = {topic: 0.5 for topic in topics}
                    state_manager.set('intelligence.confidence_scores', confidence_scores)
                else:
                    # Leave topics empty - will be populated from uploaded papers
                    state_manager.set('intelligence.topics', [])
                    state_manager.set('intelligence.confidence_scores', {})
                
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
                st.warning("⚠️ Please fill in your name and subject")
        
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
        
        # Retrieve progress metrics from state
        state_manager = st.session_state.state_manager
        syllabus_coverage = state_manager.get('progress.syllabus_coverage') or 0.0
        total_study_time = state_manager.get('progress.total_study_time') or 0
        completed_topics = state_manager.get('progress.completed_topics') or []
        
        col1, col2, col3 = st.columns(3)
        with col1:
            coverage_percent = syllabus_coverage * 100
            st.metric("Syllabus Coverage", f"{coverage_percent:.1f}%")
        with col2:
            st.metric("Study Hours", f"{total_study_time:.1f}h")
        with col3:
            st.metric("Topics Completed", f"{len(completed_topics)}")
        
        # Show completed topics list if any
        if completed_topics:
            st.success("✅ Topics mastered (60%+ confidence):")
            for topic in completed_topics:
                st.write(f"- {topic}")
        else:
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
        
        # Custom Pattern from Uploaded Papers
        st.subheader("📂 Build Custom Pattern from Uploaded Papers")
        st.write("Upload previous year papers (PDFs) to build a custom exam pattern")
        
        # Topic generation mode selection
        use_dynamic_topics = st.checkbox(
            "🔍 Auto-discover topics from papers",
            value=False,
            help="Uses LLM to identify 5-8 major themes from uploaded papers. Heavier API usage."
        )
        
        uploaded_files = st.file_uploader(
            "Upload Previous Year Papers (PDF)",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload one or more PDF files of previous exam papers"
        )
        
        # Manual paste option for scanned PDFs
        pasted_questions = st.text_area(
            "📝 Paste Questions (if PDF not readable)",
            height=200,
            placeholder="Paste questions here if PDF appears scanned or unreadable...\n\n1. First question text\n2. Second question text\n...",
            help="Use this if your PDFs are scanned images or not extracting properly"
        )
        
        if st.button("Analyze Uploaded Papers"):
            if uploaded_files or pasted_questions.strip():
                state_manager = st.session_state.state_manager
                
                # Initialize cache tracking
                if 'processed_files' not in st.session_state:
                    st.session_state.processed_files = {}
                if 'dynamic_topics_cache' not in st.session_state:
                    st.session_state.dynamic_topics_cache = {}
                
                # Create cache key based on file names and mode
                file_names_tuple = tuple(sorted([f.name for f in uploaded_files]))
                cache_key = (file_names_tuple, use_dynamic_topics)
                
                # Check if this exact configuration was already processed
                if cache_key in st.session_state.processed_files:
                    st.info("♻️ These files with this configuration were already analyzed. Using cached results.")
                else:
                    # Check prerequisites for non-dynamic mode
                    if not use_dynamic_topics:
                        syllabus_topics = state_manager.get('intelligence.topics')
                        if not syllabus_topics:
                            st.warning("⚠️ Please configure syllabus topics in sidebar first, or enable auto-discovery mode")
                            st.stop()
                    
                    try:
                        pattern_agent = st.session_state.pattern_agent
                        merged_topic_counts = {}
                        total_questions = 0
                        all_questions = []
                        has_scanned_pdf = False
                        
                        # Check if user pasted questions manually
                        if pasted_questions.strip():
                            st.info("📝 Using manually pasted questions")
                            all_questions = pattern_agent.process_text_to_questions(pasted_questions)
                        
                        # Process uploaded PDFs if no pasted text
                        elif uploaded_files:
                            with st.spinner("Extracting questions from PDFs..."):
                                for uploaded_file in uploaded_files:
                                    # Save file temporarily
                                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                                        tmp_file.write(uploaded_file.getvalue())
                                        tmp_file_path = tmp_file.name
                                    
                                    try:
                                        # Extract questions from PDF
                                        result = pattern_agent.process_uploaded_paper(tmp_file_path)
                                        
                                        # Check if error was returned
                                        if isinstance(result, dict) and "error" in result:
                                            st.warning(f"⚠️ {result['error']}")
                                            has_scanned_pdf = True
                                        elif result:
                                            all_questions.extend(result)
                                    
                                    finally:
                                        # Clean up temp file
                                        if os.path.exists(tmp_file_path):
                                            os.unlink(tmp_file_path)
                        
                        if not all_questions:
                            st.warning("⚠️ No questions found in uploaded papers")
                            if has_scanned_pdf:
                                st.error("📋 Your PDF appears to be scanned. Please paste the questions in the text area above.")
                            else:
                                st.info("💡 Tips for better extraction:")
                                st.write("- Ensure PDF has selectable text (not scanned images)")
                                st.write("- Questions should be numbered (1. 2. 3.) or contain keywords like 'explain', 'describe', etc.")
                                st.write("- Try pasting questions manually in the text area above")
                        else:
                            st.success(f"📄 Successfully extracted {len(all_questions)} questions!")
                            
                            # Show extracted questions in expander for debugging
                            with st.expander("🔍 View Extracted Questions"):
                                for i, q in enumerate(all_questions[:15], 1):  # Show first 15
                                    st.markdown(f"**{i}.** {q[:300]}")
                                if len(all_questions) > 15:
                                    st.info(f"... and {len(all_questions) - 15} more questions")
                            
                            # Choose classification method based on mode
                            if use_dynamic_topics:
                                # Dynamic topic generation with caching
                                with st.spinner("Discovering topics from questions (this may take a moment)..."):
                                    # Check if we have cached dynamic topics for these files
                                    if file_names_tuple in st.session_state.dynamic_topics_cache:
                                        st.info("♻️ Using cached topic discovery results")
                                        classification_result = st.session_state.dynamic_topics_cache[file_names_tuple]
                                    else:
                                        classification_result = pattern_agent.generate_dynamic_topics_from_questions(
                                            all_questions,
                                            generate_response
                                        )
                                        # Cache the result
                                        st.session_state.dynamic_topics_cache[file_names_tuple] = classification_result
                                
                                merged_topic_counts = classification_result.get('topic_counts', {})
                                total_questions = sum(merged_topic_counts.values())
                                
                                # Debug info
                                if not merged_topic_counts:
                                    st.error("⚠️ LLM failed to discover topics. Check API key or try again.")
                                    with st.expander("🔍 Debug: Classification Result"):
                                        st.json(classification_result)
                            else:
                                # Use existing syllabus topics
                                with st.spinner("Classifying questions to syllabus topics..."):
                                    syllabus_topics = state_manager.get('intelligence.topics') or []
                                    
                                    # Check if topics are available
                                    if not syllabus_topics:
                                        st.error("⚠️ No syllabus topics found. Please either:")
                                        st.write("1. Enter syllabus topics in the sidebar, OR")
                                        st.write("2. Enable 'Automatically discover topics' option above")
                                        st.stop()
                                    
                                    classification_result = pattern_agent.classify_questions_with_llm(
                                        all_questions,
                                        syllabus_topics,
                                        generate_response
                                    )
                                    
                                    merged_topic_counts = classification_result.get('topic_counts', {})
                                    total_questions = sum(merged_topic_counts.values())
                                    
                                    # Debug info
                                    if not merged_topic_counts:
                                        st.error("⚠️ LLM classification failed. Check API key or syllabus topics.")
                                        with st.expander("🔍 Debug: Classification Result"):
                                            st.json(classification_result)
                            
                            if total_questions > 0:
                                # Convert counts to marks distribution
                                topic_marks = {}
                                for topic, count in merged_topic_counts.items():
                                    marks = (count / total_questions) * 100
                                    topic_marks[topic] = marks
                                
                                # Build custom pattern data
                                pattern_data = {
                                    "university": "Custom (Auto-discovered)" if use_dynamic_topics else "Custom",
                                    "topics": topic_marks,
                                    "total_marks": 100
                                }
                                
                                # Store in state
                                state_manager.set('exam.pattern_data', pattern_data)
                                
                                # If using dynamic topics, update syllabus topics in state
                                if use_dynamic_topics:
                                    discovered_topics = list(merged_topic_counts.keys())
                                    state_manager.set('intelligence.topics', discovered_topics)
                                    
                                    # Initialize confidence scores for discovered topics
                                    confidence_scores = {topic: 0.5 for topic in discovered_topics}
                                    state_manager.set('intelligence.confidence_scores', confidence_scores)
                                    
                                    st.info(f"🔍 Discovered {len(discovered_topics)} topics from uploaded papers")
                                
                                # Compute probabilities
                                pattern_agent.compute_historical_probabilities()
                                
                                # Mark this configuration as processed
                                st.session_state.processed_files[cache_key] = True
                                
                                # Success message based on source
                                if pasted_questions.strip():
                                    st.success(f"✅ Analyzed pasted questions - found {total_questions} questions!")
                                else:
                                    st.success(f"✅ Analyzed {len(uploaded_files)} paper(s) with {total_questions} questions!")
                                
                                st.markdown("---")
                                st.subheader("📊 Custom Topic Distribution")
                                
                                # Display topic distribution table
                                import pandas as pd
                                table_data = []
                                for topic, marks in topic_marks.items():
                                    table_data.append({
                                        "Topic": topic,
                                        "Marks": f"{marks:.1f}",
                                        "Questions": merged_topic_counts.get(topic, 0)
                                    })
                                
                                df = pd.DataFrame(table_data)
                                st.dataframe(df, use_container_width=True, hide_index=True)
                            else:
                                st.warning("⚠️ No questions could be classified")
                    
                    except Exception as e:
                        st.error(f"❌ Error analyzing papers: {str(e)}")
            else:
                st.warning("⚠️ Please upload at least one PDF file or paste questions in the text area")
        
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
        
        # Study Notes Upload Section
        st.markdown("---")
        st.subheader("📚 Upload Study Notes (Optional)")
        st.write("Upload your study notes to get contextual hints during sprints")
        
        uploaded_notes = st.file_uploader(
            "Upload Notes (PDF or TXT)",
            type=["pdf", "txt"],
            key="notes_uploader"
        )
        
        # Manual paste option for notes
        pasted_notes = st.text_area(
            "📝 Paste notes (if PDF not readable)",
            height=200,
            placeholder="Paste your study notes here...",
            key="pasted_notes"
        )
        
        if pasted_notes.strip() or uploaded_notes:
            # Check if notes are already indexed (caching)
            notes_index = state_manager.get('notes_index')
            notes_file_name = state_manager.get('notes_file_name')
            
            # Determine source identifier for caching
            if pasted_notes.strip():
                source_identifier = f"pasted_{hash(pasted_notes)}"
                source_display = "Pasted Notes"
            else:
                source_identifier = uploaded_notes.name
                source_display = uploaded_notes.name
            
            if notes_index and notes_file_name == source_identifier:
                st.success(f"✅ Notes already indexed ({source_display})")
                indexed_topics = list(notes_index.keys())
                st.info(f"📑 Indexed for {len(indexed_topics)} topics: {', '.join(indexed_topics[:5])}" + 
                       (f" and {len(indexed_topics) - 5} more" if len(indexed_topics) > 5 else ""))
            else:
                # Extract text from pasted content or uploaded file
                try:
                    text_content = ""
                    
                    # Use pasted notes if available
                    if pasted_notes.strip():
                        st.info("📝 Using pasted notes")
                        text_content = pasted_notes
                    else:
                        # Extract from uploaded file
                        with st.spinner("Extracting text from notes..."):
                            if uploaded_notes.type == "application/pdf":
                                # Extract from PDF
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                                    tmp_file.write(uploaded_notes.getvalue())
                                    tmp_file_path = tmp_file.name
                                
                                try:
                                    with pdfplumber.open(tmp_file_path) as pdf:
                                        for page in pdf.pages:
                                            text_content += page.extract_text(layout=True) or ""
                                finally:
                                    if os.path.exists(tmp_file_path):
                                        os.unlink(tmp_file_path)
                            else:
                                # Extract from TXT
                                text_content = uploaded_notes.getvalue().decode('utf-8')
                        
                        if not text_content.strip():
                            st.error("⚠️ No text found in the uploaded file")
                        else:
                            st.success(f"✅ Extracted {len(text_content)} characters")
                            
                            # Split text into 600-800 word chunks
                            with st.spinner("Chunking text..."):
                                words = text_content.split()
                                chunks = []
                                current_chunk = []
                                current_word_count = 0
                                
                                for word in words:
                                    current_chunk.append(word)
                                    current_word_count += 1
                                    
                                    # Create chunk when reaching 600-800 words
                                    if current_word_count >= 600:
                                        if current_word_count >= 800:
                                            chunks.append(' '.join(current_chunk))
                                            current_chunk = []
                                            current_word_count = 0
                                        # Look for sentence boundary around 700 words
                                        elif current_word_count >= 700 and word.endswith(('.', '!', '?')):
                                            chunks.append(' '.join(current_chunk))
                                            current_chunk = []
                                            current_word_count = 0
                                
                                # Add remaining words as final chunk
                                if current_chunk:
                                    chunks.append(' '.join(current_chunk))
                                
                                # Store chunks in state
                                state_manager.set('notes_chunks', chunks)
                                state_manager.set('notes_file_name', source_identifier)
                                
                                st.success(f"✅ Created {len(chunks)} chunks from your notes")
                                
                                # Show chunk preview
                                with st.expander("🔍 Preview Chunks"):
                                    for i, chunk in enumerate(chunks[:3], 1):
                                        st.markdown(f"**Chunk {i}** ({len(chunk.split())} words)")
                                        st.text(chunk[:200] + "...")
                                    if len(chunks) > 3:
                                        st.info(f"... and {len(chunks) - 3} more chunks")
                
                except Exception as e:
                    st.error(f"❌ Error processing notes: {str(e)}")
            
            # Index Notes by Topic button
            notes_chunks = state_manager.get('notes_chunks')
            ranked_topics = state_manager.get('priorities.ranked_topics') or state_manager.get('intelligence.topics')
            
            if notes_chunks and ranked_topics and not (notes_index and notes_file_name == source_identifier):
                if st.button("🔍 Index Notes by Topic", type="primary"):
                    try:
                        with st.spinner(f"Indexing {len(notes_chunks)} chunks across {len(ranked_topics)} topics..."):
                            notes_index_result = {}
                            
                            # Progress tracking
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for idx, chunk in enumerate(notes_chunks):
                                # Update progress
                                progress = (idx + 1) / len(notes_chunks)
                                progress_bar.progress(progress)
                                status_text.text(f"Processing chunk {idx + 1} of {len(notes_chunks)}...")
                                
                                # Call LLM to classify chunk
                                prompt = f"""Given these topics: {', '.join(ranked_topics)}

Which topic does this text belong to? Return ONLY the topic name, nothing else.

Text:
{chunk[:1000]}"""  # Limit to first 1000 chars for efficiency
                                
                                try:
                                    topic_name = generate_response(prompt).strip()
                                    
                                    # Validate that returned topic is in our list
                                    if topic_name in ranked_topics:
                                        if topic_name not in notes_index_result:
                                            notes_index_result[topic_name] = []
                                        notes_index_result[topic_name].append(chunk)
                                    else:
                                        # Try fuzzy matching
                                        for topic in ranked_topics:
                                            if topic.lower() in topic_name.lower() or topic_name.lower() in topic.lower():
                                                if topic not in notes_index_result:
                                                    notes_index_result[topic] = []
                                                notes_index_result[topic].append(chunk)
                                                break
                                
                                except Exception as e:
                                    st.warning(f"⚠️ Failed to classify chunk {idx + 1}: {str(e)}")
                                    continue
                            
                            # Clear progress indicators
                            progress_bar.empty()
                            status_text.empty()
                            
                            # Store index in state
                            state_manager.set('notes_index', notes_index_result)
                            
                            st.success(f"✅ Indexed notes for {len(notes_index_result)} topics!")
                            
                            # Show indexing summary
                            st.markdown("### 📊 Indexing Summary")
                            for topic, topic_chunks in notes_index_result.items():
                                st.write(f"- **{topic}**: {len(topic_chunks)} chunk(s)")
                    
                    except Exception as e:
                        st.error(f"❌ Error indexing notes: {str(e)}")
        
        st.markdown("---")
        
        ranked_topics = state_manager.get('priorities.ranked_topics')
        
        if ranked_topics:
            # Cache management section
            sprint_cache = state_manager.get('sprints.generated_sprints') or {}
            cached_count = len(sprint_cache)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if cached_count > 0:
                    st.info(f"💾 {cached_count} sprint(s) cached")
            with col2:
                if st.button("🗑️ Clear Cache", help="Clear all cached sprints to regenerate with latest settings", disabled=(cached_count == 0)):
                    # Clear sprint cache from state
                    state_manager.set('sprints.generated_sprints', {})
                    # Clear active sprint from session state
                    if hasattr(st.session_state, 'active_sprint_content'):
                        del st.session_state.active_sprint_content
                    if hasattr(st.session_state, 'active_sprint_topic'):
                        del st.session_state.active_sprint_topic
                    st.success("✅ Sprint cache cleared!")
                    st.rerun()
            
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
                
                # Store active sprint in session state for persistence
                if sprint_content:
                    st.session_state.active_sprint_content = sprint_content
                    st.session_state.active_sprint_topic = selected_topic
            
            # Display sprint content if it exists (outside button block for persistence)
            if hasattr(st.session_state, 'active_sprint_content') and st.session_state.active_sprint_content:
                sprint_content = st.session_state.active_sprint_content
                active_topic = st.session_state.active_sprint_topic
                
                st.markdown("---")
                
                # Sprint header with regenerate option
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.subheader(f"⚡ Sprint: {active_topic}")
                with col2:
                    if st.button("🔄 Regenerate", help="Clear cache and regenerate this sprint"):
                        sprint_cache = state_manager.get('sprints.generated_sprints') or {}
                        if active_topic in sprint_cache:
                            del sprint_cache[active_topic]
                            state_manager.set('sprints.generated_sprints', sprint_cache)
                        if hasattr(st.session_state, 'active_sprint_content'):
                            del st.session_state.active_sprint_content
                        if hasattr(st.session_state, 'active_sprint_topic'):
                            del st.session_state.active_sprint_topic
                        st.success(f"✅ Cache cleared for '{active_topic}'. Click 'Start Sprint' to regenerate.")
                        st.rerun()
                
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
                
                # Section 4: Interactive MCQs
                st.markdown("### ✅ Multiple Choice Questions")
                mcqs = sprint_content.get('mcqs', [])
                
                if mcqs:
                    # Check if answers have been submitted
                    submission_key = f"submitted_{active_topic}"
                    answers_submitted = st.session_state.get(submission_key, False)
                    
                    # Store user answers
                    user_answers = {}
                    
                    # Display each MCQ with radio buttons
                    for i, mcq in enumerate(mcqs, 1):
                        question_text = mcq.get('question', 'N/A')
                        options = mcq.get('options', [])
                        correct_answer = mcq.get('answer', '')
                        
                        st.markdown(f"**Question {i}:** {question_text}")
                        
                        # Create radio button for options
                        if options:
                            # Create option labels (A, B, C, D)
                            option_labels = [f"{chr(65 + idx)}. {opt}" for idx, opt in enumerate(options)]
                            
                            selected = st.radio(
                                f"Select your answer for Question {i}:",
                                option_labels,
                                key=f"{active_topic}_mcq_{i}",
                                label_visibility="collapsed",
                                disabled=answers_submitted
                            )
                            
                            # Extract the letter (A, B, C, D) from selection
                            if selected:
                                user_answers[i] = selected[0]  # Get first character (A, B, C, or D)
                            
                            # Show correct answer after submission
                            if answers_submitted:
                                user_choice = user_answers.get(i, '')
                                if user_choice == correct_answer:
                                    st.success(f"✅ Correct! Answer: {correct_answer}")
                                else:
                                    st.error(f"❌ Incorrect. Your answer: {user_choice} | Correct answer: {correct_answer}")
                        
                        st.write("")  # Spacing
                    
                    st.markdown("---")
                    
                    # Submit button
                    if not answers_submitted:
                        if st.button("📝 Submit Answers", type="primary"):
                            # Calculate score
                            correct_count = 0
                            total_questions = len(mcqs)
                            
                            for i, mcq in enumerate(mcqs, 1):
                                correct_answer = mcq.get('answer', '')
                                user_answer = user_answers.get(i, '')
                                
                                if user_answer == correct_answer:
                                    correct_count += 1
                            
                            # Calculate confidence score
                            confidence_score = correct_count / total_questions if total_questions > 0 else 0.0
                            
                            # Update retention agent
                            retention_agent = st.session_state.retention_agent
                            result = retention_agent.update_after_sprint(active_topic, confidence_score)
                            
                            # Update progress tracking
                            if confidence_score >= 0.6:
                                # Mark topic as completed
                                completed_topics = state_manager.get('progress.completed_topics') or []
                                if active_topic not in completed_topics:
                                    completed_topics.append(active_topic)
                                    state_manager.set('progress.completed_topics', completed_topics)
                            
                            # Recalculate syllabus coverage
                            total_topics_list = state_manager.get('intelligence.topics') or []
                            total_topics = len(total_topics_list)
                            completed_count = len(state_manager.get('progress.completed_topics') or [])
                            
                            if total_topics > 0:
                                coverage = completed_count / total_topics
                            else:
                                coverage = 0.0
                            
                            state_manager.set('progress.syllabus_coverage', coverage)
                            
                            # Increment study time (assume 0.5 hours per sprint)
                            current_study_time = state_manager.get('progress.total_study_time') or 0
                            state_manager.set('progress.total_study_time', current_study_time + 0.5)
                            
                            # Mark as submitted
                            st.session_state[submission_key] = True
                            
                            # Store results for display
                            st.session_state[f"score_{active_topic}"] = correct_count
                            st.session_state[f"total_{active_topic}"] = total_questions
                            st.session_state[f"confidence_{active_topic}"] = confidence_score
                            st.session_state[f"result_{active_topic}"] = result
                            
                            st.rerun()
                    
                    # Display results after submission
                    if answers_submitted:
                        st.markdown("### 📊 Results")
                        
                        score = st.session_state.get(f"score_{active_topic}", 0)
                        total = st.session_state.get(f"total_{active_topic}", 10)
                        confidence = st.session_state.get(f"confidence_{active_topic}", 0.0)
                        result = st.session_state.get(f"result_{active_topic}", {})
                        
                        # Display score
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Score", f"{score} / {total}")
                        with col2:
                            st.metric("Confidence", f"{confidence * 100:.1f}%")
                        
                        st.markdown("---")
                        
                        # Display preparedness score
                        preparedness_score = result.get('preparedness_score', 0.0)
                        weak_areas = result.get('weak_areas', [])
                        
                        st.markdown("### 📈 Preparedness Score")
                        prep_percentage = preparedness_score * 100
                        
                        if preparedness_score >= 0.7:
                            st.success(f"**{prep_percentage:.1f}%** - Great progress!")
                        elif preparedness_score >= 0.5:
                            st.info(f"**{prep_percentage:.1f}%** - Keep going!")
                        else:
                            st.warning(f"**{prep_percentage:.1f}%** - Focus on weak areas")
                        
                        # Display weak areas
                        st.markdown("### 🧠 Weak Areas")
                        if weak_areas:
                            for area in weak_areas:
                                st.write(f"- {area}")
                        else:
                            st.success("No weak areas detected.")
                        
                        # Reset button
                        if st.button("🔄 Retake Test"):
                            st.session_state[submission_key] = False
                            if f"score_{active_topic}" in st.session_state:
                                del st.session_state[f"score_{active_topic}"]
                            if f"total_{active_topic}" in st.session_state:
                                del st.session_state[f"total_{active_topic}"]
                            if f"confidence_{active_topic}" in st.session_state:
                                del st.session_state[f"confidence_{active_topic}"]
                            if f"result_{active_topic}" in st.session_state:
                                del st.session_state[f"result_{active_topic}"]
                            st.rerun()
                else:
                    st.write("No MCQs available")
        else:
            # Check if topics are empty
            topics = state_manager.get('intelligence.topics') or []
            if not topics:
                st.info("📝 To get started, you can:")
                st.write("1. Enter syllabus topics in the sidebar and click 'Start Planning', OR")
                st.write("2. Go to 'Topic Prioritization' tab and upload previous year papers with automatic topic detection")
            else:
                st.warning("⚠️ Generate priority ranking first in the 'Topic Prioritization' tab.")
    
    with tab4:
        st.header("Retention Optimization")
        st.write("Track confidence levels and optimize memory retention")
        
        state_manager = st.session_state.state_manager
        
        # Retrieve data from state
        preparedness_score = state_manager.get('intelligence.preparedness_score') or 0.0
        confidence_scores = state_manager.get('intelligence.confidence_scores') or {}
        weak_areas = state_manager.get('retention.weak_areas') or []
        
        # Section 1: Preparedness Score
        st.markdown("### 📈 Preparedness Score")
        prep_percentage = preparedness_score * 100
        
        if preparedness_score >= 0.7:
            st.success(f"### {prep_percentage:.1f}%")
            st.write("Excellent progress! You're well-prepared for the exam.")
        elif preparedness_score >= 0.5:
            st.info(f"### {prep_percentage:.1f}%")
            st.write("Good progress. Focus on weak areas to improve further.")
        else:
            st.warning(f"### {prep_percentage:.1f}%")
            st.write("Needs attention. Prioritize weak topics in your study plan.")
        
        st.markdown("---")
        
        # Section 2: Confidence Table
        st.markdown("### 📊 Confidence by Topic")
        
        if confidence_scores:
            import pandas as pd
            
            # Build table data
            table_data = []
            for topic, confidence in confidence_scores.items():
                # Determine status
                if confidence >= 0.7:
                    status = "Strong"
                elif confidence >= 0.5:
                    status = "Moderate"
                else:
                    status = "Weak"
                
                table_data.append({
                    "Topic": topic,
                    "Confidence": f"{confidence:.2f}",
                    "Status": status
                })
            
            # Create DataFrame and display
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No confidence data available yet. Complete sprints to track your progress.")
        
        st.markdown("---")
        
        # Section 3: Weak Areas
        st.markdown("### 🧠 Weak Areas")
        
        if weak_areas:
            st.write("Topics that need more attention:")
            for area in weak_areas:
                st.write(f"- {area}")
            
            # Find lowest confidence topic for recommendation
            if confidence_scores:
                lowest_topic = min(confidence_scores.items(), key=lambda x: x[1])
                st.markdown("---")
                st.info(f"💡 **Recommended next sprint:** {lowest_topic[0]} (Confidence: {lowest_topic[1]:.2f})")
        else:
            st.success("✅ All topics stable. No weak areas detected.")
        
        st.markdown("---")
        
        # Section 4: Quick Revision Notes
        st.markdown("### 📝 Quick Revision Notes")
        st.write("Generate ultra-concise revision notes for top priority topics")
        
        if st.button("📚 Generate Quick Revision Notes", type="primary"):
            with st.spinner("Generating revision notes..."):
                try:
                    revision_agent = st.session_state.revision_agent
                    result = revision_agent.generate_revision_notes(generate_response)
                    
                    if result['status'] == 'success':
                        st.success("✅ Revision notes generated successfully!")
                        st.rerun()
                    elif result['status'] == 'cached':
                        st.info("♻️ Using cached revision notes")
                        st.rerun()
                    else:
                        st.error(f"❌ {result.get('message', 'Failed to generate notes')}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        # Display revision notes if available
        revision_notes = state_manager.get('revision_notes')
        
        if revision_notes:
            st.markdown("---")
            st.markdown("### 📖 Your Revision Notes")
            
            # Display notes
            for topic, points in revision_notes.items():
                st.markdown(f"#### {topic}")
                for point in points:
                    st.write(f"• {point}")
                st.write("")  # Spacing
            
            # Download as PDF button
            st.markdown("---")
            
            try:
                # Generate PDF
                pdf_path = generate_revision_pdf(revision_notes)
                
                # Read PDF file
                with open(pdf_path, 'rb') as pdf_file:
                    pdf_bytes = pdf_file.read()
                
                # Clean up temporary file
                if os.path.exists(pdf_path):
                    os.unlink(pdf_path)
                
                # Show download button
                col1, col2 = st.columns([3, 1])
                with col2:
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_bytes,
                        file_name="revision_notes.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
            
            except Exception as e:
                st.error(f"❌ Error generating PDF: {str(e)}")
    
    with tab5:
        st.header("Crisis Mode")
        st.write("Emergency planning for last-minute preparation")
        
        state_manager = st.session_state.state_manager
        
        # Retrieve data from state
        psi = state_manager.get('intelligence.psi') or 0.0
        crisis_level = state_manager.get('crisis.level') or "normal"
        ranked_topics = state_manager.get('priorities.ranked_topics') or []
        
        # Section 1: Crisis Level Display
        if crisis_level == "critical":
            st.error("🚨 CRITICAL MODE ACTIVATED")
            st.write("Exam is imminent. Focus on highest-priority topics only.")
        elif crisis_level == "high":
            st.warning("⚠️ High Pressure Mode")
            st.write("Limited time remaining. Strategic focus required.")
        else:
            st.info("📌 Normal Preparation Mode")
            st.write("You have adequate time. Follow standard study plan.")
        
        st.markdown("---")
        
        # Section 2: Emergency Measures
        if ranked_topics:
            if crisis_level in ["high", "critical"]:
                st.markdown("### 🎯 Emergency Strategy")
                st.warning("**Focus only on top 3 topics.**")
                
                # Display top 3 topics
                top_3 = ranked_topics[:3]
                st.markdown("#### Priority Topics:")
                for i, topic in enumerate(top_3, 1):
                    st.write(f"{i}. **{topic}**")
                
                st.markdown("---")
                
                # Emergency recommendations
                st.markdown("### ⚡ Recommended Approach")
                st.write("- **30-minute sprint per topic**")
                st.write("- **Focus on active recall and MCQs**")
                st.write("- **Skip lowest ranked topics**")
                st.write("- **Review past exam patterns**")
                
                st.info("💡 Use Sprint Planning tab to start focused sprints on these topics.")
            else:
                st.success("✅ No emergency measures required.")
                st.write("Continue with your regular study plan and complete sprints for all topics.")
        else:
            # Check if topics are empty
            topics = state_manager.get('intelligence.topics') or []
            if not topics:
                st.info("📝 To get started, you can:")
                st.write("1. Enter syllabus topics in the sidebar and click 'Start Planning', OR")
                st.write("2. Go to 'Topic Prioritization' tab and upload previous year papers with automatic topic detection")
            else:
                st.warning("⚠️ Generate priority ranking first in the 'Topic Prioritization' tab to view crisis recommendations.")


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
