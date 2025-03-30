# Reference: Inspired by https://github.com/tylerprogramming/ai/blob/main/crewai_tools_11/csv_file_rag_search.py

# Must precede any llm module imports
# from langtrace_python_sdk import langtrace
# langtrace.init(api_key = '991ac5f7cd887e2a2c74f851962e37dc8b64cd8276d1de94114318c5689f8ae9')

from crewai_tools import CSVSearchTool
from crewai import Agent, Task, Crew, Process, LLM
from dotenv import load_dotenv

load_dotenv()

tool = CSVSearchTool(
    description = "This tool searches a CVS file for weather data that match the location and date",
    csv='../../../data/hourly-weather.csv',
    llm=dict(
        config=dict(
            # model="llama2",
            temperature=0,
            top_p=20,
            max_tokens=5000,
            # stream=true,
            
        ),
    ),    
)

agent = Agent(
    role="CSV Search Agent",
    goal="You will search the CSV file for the answer to the question.  Use the tools to search the CSV file.",
    backstory="""You are a master at searching CSV files.""",
    tools=[tool],
    verbose=True,
    allow_delegation=False,
)

task = Task(
    description="Answer the following questions about the CSV file: {question}",
    expected_output="An answer to the question.",
    tools=[tool],
    agent=agent,
)


meteorology_agent = Agent(
    role="Weather Information Analyst",
    goal="Provide accurate and detailed weather information by searching the CSV file for the answer to the question.  Use the tools to search the CSV file.",
    backstory="""You are a master at searching CSV files. You are also an expert weather analyst with years of experience in 
    meteorology. Your job is to provide accurate weather information and interpret weather data for users in a clear and concise manner.""",    
    tools=[tool],
    verbose=True,
    allow_delegation=False,
)

meteorology_task = Task(
    description="Answer the following weather-related questions using only the CSV file: {question}",
    expected_output="An answer to the question.",
    tools=[tool],
    agent=meteorology_agent,
)

crew = Crew(
    agents=[meteorology_agent],
    tasks=[meteorology_task],
    verbose=True,
    process=Process.sequential,
)

while True:
    question = input("Enter a question about the CSV file: ")
    result = crew.kickoff(inputs={"question": question})
    print(result)

