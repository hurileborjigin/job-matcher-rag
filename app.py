"""
Job Fair Navigator - Streamlit Application
Help users find the best-fitting jobs and get personalized approach strategies
"""
import streamlit as st
import sys
from pathlib import Path
from typing import List, Dict, Optional
import csv
from io import StringIO

from src.cv.cv_parser import get_cv_parser


# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.rag.retriever import JobRetriever
from src.rag.generator import JobResponseGenerator

# Page configuration
st.set_page_config(
    page_title="IT-CS Job Fair Navigator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .job-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .job-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .job-company {
        font-size: 1.1rem;
        color: #333;
        margin-bottom: 0.3rem;
    }
    .job-details {
        color: #666;
        font-size: 0.95rem;
    }
    .relevance-badge {
        background-color: #28a745;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
        display: inline-block;
        margin-top: 0.5rem;
    }
    .relevance-badge-low {
        background-color: #ffc107;
        color: #333;
    }
    .relevance-badge-very-low {
        background-color: #dc3545;
        color: white;
    }
    .strategy-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin-top: 1rem;
    }
    .stats-box {
        background-color: #e7f3ff;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 2rem;
    }
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 2rem;
    }
    </style>
""", unsafe_allow_html=True)


# Initialize session state
if 'retriever' not in st.session_state:
    st.session_state.retriever = None
if 'generator' not in st.session_state:
    st.session_state.generator = None
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'current_jobs' not in st.session_state:
    st.session_state.current_jobs = []
if 'user_cv' not in st.session_state:
    st.session_state.user_cv = ""


@st.cache_resource
def initialize_rag_system():
    """Initialize RAG components (cached for performance)."""
    try:
        retriever = JobRetriever()
        generator = JobResponseGenerator()
        return retriever, generator
    except Exception as e:
        st.error(f"❌ Error initializing RAG system: {str(e)}")
        st.info("💡 Please make sure you've run: `python scripts/build_vectorstore.py`")
        return None, None


def format_job_context(jobs: List[Dict]) -> str:
    """Format jobs into context string for the generator."""
    if not jobs:
        return "No jobs found."
    
    context_parts = []
    for i, job in enumerate(jobs[:5], 1):  # Top 5 jobs
        context = f"""Job {i}:
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Type: {job.get('job_type', 'N/A')}
Category: {job.get('category', 'N/A')}
Relevance: {job.get('relevance_score', 0):.1f}%
Description: {job.get('description', 'N/A')[:300]}...
Requirements: {job.get('requirements', 'N/A')[:300]}...
URL: {job['url']}
"""
        context_parts.append(context.strip())
    
    return "\n\n".join(context_parts)


def sort_jobs(jobs: List[Dict], sort_by: str = "relevance") -> List[Dict]:
    """Sort jobs by different criteria."""
    if sort_by == "relevance":
        return sorted(jobs, key=lambda x: x.get('relevance_score', 0), reverse=True)
    elif sort_by == "company":
        return sorted(jobs, key=lambda x: x.get('company', 'Unknown'))
    elif sort_by == "location":
        return sorted(jobs, key=lambda x: x.get('location', 'Unknown'))
    elif sort_by == "title":
        return sorted(jobs, key=lambda x: x.get('title', 'Unknown'))
    return jobs


def export_jobs_to_csv(jobs: List[Dict]) -> str:
    """Export jobs to CSV format."""
    output = StringIO()
    
    if not jobs:
        return ""
    
    # Define CSV columns
    fieldnames = ['title', 'company', 'location', 'job_type', 'category', 'relevance_score', 'url']
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for job in jobs:
        writer.writerow({
            'title': job.get('title', ''),
            'company': job.get('company', ''),
            'location': job.get('location', ''),
            'job_type': job.get('job_type', ''),
            'category': job.get('category', ''),
            'relevance_score': f"{job.get('relevance_score', 0):.1f}%",
            'url': job.get('url', '')
        })
    
    return output.getvalue()


def get_relevance_badge_class(score: float) -> str:
    """Get CSS class for relevance badge based on score."""
    if score >= 70:
        return "relevance-badge"
    elif score >= 50:
        return "relevance-badge relevance-badge-low"
    else:
        return "relevance-badge relevance-badge-very-low"


# Add this to your session state initialization
if 'translate_to_english' not in st.session_state:
    st.session_state.translate_to_english = False

# Add this function for translation
def translate_text(text: str, target_lang: str = "en") -> str:
    """Translate text using Azure OpenAI."""
    generator = st.session_state.generator
    
    prompt = f"""Translate the following German text to {target_lang}. 
    Maintain the original formatting and structure.
    
    Text to translate:
    {text}
    
    Provide only the translation, no explanations."""
    
    messages = [
        {"role": "system", "content": "You are a professional translator."},
        {"role": "user", "content": prompt}
    ]
    
    response = generator.client.chat.completions.create(
        model=generator.deployment,
        messages=messages,
        temperature=0.3,
        max_tokens=1500
    )
    
    return response.choices[0].message.content

# Update the display_job_card function to include translation
def display_job_card(job: Dict, index: int):
    """Display a job as a card with details."""
    relevance = job.get('relevance_score', 0)
    
    st.markdown(f"""
    <div class="job-card">
        <div class="job-title">🎯 {job['title']}</div>
        <div class="job-company">🏢 {job['company']}</div>
        <div class="job-details">
            📍 {job['location']} | 💼 {job.get('job_type', 'N/A')} | 🏷️ {job.get('category', 'N/A')}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander(f"📋 View Full Details & Strategy for {job['title']}", expanded=False):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Translation toggle
            translate_key = f"translate_{job['id']}_{index}"
            if translate_key not in st.session_state:
                st.session_state[translate_key] = False
            
            if st.button("🌐 Translate to English" if not st.session_state[translate_key] else "🇩🇪 Show Original", 
                        key=f"trans_btn_{job['id']}_{index}"):
                st.session_state[translate_key] = not st.session_state[translate_key]
                st.rerun()
            
            # Display description
            st.markdown("**📝 Job Description:**")
            description = job.get('description', 'No description available')
            if st.session_state[translate_key] and description != 'No description available':
                with st.spinner("Translating..."):
                    description = translate_text(description)
            st.write(description)
            
            # Display requirements
            st.markdown("**✅ Requirements:**")
            requirements = job.get('requirements', 'No requirements listed')
            if st.session_state[translate_key] and requirements != 'No requirements listed':
                with st.spinner("Translating..."):
                    requirements = translate_text(requirements)
            st.write(requirements)
            
            st.markdown(f"**🔗 Job URL:** [{job['url']}]({job['url']})")
        
        with col2:
            st.markdown("**📊 Job Info:**")
            st.info(f"""
            **ID:** {job['id']}  
            **Type:** {job.get('job_type', 'N/A')}  
            **Category:** {job.get('category', 'N/A')}
            """)
        
        # Generate personalized approach strategy
        if st.button(f"🎯 Get Approach Strategy", key=f"strategy_{job['id']}_{index}"):
            with st.spinner("Generating personalized approach strategy..."):
                strategy = generate_approach_strategy(job, st.session_state.user_cv)
                st.markdown(f"""
                <div class="strategy-box">
                    <h4>🎯 Your Personalized Approach Strategy:</h4>
                    {strategy}
                </div>
                """, unsafe_allow_html=True)

def generate_approach_strategy(job: Dict, user_cv: str) -> str:
    """Generate a personalized strategy for approaching this company at the job fair."""
    generator = st.session_state.generator
    
    cv_context = f"\n\nCandidate Background:\n{user_cv}" if user_cv else ""
    
    prompt = f"""Based on this job posting, provide a concise, actionable strategy for approaching this company at a job fair in person.

Job Details:
- Title: {job['title']}
- Company: {job['company']}
- Requirements: {job.get('requirements', 'N/A')}
- Description: {job.get('description', 'N/A')[:500]}...
{cv_context}

Provide:
1. Key talking points to mention (2-3 points)
2. Questions to ask the recruiter (2-3 questions)
3. How to stand out for this specific role
4. What materials/portfolio items to bring or show

Keep it practical and specific to this role. Format as a clear, bulleted list."""

    messages = [
        {"role": "system", "content": "You are a career coach helping candidates prepare for job fair interactions."},
        {"role": "user", "content": prompt}
    ]
    
    response = generator.client.chat.completions.create(
        model=generator.deployment,
        messages=messages,
        temperature=0.7,
        max_tokens=600
    )
    
    return response.choices[0].message.content


def search_jobs_by_cv(cv_text: str, top_k: int = 10) -> List[Dict]:
    """
    Search for jobs matching the user's CV.
    Uses intelligent keyword extraction and semantic search.
    """
    retriever = st.session_state.retriever
    generator = st.session_state.generator
    
    # Extract key skills and experience using AI
    extraction_prompt = f"""Analyze this CV and extract:
1. Key technical skills
2. Years of experience
3. Preferred job types
4. Preferred locations (if mentioned)

CV:
{cv_text[:1500]}

Provide a concise summary in this format:
Skills: [list]
Experience: [X years]
Job Types: [list]
Locations: [list if any]
"""
    
    messages = [
        {"role": "system", "content": "You are an expert at analyzing CVs and extracting key information."},
        {"role": "user", "content": extraction_prompt}
    ]
    
    response = generator.client.chat.completions.create(
        model=generator.deployment,
        messages=messages,
        temperature=0.3,
        max_tokens=300
    )
    
    cv_summary = response.choices[0].message.content
    
    # Create search query
    search_query = f"""Find jobs matching this candidate profile:

{cv_summary}

Full CV Summary:
{cv_text[:1000]}
"""
    
    # Search for jobs
    jobs = retriever.retrieve_jobs(search_query, top_k=top_k)
    
    return jobs


def search_jobs_by_query(query: str, filters: Dict, top_k: int = 10) -> List[Dict]:
    """Search jobs by query and filters."""
    retriever = st.session_state.retriever
    
    # Build filter dict
    where_filter = {}
    if filters.get('location') and filters['location'] != "All":
        where_filter['location'] = {'$eq': filters['location']}
    if filters.get('job_type') and filters['job_type'] != "All":
        where_filter['job_type'] = {'$eq': filters['job_type']}
    if filters.get('category') and filters['category'] != "All":
        where_filter['category'] = {'$eq': filters['category']}
    
    jobs = retriever.retrieve_jobs(
        query=query,
        top_k=top_k,
        filter_dict=where_filter if where_filter else None
    )
    
    return jobs


def main():
    """Main application."""
    
    # Header
    st.markdown('<div class="main-header">🎯 IT-CS Job Fair Navigator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Find your perfect job match and get personalized strategies to approach companies at the fair</div>', unsafe_allow_html=True)
    
    # Initialize RAG system
    if st.session_state.retriever is None or st.session_state.generator is None:
        with st.spinner("🔧 Initializing AI system..."):
            retriever, generator = initialize_rag_system()
            if retriever and generator:
                st.session_state.retriever = retriever
                st.session_state.generator = generator
                st.success("✅ System ready!")
            else:
                st.stop()
    
    retriever = st.session_state.retriever
    generator = st.session_state.generator
    
    # Sidebar
    with st.sidebar:
        st.header("🎯 Job Fair Tools")
        
        # Statistics
        stats = retriever.get_collection_stats()
        st.markdown(f"""
        <div class="stats-box">
            <h3>{stats['total_jobs']}</h3>
            <p>Companies at the Fair</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Search Mode
        st.subheader("🔍 Search Mode")
        search_mode = st.radio(
            "Choose how to search:",
            ["💬 AI Chat", "📄 Upload CV", "🔎 Manual Search"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Filters (for manual search)
        if search_mode == "🔎 Manual Search":
            st.subheader("🎚️ Filters")
            
            # Get unique values
            locations = ["All"] + retriever.get_all_locations()
            categories = ["All"] + retriever.get_all_categories()
            job_types = ["All", "Vollzeit", "Teilzeit", "Praktikum", "Werkstudent*in"]
            
            selected_location = st.selectbox("📍 Location", locations)
            selected_job_type = st.selectbox("💼 Job Type", job_types)
            selected_category = st.selectbox("🏷️ Category", categories)
            
            filters = {
                'location': selected_location,
                'job_type': selected_job_type,
                'category': selected_category
            }
        else:
            filters = {}
        
        st.markdown("---")
        
        # Number of results
        num_results = st.slider("📊 Number of results", 5, 20, 10)
        
        # Sort options
        if st.session_state.current_jobs:
            st.markdown("---")
            st.subheader("🔀 Sort Results")
            sort_option = st.selectbox(
                "Sort by:",
                ["relevance", "company", "location", "title"],
                format_func=lambda x: {
                    "relevance": "📊 Relevance Score",
                    "company": "🏢 Company Name",
                    "location": "📍 Location",
                    "title": "📝 Job Title"
                }[x]
            )
            
            if sort_option:
                st.session_state.current_jobs = sort_jobs(st.session_state.current_jobs, sort_option)
        
        st.markdown("---")
        
        # Clear button
        if st.button("🔄 Clear All", use_container_width=True):
            st.session_state.conversation_history = []
            st.session_state.current_jobs = []
            st.session_state.user_cv = ""
            st.rerun()
    
    # Main content area
    if search_mode == "💬 AI Chat":
        st.header("💬 Chat with AI Job Assistant")
        st.info("💡 Ask me anything about jobs at the fair! For example: 'I'm a Python developer looking for remote work' or 'What backend positions are available in Berlin?'")
        
        # Display conversation history
        for message in st.session_state.conversation_history:
            role = message['role']
            content = message['content']
            
            if role == 'user':
                st.markdown(f'<div class="chat-message user-message"><strong>You:</strong><br>{content}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message assistant-message"><strong>🤖 Assistant:</strong><br>{content}</div>', unsafe_allow_html=True)
        
        # Chat input
        user_query = st.chat_input("Ask about jobs at the fair...")
        
        if user_query:
            # Add user message to history
            st.session_state.conversation_history.append({
                'role': 'user',
                'content': user_query
            })
            
            # Search for jobs
            with st.spinner("🔍 Searching for relevant jobs..."):
                jobs = search_jobs_by_query(user_query, {}, num_results)
                st.session_state.current_jobs = jobs
            
            # Generate response
            with st.spinner("🤖 Generating response..."):
                job_context = format_job_context(jobs)
                
                # Use the correct method signature
                response = generator.generate_response(
                    query=user_query,
                    jobs=jobs,
                    job_context=job_context,
                    conversation_history=st.session_state.conversation_history[:-1]
                )
                
                # Add assistant response to history
                st.session_state.conversation_history.append({
                    'role': 'assistant',
                    'content': response
                })
            
            st.rerun()
        
        # Display current jobs
        if st.session_state.current_jobs:
            st.markdown("---")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"📋 Found {len(st.session_state.current_jobs)} Matching Jobs")
            with col2:
                csv_data = export_jobs_to_csv(st.session_state.current_jobs)
                st.download_button(
                    label="📥 Export CSV",
                    data=csv_data,
                    file_name="job_search_results.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            for i, job in enumerate(st.session_state.current_jobs):
                display_job_card(job, i)
    
    elif search_mode == "📄 Upload CV":
        st.header("📄 Find Jobs Based on Your CV")
        st.info("💡 Upload your CV (PDF, DOCX, or TXT), and I'll find the best-matching jobs at the fair for you!")
        
        # Get CV parser
        cv_parser = get_cv_parser()
        
        # Show supported formats
        supported_formats = list(cv_parser.supported_formats.keys())
        formats_display = ", ".join([f".{fmt}" for fmt in supported_formats])
        
        # CV input options
        cv_input_method = st.radio(
            "How would you like to provide your CV?", 
            ["📝 Paste Text", "📎 Upload File"],
            help=f"Supported file formats: {formats_display}"
        )
        
        cv_text = ""
        
        if cv_input_method == "📝 Paste Text":
            cv_text = st.text_area(
                "Paste your CV or professional summary:",
                height=300,
                placeholder="""Example:

    PROFESSIONAL SUMMARY
    Full-Stack Developer with 3 years of experience in React, Node.js, and Python. 
    Strong background in e-commerce platforms and cloud deployment (AWS).

    SKILLS
    - Frontend: React, Vue.js, TypeScript
    - Backend: Node.js, Python, Django
    - Cloud: AWS, Docker, Kubernetes
    - Databases: PostgreSQL, MongoDB

    EXPERIENCE
    Senior Developer at Tech Company (2021-2024)
    - Built scalable e-commerce platform
    - Implemented CI/CD pipelines
    - Led team of 4 developers

    EDUCATION
    B.Sc. Computer Science, Technical University (2018-2021)
                """,
                key="cv_paste_area"
            )
        
        else:  # Upload File
            uploaded_file = st.file_uploader(
                f"Upload your CV ({formats_display})",
                type=supported_formats,
                help=f"Maximum file size: {cv_parser.MAX_FILE_SIZE / 1024 / 1024:.0f} MB"
            )
            
            if uploaded_file:
                # Show file info
                file_size_mb = len(uploaded_file.getvalue()) / 1024 / 1024
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("File Name", uploaded_file.name)
                with col2:
                    st.metric("File Size", f"{file_size_mb:.2f} MB")
                with col3:
                    file_ext = Path(uploaded_file.name).suffix.lower().lstrip('.')
                    st.metric("Format", cv_parser.supported_formats.get(file_ext, "Unknown"))
                
                # Parse the file
                with st.spinner("📖 Reading your CV..."):
                    try:
                        file_content = uploaded_file.getvalue()
                        cv_text = cv_parser.parse_cv(file_content, uploaded_file.name)
                        
                        if cv_text:
                            st.success(f"✅ Successfully extracted {len(cv_text)} characters from your CV!")
                            
                            # Show preview
                            with st.expander("👀 Preview extracted text (first 500 characters)"):
                                st.text(cv_text[:500] + "..." if len(cv_text) > 500 else cv_text)
                        else:
                            st.error("❌ Failed to extract text from the file. Please try a different format or paste your CV as text.")
                            cv_text = ""
                    
                    except Exception as e:
                        st.error(f"❌ Error processing file: {str(e)}")
                        st.info("💡 Try using the 'Paste Text' option instead.")
                        cv_text = ""
        
        # Process CV if we have text
        if cv_text and len(cv_text.strip()) > 50:  # At least 50 characters
            st.session_state.user_cv = cv_text
            
            # Show CV statistics
            with st.expander("📊 CV Statistics"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Characters", f"{len(cv_text):,}")
                with col2:
                    word_count = len(cv_text.split())
                    st.metric("Word Count", f"{word_count:,}")
                with col3:
                    line_count = len(cv_text.split('\n'))
                    st.metric("Lines", f"{line_count:,}")
            
            # Search button
            if st.button("🎯 Find Matching Jobs", type="primary", use_container_width=True):
                with st.spinner("🔍 Analyzing your CV and finding best matches..."):
                    # Extract summary for better matching
                    cv_summary = cv_parser.extract_cv_summary(cv_text, max_length=1000)
                    
                    # Search for jobs
                    jobs = search_jobs_by_cv(cv_summary, num_results)
                    st.session_state.current_jobs = jobs
                
                if jobs:
                    st.success(f"✅ Found {len(jobs)} jobs matching your profile!")
                else:
                    st.warning("⚠️ No matching jobs found. Try adjusting your CV or search criteria.")
                
                st.rerun()
        
        elif cv_text and len(cv_text.strip()) <= 50:
            st.warning("⚠️ Your CV seems too short. Please provide more information for better matching.")
        
        # Display results
        if st.session_state.current_jobs:
            st.markdown("---")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"🎯 Top {len(st.session_state.current_jobs)} Jobs for Your Profile")
            with col2:
                csv_data = export_jobs_to_csv(st.session_state.current_jobs)
                st.download_button(
                    label="📥 Export CSV",
                    data=csv_data,
                    file_name="cv_matched_jobs.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            # Generate overall strategy
            if st.button("📋 Get Overall Job Fair Strategy", use_container_width=True):
                with st.spinner("Generating your personalized job fair strategy..."):
                    top_jobs = st.session_state.current_jobs[:5]
                    job_list = "\n".join([f"- {job['title']} at {job['company']}" for job in top_jobs])
                    
                    strategy_prompt = f"""Based on this candidate's CV and their top matching jobs, provide a comprehensive job fair strategy.

    Candidate CV:
    {st.session_state.user_cv[:1000]}

    Top Matching Jobs:
    {job_list}

    Provide:
    1. Overall preparation tips
    2. Priority order for visiting companies
    3. General talking points that work across multiple companies
    4. What to bring/prepare
    5. Time management tips for the fair

    Keep it actionable and specific."""

                    messages = [
                        {"role": "system", "content": "You are a career coach helping candidates prepare for job fairs."},
                        {"role": "user", "content": strategy_prompt}
                    ]
                    
                    response = generator.client.chat.completions.create(
                        model=generator.deployment,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=800
                    )
                    
                    st.markdown(f"""
                    <div class="strategy-box">
                        <h3>🎯 Your Job Fair Strategy:</h3>
                        {response.choices[0].message.content}
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            for i, job in enumerate(st.session_state.current_jobs):
                display_job_card(job, i)

    else:  # Manual Search
        st.header("🔎 Manual Job Search")
        st.info("💡 Use the filters in the sidebar and search by keywords below.")
        
        # Search input
        search_query = st.text_input(
            "🔍 Search keywords:",
            placeholder="e.g., Python, React, Machine Learning, DevOps..."
        )
        
        if st.button("🔍 Search Jobs", type="primary", use_container_width=True) or search_query:
            query = search_query if search_query else "software developer"
            
            with st.spinner("🔍 Searching jobs..."):
                jobs = search_jobs_by_query(query, filters, num_results)
                st.session_state.current_jobs = jobs
            
            if jobs:
                st.success(f"✅ Found {len(jobs)} matching jobs!")
            else:
                st.warning("⚠️ No jobs found. Try adjusting your filters or search terms.")
        
        # Display results
        if st.session_state.current_jobs:
            st.markdown("---")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"📋 Search Results ({len(st.session_state.current_jobs)} jobs)")
            with col2:
                csv_data = export_jobs_to_csv(st.session_state.current_jobs)
                st.download_button(
                    label="📥 Export CSV",
                    data=csv_data,
                    file_name="manual_search_results.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            for i, job in enumerate(st.session_state.current_jobs):
                display_job_card(job, i)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>🎯 IT-CS Job Fair Navigator | Powered by Azure OpenAI RAG System</p>
        <p style="font-size: 0.9rem;">Find your perfect match and ace your job fair conversations!</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()