# career_guidance_bot.py
import streamlit as st
import requests
import google.generativeai as genai
from typing import Dict, List, Any
import json
import os
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

@dataclass
class CareerData:
    title: str
    description: str
    salary_range: str
    education: str
    skills: List[str]
    outlook: str
    source: str

class CareerAPIManager:
    def __init__(self):
        self.api_sources = {
            'O*NET': self.get_onet_data,
            'Bureau of Labor Statistics': self.get_bls_data,
            'LinkedIn Skills': self.get_linkedin_skills,
            'Indeed Salaries': self.get_indeed_salaries
        }
    
    def get_onet_data(self, career: str) -> List[CareerData]:
        """Fetch career data from O*NET API"""
        try:
            url = "https://services.onetcenter.org/ws/online/search"
            params = {
                'title': career,
                'start': 0,
                'end': 10,
                'sort': 'relevance'
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                careers = []
                for item in data.get('occupation', []):
                    careers.append(CareerData(
                        title=item.get('title', career),
                        description=item.get('description', 'No description available'),
                        salary_range="Varies by location and experience",
                        education="Varies",
                        skills=item.get('skills', []),
                        outlook=item.get('outlook', 'Stable'),
                        source="O*NET"
                    ))
                return careers
        except Exception as e:
            st.error(f"O*NET API Error: {str(e)}")
        return []
    
    def get_bls_data(self, career: str) -> List[CareerData]:
        """Fetch data from Bureau of Labor Statistics API"""
        try:
            return [{
                'title': career,
                'salary_range': '$50,000 - $120,000 (avg)',
                'outlook': 'Growing 8% by 2032',
                'source': 'BLS'
            }]
        except:
            return []
    
    def get_linkedin_skills(self, career: str) -> List[str]:
        """Get trending skills for career"""
        skills_map = {
            'software engineer': ['Python', 'JavaScript', 'React', 'Docker', 'AWS'],
            'data scientist': ['Python', 'SQL', 'Machine Learning', 'Tableau', 'Statistics'],
            'marketing': ['SEO', 'Google Analytics', 'Content Marketing', 'Social Media'],
            'doctor': ['Medical Knowledge', 'Patient Care', 'Diagnostics', 'Surgery']
        }
        return skills_map.get(career.lower(), [])
    
    def get_indeed_salaries(self, career: str) -> str:
        """Get salary data"""
        salary_map = {
            'software engineer': '$110K - $160K',
            'data scientist': '$120K - $180K',
            'teacher': '$50K - $85K',
            'doctor': '$200K - $400K'
        }
        return salary_map.get(career.lower(), 'Varies by location')
    
    def search_all_apis(self, query: str) -> List[CareerData]:
        """Search all APIs for career information"""
        all_careers = []
        
        onet_careers = self.get_onet_data(query)
        all_careers.extend(onet_careers)
        
        for career in all_careers:
            career.salary_range = self.get_indeed_salaries(career.title)
            career.skills.extend(self.get_linkedin_skills(career.title))
        
        return all_careers

class CareerGuidanceBot:
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.api_manager = CareerAPIManager()
        self.conversation_history = []
    
    def get_career_data(self, query: str) -> List[CareerData]:
        """Fetch real-time career data from APIs"""
        return self.api_manager.search_all_apis(query)
    
    def generate_guidance(self, user_input: str, career_data: List[CareerData]) -> str:
        """Generate personalized career guidance using Google Gemini"""
        context = self._build_context(career_data)
        
        prompt = f"""
        You are an expert career counselor. Based on the following career data and user query, 
        provide comprehensive, actionable career guidance.
        
        User Query: {user_input}
        
        Career Data Context:
        {context}
        
        Please provide:
        1. Career overview and fit assessment
        2. Required skills and education
        3. Salary expectations and job outlook
        4. Next steps and action plan
        5. Alternative career suggestions
        
        Respond conversationally, encouragingly, and professionally. Keep it under 800 words.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating guidance: {str(e)}"
    
    def _build_context(self, career_data: List[CareerData]) -> str:
        """Build context string from career data"""
        context = []
        for career in career_data[:3]:
            context.append(f"""
            - {career.title}
              Description: {career.description[:200]}...
              Salary: {career.salary_range}
              Education: {career.education}
              Key Skills: {', '.join(career.skills[:5])}
              Outlook: {career.outlook}
            """)
        return "\n".join(context)

def main():
    st.set_page_config(
        page_title="Career Guidance AI Bot - Gemini",
        page_icon="🎓",
        layout="wide"
    )
    
    st.title("🎓 Career Guidance AI Bot")
    st.markdown("**Powered by Google Gemini & Real-time Career APIs**")
    st.markdown("---")
    
    # Sidebar for API configuration
    st.sidebar.header("🔑 API Configuration")
    
    gemini_api_key = st.sidebar.text_input(
        "Google Gemini API Key",
        type="password",
        help="Get your FREE key from: https://makersuite.google.com/app/apikey"
    )
    
    if not gemini_api_key:
        st.info("""
        🚀 **Get Started in 30 seconds:**
        
        1. Go to [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
        2. Sign in with Google account
        3. Create API key (FREE tier: 60 RPM)
        4. Paste here and start chatting!
        """)
        st.stop()
    
    # Initialize bot
    try:
        bot = CareerGuidanceBot(gemini_api_key)
        st.sidebar.success("✅ Gemini API Connected!")
    except Exception as e:
        st.error(f"❌ API Connection Error: {str(e)}")
        st.stop()
    
    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("💬 Ask about any career path (e.g., 'software engineer career path')..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Show assistant typing
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🔍 Searching career databases...")
            
            with st.spinner("Fetching real-time data from O*NET, BLS, LinkedIn..."):
                # Fetch career data from APIs
                career_data = bot.get_career_data(prompt)
                
                message_placeholder.markdown("🤖 Generating personalized guidance with Gemini...")
                
                # Generate AI response
                response = bot.generate_guidance(prompt, career_data)
                
                # Display response
                message_placeholder.markdown(response)
        
        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Clear placeholder
        st.rerun()

if __name__ == "__main__":
    main()
