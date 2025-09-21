#!/usr/bin/env python3
"""
AI Chat Interface for Calendar Insights
Streamlit-based chat interface for interacting with the AI agent
"""

import streamlit as st
import logging
import os
from datetime import datetime
from typing import List, Dict
import json

from ai_agent import get_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_session_state():
    """Initialize session state variables for the chat interface"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'agent' not in st.session_state:
        try:
            st.session_state.agent = get_agent()
        except Exception as e:
            st.error(f"Failed to initialize AI agent: {e}")
            st.session_state.agent = None

def display_chat_message(role: str, content: str, timestamp: str = None):
    """Display a chat message with appropriate styling"""
    with st.chat_message(role):
        st.markdown(content)
        if timestamp:
            st.caption(timestamp)

def display_conversation_history():
    """Display the conversation history"""
    for message in st.session_state.messages:
        display_chat_message(
            message["role"], 
            message["content"], 
            message.get("timestamp")
        )

def add_message_to_history(role: str, content: str):
    """Add a message to the conversation history"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.messages.append({
        "role": role,
        "content": content,
        "timestamp": timestamp
    })

def get_suggested_questions() -> List[str]:
    """Get a list of suggested questions for the user"""
    return [
        "What are the most common meeting patterns in our organization?",
        "Which departments have the most meetings?",
        "What's the average meeting duration and how can we improve efficiency?",
        "Are there any meeting overload issues I should be aware of?",
        "How many one-on-one meetings do we have compared to group meetings?",
        "What time of day do most meetings occur?",
        "Which day of the week has the most meetings?",
        "What's our meeting acceptance rate and what does it tell us?",
        "Can you analyze our meeting efficiency scores?",
        "What recommendations do you have for improving our meeting culture?"
    ]

def display_suggested_questions():
    """Display suggested questions as clickable buttons"""
    st.subheader("💡 Suggested Questions")
    
    suggested_questions = get_suggested_questions()
    
    # Create columns for better layout
    cols = st.columns(2)
    
    for i, question in enumerate(suggested_questions):
        col_idx = i % 2
        with cols[col_idx]:
            if st.button(
                question, 
                key=f"suggested_{i}",
                help="Click to ask this question",
                use_container_width=True
            ):
                # Add the question to the chat input
                st.session_state.user_input = question
                st.rerun()

def process_user_input(user_input: str) -> str:
    """Process user input and return AI response"""
    if not st.session_state.agent:
        return "❌ AI agent is not available. Please check the configuration and ensure GOOGLE_API_KEY is set."
    
    try:
        # Check if agent is properly initialized
        if hasattr(st.session_state.agent, 'is_initialized') and not st.session_state.agent.is_initialized():
            return "❌ AI agent is not properly initialized. Please check your Google API key configuration."
        
        # Show typing indicator
        with st.spinner("🤖 AI is thinking..."):
            response = st.session_state.agent.chat(user_input)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing user input: {e}")
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Full error traceback: {error_details}")
        
        return f"""❌ I apologize, but I encountered an error while processing your request: {str(e)}

**Troubleshooting Tips:**
- Ensure your Google API key is correctly configured
- Check that the database is accessible
- Try rephrasing your question
- Contact support if the issue persists

Please try again or rephrase your question."""

# def display_ai_capabilities():
#     """Display information about AI capabilities"""
#     with st.expander("🤖 AI Assistant Capabilities"):
#         st.markdown("""
#         **Our AI Assistant can help you with:**
        
#         📊 **Meeting Analytics**
#         - Analyze meeting patterns and trends
#         - Identify efficiency opportunities
#         - Compare department collaboration
        
#         📈 **Insights & Recommendations**
#         - Suggest meeting optimization strategies
#         - Identify potential meeting overload
#         - Recommend best practices
        
#         🔍 **Data Analysis**
#         - Deep dive into specific time periods
#         - Compare different departments or users
#         - Analyze meeting response rates
        
#         💡 **Smart Questions**
#         - Ask natural language questions about your data
#         - Get contextual insights and explanations
#         - Receive actionable recommendations
        
#         **Example Questions:**
#         - "What's our meeting efficiency like this month?"
#         - "Which departments collaborate the most?"
#         - "How can we reduce meeting time while maintaining productivity?"
#         """)

def main():
    """Main chat interface function"""
    st.set_page_config(
        page_title="AI Calendar Insights Chat",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 AI Calendar Insights Assistant")
    st.markdown("Ask me anything about your meeting data and get intelligent insights!")
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar with capabilities and controls
    with st.sidebar:
        st.header("🎛️ Chat Controls")
        
        # # Display AI capabilities
        # display_ai_capabilities()
        
        # Clear conversation button
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            if st.session_state.agent:
                st.session_state.agent.clear_conversation()
            st.rerun()
        
        # Export conversation
        if st.session_state.messages:
            if st.button("📥 Export Chat", use_container_width=True):
                chat_data = {
                    "timestamp": datetime.now().isoformat(),
                    "conversation": st.session_state.messages
                }
                st.download_button(
                    label="Download Chat History",
                    data=json.dumps(chat_data, indent=2),
                    file_name=f"calendar_insights_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        # Agent status and environment info
        st.subheader("🔧 System Status")
        
        # # Check API key
        # api_key = os.getenv('GOOGLE_API_KEY')
        # if api_key:
        #     st.success("✅ Google API Key Available")
        # else:
        #     st.error("❌ Google API Key Missing")
        
        # Check agent status
        if st.session_state.agent:
            st.success("✅ AI Agent Ready")
            if hasattr(st.session_state.agent, 'is_initialized'):
                if st.session_state.agent.is_initialized():
                    st.success("✅ Agent Initialized")
                else:
                    st.warning("⚠️ Agent Not Initialized")
        else:
            st.error("❌ AI Agent Not Available")
        
#         # Environment info
#         with st.expander("🔍 Environment Details"):
#             st.code(f"""
# API Key: {'✅ Available' if api_key else '❌ Missing'}
# Environment: {os.getenv('ENVIRONMENT', 'Not set')}
# Database Host: {os.getenv('POSTGRES_HOST', 'Not set')}
# Database Port: {os.getenv('POSTGRES_PORT', 'Not set')}
# Database Name: {os.getenv('POSTGRES_DB', 'Not set')}
#             """)
    
    # # Main chat interface
    # col1, col2 = st.columns([2, 1])
    
    # with col1:
    #     # Display conversation history
    #     if st.session_state.messages:
    #         display_conversation_history()
    #     else:
    #         # Welcome message
    #         st.markdown("""
    #         👋 **Welcome to the AI Calendar Insights Assistant!**
            
    #         I can help you analyze your meeting data and provide insights about:
    #         - Meeting patterns and trends
    #         - Efficiency opportunities
    #         - Department collaboration
    #         - Best practices and recommendations
            
    #         Try asking me a question or click on one of the suggested questions below!
    #         """)
    
    # with col2:
    #     # Suggested questions
    #     display_suggested_questions()
        
    #     # Quick stats
    #     st.subheader("📊 Quick Stats")
    #     try:
    #         from database import get_summary_stats
    #         stats = get_summary_stats()
    #         if stats:
    #             st.metric("Total Meetings", f"{stats.get('total_meetings', 0):,}")
    #             st.metric("Active Users", f"{stats.get('total_users', 0):,}")
    #             st.metric("Avg Duration", f"{stats.get('avg_duration', 0):.0f} min")
    #             st.metric("Avg Attendees", f"{stats.get('avg_attendees', 0):.1f}")
    #         else:
    #             st.info("No data available")
    #     except Exception as e:
    #         st.warning("Unable to load quick stats")
    
    # Chat input moved below the main content
    st.markdown("---")
    if prompt := st.chat_input("Ask me about your meeting data..."):
        # Add user message to history
        add_message_to_history("user", prompt)
        
        # Display user message
        display_chat_message("user", prompt)
        
        # Process and display AI response
        response = process_user_input(prompt)
        add_message_to_history("assistant", response)
        display_chat_message("assistant", response)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "💡 **Tip:** Ask specific questions about your data, or use natural language to get insights. "
        "The AI can analyze patterns, suggest improvements, and help you understand your meeting culture better."
    )

if __name__ == "__main__":
    main()
