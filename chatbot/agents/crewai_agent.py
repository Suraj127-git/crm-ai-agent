from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

def create_crew_agents():
    """Create a crew of AI agents for educational CRM"""
    
    # Initialize the LLM
    llm = ChatOpenAI(model="gpt-4o")
    
    # Create the education advisor agent
    education_advisor = Agent(
        role="Education Advisor",
        goal="Help students find the perfect courses for their career goals",
        backstory="""You are an experienced education advisor with years of 
        experience guiding students toward their ideal learning paths. You 
        understand the education market and how different courses can benefit 
        different career trajectories.""",
        verbose=True,
        allow_delegation=True,
        llm=llm
    )
    
    # Create the course content expert
    content_expert = Agent(
        role="Course Content Expert",
        goal="Provide detailed information about course content and learning outcomes",
        backstory="""You are a course content expert who has reviewed thousands of
        educational programs. You can explain complex topics in simple terms and
        help students understand what they will learn in each course.""",
        verbose=True,
        allow_delegation=True,
        llm=llm
    )
    
    # Create the career counselor
    career_counselor = Agent(
        role="Career Counselor",
        goal="Connect educational choices to career outcomes",
        backstory="""You are a career development specialist who helps students
        understand how specific courses will impact their job prospects and
        career progression. You stay up-to-date with industry trends.""",
        verbose=True,
        allow_delegation=True,
        llm=llm
    )
    
    return {
        "education_advisor": education_advisor,
        "content_expert": content_expert,
        "career_counselor": career_counselor
    }

def create_course_recommendation_crew(user_query, user_profile, available_courses):
    """Create a crew for course recommendations"""
    agents = create_crew_agents()
    
    # Define the tasks
    analyze_user_needs = Task(
        description=f"""Analyze the user query: '{user_query}' along with their profile
        to understand their educational needs and goals.""",
        agent=agents["education_advisor"],
    )
    
    find_matching_courses = Task(
        description=f"""Based on the user's needs, review the available courses and
        identify the top 3 most suitable options. Available courses: {available_courses}""",
        agent=agents["content_expert"],
    )
    
    explain_career_benefits = Task(
        description="""For each recommended course, explain how it will benefit
        the user's career path and what specific job opportunities it might open up.""",
        agent=agents["career_counselor"],
    )
    
    # Create the crew
    crew = Crew(
        agents=list(agents.values()),
        tasks=[analyze_user_needs, find_matching_courses, explain_career_benefits],
        verbose=True
    )
    
    return crew