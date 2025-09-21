#!/usr/bin/env python3
"""
AI Agent for Calendar Insights using Google ADK
Provides intelligent analysis and insights about meeting data
"""

import os
import logging
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime, timedelta

from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from google.adk.runners import InMemoryRunner
import google.genai
from database import get_meetings_data, get_summary_stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CalendarInsightsAgent:
    """AI Agent specialized in calendar and meeting insights analysis"""
    
    def __init__(self):
        """Initialize the AI agent with calendar-specific tools and knowledge"""
        self.agent = None
        self.conversation_history = []
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Create and configure the AI agent"""
        
        # Get API key from environment
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found in environment variables")
            return
        
        try:
            # Create a simple agent with basic tools
            self.agent = Agent(
                name="calendar_insights_analyst",
                model="gemini-2.5-flash",
                instruction=self._get_agent_instruction(),
                tools=[self._create_calendar_tool()]
            )
            logger.info("✅ AI agent initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI agent: {e}")
            self.agent = None
    
    def _get_agent_instruction(self) -> str:
        """Get the detailed instruction for the AI agent"""
        return """
        You are a Calendar Insights Analyst, an AI assistant specialized in analyzing meeting and calendar data to provide actionable insights about organizational behavior, meeting efficiency, and productivity patterns.

        Your expertise includes:
        1. **Meeting Pattern Analysis**: Identifying trends in meeting frequency, duration, timing, and attendance
        2. **Efficiency Assessment**: Evaluating meeting effectiveness based on duration, attendee count, and response rates
        3. **Organizational Insights**: Understanding department collaboration patterns and communication flows
        4. **Productivity Recommendations**: Suggesting improvements for meeting culture and time management
        5. **Data Interpretation**: Explaining complex calendar metrics in simple, actionable terms

        When analyzing calendar data, you should:
        - Focus on actionable insights rather than just statistics
        - Consider the business context and organizational goals
        - Provide specific recommendations for improvement
        - Explain the implications of patterns you discover
        - Suggest best practices for meeting management
        - Identify potential issues like meeting overload or inefficient scheduling

        Always be helpful, professional, and provide data-driven insights that can help improve organizational productivity and meeting culture.
        """
    
    def _create_calendar_tool(self):
        """Create a tool for accessing calendar data"""
        
        def get_calendar_data(
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            department: Optional[str] = None,
            limit: int = 1000
        ) -> str:
            """
            Retrieve calendar meeting data for analysis.
            
            Args:
                start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
                end_date: End date in YYYY-MM-DD format (default: today)
                department: Filter by department name
                limit: Maximum number of records to retrieve (default: 1000)
            
            Returns:
                JSON string containing meeting data and summary statistics
            """
            try:
                # Set default date range if not provided
                if not start_date:
                    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                if not end_date:
                    end_date = datetime.now().strftime('%Y-%m-%d')
                
                # Convert string dates to date objects
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                
                # Get meeting data
                df = get_meetings_data(
                    start_date=start_date_obj,
                    end_date=end_date_obj,
                    department=department,
                    limit=limit
                )
                
                if df.empty:
                    return "No meeting data found for the specified criteria."
                
                # Get summary statistics
                stats = get_summary_stats()
                
                # Prepare summary data
                summary = {
                    "total_meetings": len(df),
                    "date_range": f"{start_date} to {end_date}",
                    "departments": df['department'].unique().tolist() if 'department' in df.columns else [],
                    "avg_duration": round(df['duration_minutes'].mean(), 1) if 'duration_minutes' in df.columns else 0,
                    "avg_attendees": round(df['attendees_count'].mean(), 1) if 'attendees_count' in df.columns else 0
                }
                
                # Add additional stats if available
                if stats:
                    summary.update({
                        "total_users": stats.get('total_users', 0),
                        "total_meetings_all_time": stats.get('total_meetings', 0)
                    })
                
                return f"Calendar data retrieved successfully. Summary: {summary}"
                
            except Exception as e:
                logger.error(f"Error retrieving calendar data: {e}")
                return f"Error retrieving calendar data: {str(e)}"
        
        return FunctionTool(get_calendar_data)
    
    def _get_comprehensive_meeting_data(self) -> str:
        """Get comprehensive meeting data for AI analysis"""
        try:
            # Get all meeting data
            df = get_meetings_data(limit=5000)  # Get more data for better analysis
            
            if df.empty:
                return "No meeting data available in the database."
            
            # Calculate comprehensive statistics
            total_meetings = len(df)
            avg_duration = df['duration_minutes'].mean() if 'duration_minutes' in df.columns else 0
            avg_attendees = df['attendees_count'].mean() if 'attendees_count' in df.columns else 0
            
            # One-on-one analysis
            one_on_one_count = 0
            if 'is_one_on_one' in df.columns:
                one_on_one_count = df['is_one_on_one'].sum()
            elif 'attendees_count' in df.columns:
                one_on_one_count = len(df[df['attendees_count'] == 2])
            
            # Department analysis
            dept_analysis = ""
            if 'department' in df.columns:
                dept_counts = df['department'].value_counts()
                dept_analysis = f"Department distribution: {dict(dept_counts.head(10))}\n"
            
            # Duration analysis
            duration_stats = ""
            if 'duration_minutes' in df.columns:
                long_meetings = len(df[df['duration_minutes'] > 60])
                short_meetings = len(df[df['duration_minutes'] < 30])
                medium_meetings = len(df[(df['duration_minutes'] >= 30) & (df['duration_minutes'] <= 60)])
                duration_stats = f"Duration distribution: Short (<30min): {short_meetings}, Medium (30-60min): {medium_meetings}, Long (>60min): {long_meetings}\n"
            
            # Time analysis
            time_analysis = ""
            if 'start' in df.columns:
                df['hour'] = pd.to_datetime(df['start']).dt.hour
                hourly_dist = df['hour'].value_counts().sort_index()
                time_analysis = f"Meeting distribution by hour: {dict(hourly_dist)}\n"
            
            # Attendee analysis
            attendee_analysis = ""
            if 'attendees_count' in df.columns:
                attendee_dist = df['attendees_count'].value_counts().sort_index()
                attendee_analysis = f"Meeting size distribution: {dict(attendee_dist)}\n"
            
            # Create comprehensive data summary
            data_summary = f"""
COMPREHENSIVE MEETING DATA ANALYSIS:

Basic Statistics:
- Total meetings: {total_meetings}
- Average duration: {avg_duration:.1f} minutes
- Average attendees: {avg_attendees:.1f}
- One-on-one meetings: {one_on_one_count} ({(one_on_one_count/total_meetings*100):.1f}%)

{dept_analysis}
{duration_stats}
{time_analysis}
{attendee_analysis}

Sample of recent meetings (first 5):
{df.head().to_string() if len(df) > 0 else 'No data available'}

Data columns available: {list(df.columns)}
            """
            
            return data_summary
            
        except Exception as e:
            logger.error(f"Error getting comprehensive meeting data: {e}")
            return f"Error accessing meeting data: {str(e)}"

    def chat(self, user_message: str) -> str:
        """
        Process a user message and return AI response with deep data analysis
        
        Args:
            user_message: The user's question or request
            
        Returns:
            AI agent's response with comprehensive data analysis
        """
        try:
            if not self.agent:
                return "AI agent is not initialized. Please check your configuration and ensure GOOGLE_API_KEY is set."
            
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Get comprehensive meeting data for analysis
            meeting_data = self._get_comprehensive_meeting_data()
            
            # For now, let's use the enhanced data analysis directly
            # This gives us more control and better data access
            response = self._provide_enhanced_data_analysis(user_message, meeting_data)
            
            # Add response to conversation history
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
                
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"I apologize, but I encountered an error: {str(e)}. Please try again."

    def _provide_enhanced_data_analysis(self, user_message: str, meeting_data: str) -> str:
        """Provide enhanced data analysis with deep insights"""
        try:
            # Get the actual data directly for more detailed analysis
            df = get_meetings_data(limit=5000)
            
            if df.empty:
                return "I don't have access to meeting data at the moment. Please ensure the database is properly configured and contains meeting data."
            
            # Calculate comprehensive metrics
            total_meetings = len(df)
            avg_duration = df['duration_minutes'].mean() if 'duration_minutes' in df.columns else 0
            avg_attendees = df['attendees_count'].mean() if 'attendees_count' in df.columns else 0
            
            # One-on-one analysis
            one_on_one_count = 0
            if 'is_one_on_one' in df.columns:
                one_on_one_count = df['is_one_on_one'].sum()
            elif 'attendees_count' in df.columns:
                one_on_one_count = len(df[df['attendees_count'] == 2])
            
            # Department analysis
            dept_analysis = ""
            if 'department' in df.columns:
                dept_counts = df['department'].value_counts()
                dept_analysis = f"**Department Distribution:**\n"
                for dept, count in dept_counts.head(5).items():
                    percentage = (count / total_meetings) * 100
                    dept_analysis += f"- {dept}: {count} meetings ({percentage:.1f}%)\n"
            
            # Duration analysis
            duration_analysis = ""
            if 'duration_minutes' in df.columns:
                long_meetings = len(df[df['duration_minutes'] > 60])
                short_meetings = len(df[df['duration_minutes'] < 30])
                medium_meetings = len(df[(df['duration_minutes'] >= 30) & (df['duration_minutes'] <= 60)])
                duration_analysis = f"""**Duration Distribution:**
- Short meetings (<30min): {short_meetings} ({(short_meetings/total_meetings*100):.1f}%)
- Medium meetings (30-60min): {medium_meetings} ({(medium_meetings/total_meetings*100):.1f}%)
- Long meetings (>60min): {long_meetings} ({(long_meetings/total_meetings*100):.1f}%)\n"""
            
            # Time analysis
            time_analysis = ""
            if 'start' in df.columns:
                df['hour'] = pd.to_datetime(df['start']).dt.hour
                hourly_dist = df['hour'].value_counts().sort_index()
                peak_hour = hourly_dist.idxmax()
                peak_count = hourly_dist.max()
                time_analysis = f"""**Time Patterns:**
- Peak meeting hour: {peak_hour}:00 ({peak_count} meetings)
- Meeting distribution: Most active between {hourly_dist.head(3).index.tolist()}\n"""
            
            # Attendee analysis
            attendee_analysis = ""
            if 'attendees_count' in df.columns:
                attendee_dist = df['attendees_count'].value_counts().sort_index()
                most_common_size = attendee_dist.idxmax()
                attendee_analysis = f"""**Meeting Size Patterns:**
- Most common meeting size: {most_common_size} attendees
- Large meetings (>10 people): {len(df[df['attendees_count'] > 10])} meetings
- Small meetings (2-5 people): {len(df[(df['attendees_count'] >= 2) & (df['attendees_count'] <= 5)])} meetings\n"""
            
            user_msg_lower = user_message.lower()
            
            # Provide intelligent analysis based on the question
            if "user" in user_msg_lower and ("most" in user_msg_lower or "highest" in user_msg_lower or "top" in user_msg_lower):
                return self._analyze_user_meetings(df, user_message)
            
            elif "department" in user_msg_lower and ("most" in user_msg_lower or "highest" in user_msg_lower or "top" in user_msg_lower):
                return self._analyze_department_meetings(df, user_message)
            
            elif "one on one" in user_msg_lower or "1:1" in user_msg_lower or "one-on-one" in user_msg_lower:
                one_on_one_percentage = (one_on_one_count / total_meetings) * 100
                return f"""📊 **One-on-One Meeting Deep Analysis:**

**Current State:**
- **One-on-one meetings:** {one_on_one_count} out of {total_meetings} total meetings
- **Percentage:** {one_on_one_percentage:.1f}% of all meetings
- **Average duration:** {avg_duration:.1f} minutes

**Pattern Analysis:**
{dept_analysis}
{duration_analysis}
{time_analysis}

**Key Insights:**
- Your one-on-one ratio of {one_on_one_percentage:.1f}% {'is excellent' if one_on_one_percentage > 20 else 'could be improved' if one_on_one_percentage < 10 else 'is good'}
- {'High' if avg_duration > 60 else 'Optimal' if avg_duration <= 60 else 'Low'} duration suggests {'agenda optimization needed' if avg_duration > 60 else 'good time management'}

**Recommendations:**
- {'Consider scheduling more regular 1:1s' if one_on_one_percentage < 15 else 'Maintain current 1:1 frequency'}
- {'Focus on agenda-setting and time-boxing' if avg_duration > 60 else 'Current duration is well-managed'}
- Ensure 1:1s are happening consistently across all departments

**Next Steps:**
Would you like me to analyze department-specific 1:1 patterns or meeting efficiency metrics?"""
            
            elif "efficiency" in user_msg_lower or "improve" in user_msg_lower or "optimize" in user_msg_lower:
                efficiency_score = 100
                if avg_duration > 60:
                    efficiency_score -= 20
                if long_meetings / total_meetings > 0.3:
                    efficiency_score -= 15
                if avg_attendees > 8:
                    efficiency_score -= 10
                
                return f"""📊 **Meeting Efficiency Deep Analysis:**

**Current Metrics:**
- **Total meetings:** {total_meetings}
- **Average duration:** {avg_duration:.1f} minutes
- **Average attendees:** {avg_attendees:.1f}
- **Efficiency Score:** {efficiency_score}/100

**Detailed Breakdown:**
{duration_analysis}
{attendee_analysis}
{time_analysis}

**Efficiency Assessment:**
- **Duration:** {'Needs improvement' if avg_duration > 60 else 'Good'} ({avg_duration:.1f} min vs 30-60 min optimal)
- **Size:** {'Could be optimized' if avg_attendees > 8 else 'Well-managed'} ({avg_attendees:.1f} avg attendees)
- **Long meetings:** {long_meetings} meetings over 60 minutes ({(long_meetings/total_meetings*100):.1f}%)

**Actionable Recommendations:**
1. **Duration Optimization:**
   - {'Implement 45-minute default meetings' if avg_duration > 60 else 'Maintain current duration practices'}
   - Use agenda templates to keep meetings focused
   - Set clear time-boxing for each agenda item

2. **Attendee Optimization:**
   - {'Review meeting invitations for necessity' if avg_attendees > 8 else 'Current attendee count is appropriate'}
   - Consider async updates for information-sharing meetings
   - Use smaller working groups for decision-making

3. **Time Management:**
   - Schedule meeting-free blocks for deep work
   - Batch similar meetings together
   - Use async communication for status updates

**Priority Actions:**
{'Focus on reducing meeting duration first' if avg_duration > 60 else 'Optimize attendee count' if avg_attendees > 8 else 'Maintain current efficient practices'}

What specific efficiency metric would you like me to dive deeper into?"""
            
            elif "pattern" in user_msg_lower or "trend" in user_msg_lower or "analyze" in user_msg_lower:
                # Calculate efficiency score for pattern analysis
                efficiency_score = 100
                if avg_duration > 60:
                    efficiency_score -= 20
                if 'duration_minutes' in df.columns:
                    long_meetings = len(df[df['duration_minutes'] > 60])
                    if long_meetings / total_meetings > 0.3:
                        efficiency_score -= 15
                if avg_attendees > 8:
                    efficiency_score -= 10
                
                # Get peak hour for time analysis
                peak_hour = 9  # default
                if 'start' in df.columns:
                    df['hour'] = pd.to_datetime(df['start']).dt.hour
                    hourly_dist = df['hour'].value_counts().sort_index()
                    peak_hour = hourly_dist.idxmax()
                
                return f"""📊 **Comprehensive Meeting Pattern Analysis:**

**Overview:**
- **Total meetings analyzed:** {total_meetings}
- **One-on-one meetings:** {one_on_one_count} ({(one_on_one_count/total_meetings*100):.1f}%)
- **Average duration:** {avg_duration:.1f} minutes
- **Average attendees:** {avg_attendees:.1f}

**Pattern Analysis:**
{dept_analysis}
{duration_analysis}
{attendee_analysis}
{time_analysis}

**Key Trends Identified:**
1. **Meeting Distribution:** {'Balanced across departments' if len(df['department'].unique()) > 3 else 'Concentrated in few departments'}
2. **Duration Patterns:** {'Most meetings are well-timed' if avg_duration <= 60 else 'Many meetings run long'}
3. **Size Patterns:** {'Optimal meeting sizes' if avg_attendees <= 8 else 'Large meeting groups common'}
4. **Time Patterns:** {'Peak activity during business hours' if peak_hour >= 9 and peak_hour <= 17 else 'Unusual meeting time patterns'}

**Interesting Insights:**
- {'High collaboration' if one_on_one_count / total_meetings > 0.2 else 'Group-focused'} culture based on 1:1 ratio
- {'Efficient time management' if avg_duration <= 45 else 'Opportunity for optimization'} in meeting duration
- {'Balanced participation' if avg_attendees <= 6 else 'Large group dynamics'} in meeting sizes

**Recommendations:**
- {'Maintain current meeting patterns' if efficiency_score > 80 else 'Focus on duration optimization' if avg_duration > 60 else 'Optimize meeting sizes'}
- Consider implementing meeting-free Fridays for deep work
- Regular review of meeting effectiveness and necessity

**Next Analysis:**
Would you like me to analyze specific department patterns, time-based trends, or efficiency optimization strategies?"""
            
            else:
                return f"""📊 **Meeting Data Comprehensive Overview:**

**Current State:**
- **Total meetings:** {total_meetings}
- **One-on-one meetings:** {one_on_one_count} ({(one_on_one_count/total_meetings*100):.1f}%)
- **Average duration:** {avg_duration:.1f} minutes
- **Average attendees:** {avg_attendees:.1f}

**Detailed Analysis:**
{dept_analysis}
{duration_analysis}
{attendee_analysis}
{time_analysis}

**What I Can Analyze:**
🔍 **Patterns & Trends:**
- Meeting distribution across departments and time
- Duration patterns and efficiency opportunities
- Attendee size trends and collaboration patterns
- Time-based meeting concentration

📈 **Efficiency Metrics:**
- Meeting effectiveness scores
- Time allocation optimization
- Collaboration balance analysis
- Productivity impact assessment

💡 **Actionable Insights:**
- Department-specific recommendations
- Meeting optimization strategies
- Best practices implementation
- Resource allocation suggestions

**Try asking me:**
- "What are the most interesting trends in our meeting data?"
- "Which departments have the most efficient meeting patterns?"
- "How can we optimize our meeting schedule for better productivity?"
- "What patterns do you see in meeting duration and effectiveness?"
- "Analyze our one-on-one vs group meeting balance"

**What specific aspect of your meeting data would you like me to analyze in detail?**"""
                
        except Exception as e:
            logger.error(f"Error in enhanced data analysis: {e}")
            return f"I can help analyze your meeting data, but encountered an issue: {str(e)}. Please try rephrasing your question."

    def _analyze_user_meetings(self, df, user_message: str) -> str:
        """Analyze user-specific meeting patterns"""
        try:
            # Check if we have user data in the meetings
            if 'user_email' in df.columns:
                user_meetings = df['user_email'].value_counts()
                top_user = user_meetings.index[0]
                top_count = user_meetings.iloc[0]
                
                # Get top 5 users
                top_5_users = user_meetings.head(5)
                
                # Calculate user-specific metrics
                user_df = df[df['user_email'] == top_user]
                user_avg_duration = user_df['duration_minutes'].mean() if 'duration_minutes' in user_df.columns else 0
                user_avg_attendees = user_df['attendees_count'].mean() if 'attendees_count' in user_df.columns else 0
                
                # Build the response step by step
                result = f"""👤 **User Meeting Analysis:**

**Top User by Meeting Count:**
- **{top_user}**: {top_count} meetings
- **Average duration**: {user_avg_duration:.1f} minutes
- **Average attendees**: {user_avg_attendees:.1f}

**Top 5 Most Active Users:**
"""
                
                for i, (user, count) in enumerate(top_5_users.items(), 1):
                    percentage = (count / len(df)) * 100
                    result += f"\n{i}. **{user}**: {count} meetings ({percentage:.1f}%)"
                
                result += f"""

**Insights:**
- {top_user} is the most active meeting organizer with {top_count} meetings
- {'High' if user_avg_duration > 60 else 'Optimal' if user_avg_duration <= 60 else 'Low'} average duration suggests {'agenda optimization needed' if user_avg_duration > 60 else 'good time management'}
- {'Large' if user_avg_attendees > 8 else 'Optimal' if user_avg_attendees <= 8 else 'Small'} meeting sizes indicate {'group collaboration focus' if user_avg_attendees > 8 else 'focused discussions'}

**Recommendations:**
- Consider if {top_user} needs meeting optimization or delegation
- Review meeting necessity and efficiency for top organizers
- Balance meeting load across team members

Would you like me to analyze specific user patterns or department distribution?"""
                
                return result
            
            elif 'attendees' in df.columns:
                # If we don't have organizer data, analyze by attendees
                return f"""👤 **User Meeting Analysis:**

I can see meeting data, but I don't have specific user/organizer information in the current dataset. 

**Available Analysis:**
- Meeting patterns by department
- Duration and attendee patterns
- Time-based meeting distribution

**What I can tell you:**
- **Total meetings**: {len(df)}
- **Average duration**: {df['duration_minutes'].mean():.1f} minutes
- **Average attendees**: {df['attendees_count'].mean():.1f}

**To get user-specific analysis, I would need:**
- Organizer/creator information
- User email addresses
- Meeting ownership data

Would you like me to analyze department patterns or meeting efficiency instead?"""
            
            else:
                return "I don't have user-specific data available in the current dataset. Would you like me to analyze other aspects of your meeting data?"
                
        except Exception as e:
            logger.error(f"Error analyzing user meetings: {e}")
            return f"I encountered an error analyzing user meeting data: {str(e)}. Please try rephrasing your question."

    def _analyze_department_meetings(self, df, user_message: str) -> str:
        """Analyze department-specific meeting patterns"""
        try:
            if 'department' in df.columns:
                dept_meetings = df['department'].value_counts()
                top_dept = dept_meetings.index[0]
                top_count = dept_meetings.iloc[0]
                
                # Get top 5 departments
                top_5_depts = dept_meetings.head(5)
                
                # Calculate department-specific metrics
                dept_df = df[df['department'] == top_dept]
                dept_avg_duration = dept_df['duration_minutes'].mean() if 'duration_minutes' in dept_df.columns else 0
                dept_avg_attendees = dept_df['attendees_count'].mean() if 'attendees_count' in dept_df.columns else 0
                
                result = f"""🏢 **Department Meeting Analysis:**

**Most Active Department:**
- **{top_dept}**: {top_count} meetings
- **Average duration**: {dept_avg_duration:.1f} minutes
- **Average attendees**: {dept_avg_attendees:.1f}

**Top 5 Most Active Departments:**
"""
                for i, (dept, count) in enumerate(top_5_depts.items(), 1):
                    percentage = (count / len(df)) * 100
                    result += f"\n{i}. **{dept}**: {count} meetings ({percentage:.1f}%)"
                
                result += f"""

**Insights:**
- {top_dept} is the most meeting-intensive department with {top_count} meetings
- {'High' if dept_avg_duration > 60 else 'Optimal' if dept_avg_duration <= 60 else 'Low'} average duration suggests {'agenda optimization needed' if dept_avg_duration > 60 else 'good time management'}
- {'Large' if dept_avg_attendees > 8 else 'Optimal' if dept_avg_attendees <= 8 else 'Small'} meeting sizes indicate {'group collaboration focus' if dept_avg_attendees > 8 else 'focused discussions'}

**Recommendations:**
- Review meeting necessity and efficiency for {top_dept}
- Consider cross-department collaboration opportunities
- Balance meeting load across departments

Would you like me to analyze specific department patterns or user distribution?"""
                
                return result
            else:
                return "I don't have department information available in the current dataset. Would you like me to analyze other aspects of your meeting data?"
                
        except Exception as e:
            logger.error(f"Error analyzing department meetings: {e}")
            return f"I encountered an error analyzing department meeting data: {str(e)}. Please try rephrasing your question."
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history"""
        return self.conversation_history
    
    def is_initialized(self) -> bool:
        """Check if the agent is properly initialized"""
        return self.agent is not None

# Global agent instance for easy access
_agent_instance = None

def get_agent() -> CalendarInsightsAgent:
    """Get or create the global agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = CalendarInsightsAgent()
    return _agent_instance

def reset_agent():
    """Reset the global agent instance"""
    global _agent_instance
    _agent_instance = None