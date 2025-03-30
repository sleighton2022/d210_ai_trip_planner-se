import os
from typing import List, Tuple, Dict, Union
from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool, ScrapeWebsiteTool, WebsiteSearchTool
from langchain_core.agents import AgentFinish

import dotenv
from dotenv import load_dotenv, find_dotenv

from rt_ai_trip_planner.model import Itinerary, ActivityContainer, Restaurant, WeatherDetails
from rt_ai_trip_planner.tools.activity_pd_search_tool import ActivityDataFrameSearchTool
from rt_ai_trip_planner.tools.weather_tool import WeatherOpenMeteoSearchTool


@CrewBase
class RtAiTripPlanner():
	"""The RtAiTripPlanner crew class."""

	# Define the configuration files.
	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	dotenv_path = find_dotenv(usecwd=True)
	load_dotenv(dotenv_path=dotenv_path)

	# Customize LLM with a temperature of 0 to ensure deterministic outputs.
	llm = LLM(
		model=os.getenv('OPENAI_MODEL_NAME'),
    	temperature=0
	)


	# Experiment: Use crewai csv-related knowledge-source and search-tool.
	# hotspots_source = CSVKnowledgeSource(file_paths=["./data/MVP_Data.csv"])
	# hotspots_csv_search_tool = CSVSearchTool(csv='./data/MVP_Data.csv')

	# Define the agents' tools.
	web_search_tool = WebsiteSearchTool()
	seper_dev_tool = SerperDevTool()
	scrape_website_tool = ScrapeWebsiteTool()
	weather_open_meteo_search_tool = WeatherOpenMeteoSearchTool()
	activity_df_search_tool = ActivityDataFrameSearchTool()
	

	def __init__(self, run_find_activity_task=True, run_find_nearby_restaurant_task=True, run_find_weather_forecast_task=True, run_plan_activity_task=True):
		# Initialize the flags to control the tasks.
		self.run_find_activity_task = run_find_activity_task
		self.run_find_nearby_restaurant_task = run_find_nearby_restaurant_task
		self.run_find_weather_forecast_task = run_find_weather_forecast_task
		self.run_plan_activity_task = run_plan_activity_task

	###########################################################################
	# Define the agents.
	###########################################################################
	@agent
	def local_tour_guide(self) -> Agent:
		return Agent(
			config=self.agents_config['local_tour_guide'],
			# tools=[self.activity_df_search_tool, self.web_search_tool, self.seper_dev_tool],
			tools = [self.activity_df_search_tool],
			max_iter=2, # avoid too many back-and-forth.
			verbose=True,
			allow_delegation=False,
			llm=self.llm,
			# knowledge_sources=[self.hotspots_source],
			# callback=log_step,
			# step_callback=lambda step: self.step_callback(step, "Local Tour Agent"),
		)

	@agent
	def restaurant_scout(self) -> Agent:
		return Agent(
			config=self.agents_config['restaurant_scout'],
			tools=[self.seper_dev_tool, self.scrape_website_tool],
			verbose=True,
			allow_delegation=False,
			llm=self.llm,
		)

	@agent
	def meteorology_agent(self) -> Agent:	
		return Agent(
			config=self.agents_config['meteorology_agent'],
			tools=[self.weather_open_meteo_search_tool],
			max_iter=2, # avoid too many back-and-forth.
			verbose=True,
			allow_delegation=False,
			llm=self.llm,
			# step_callback=lambda step: self.step_callback(step, "Meteorology Agent"),
		)	
	
	@agent
	def route_optimizer_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['route_optimizer_agent'],
			# tools=[self.seper_dev_tool, self.scrape_website_tool],
			# max_iter=2, # avoid too many back-and-forth.
			verbose=True,
			allow_delegation=False,
			llm=self.llm,
			# step_callback=lambda step: self.step_callback(step, "Route Optimizer Agent"),
		)
	
	###########################################################################
	# Define the tasks.
	###########################################################################

	# Declare task instances that need to be referenced in other task.
	# keep: Utilize internet search tools and recommendation engines to gather the information.
	find_activity_task_instance = None
	find_weather_forecast_task_instance = None
	find_nearby_restaurant_task_instance = None

	@task
	def find_activity_task(self) -> Task:
		self.find_activity_task_instance = Task(
			config=self.tasks_config['find_activity_task'],
			agent=self.local_tour_guide(),
			verbose=True,
			output_json=ActivityContainer,			
			# callback=log_step,
		)
		return self.find_activity_task_instance
	
	@task
	def find_nearby_restaurant_task(self) -> Task:
		self.find_nearby_restaurant_task_instance = Task(
			config=self.tasks_config['find_nearby_restaurant_task'],
			agent=self.restaurant_scout(),
			verbose=True,
			# async_execution=True,
			output_json=Restaurant,
		)
		return self.find_nearby_restaurant_task_instance

	@task
	def find_weather_forecast_task(self) -> Task:
		self.find_weather_forecast_task_instance = Task(
			config=self.tasks_config['find_weather_forecast_task'],
			agent=self.meteorology_agent(),
			verbose=True,
			output_json=WeatherDetails,
			# async_execution=True,
			# callback=log_step,
		)
		return self.find_weather_forecast_task_instance	
	
	@task
	def plan_activity_task(self) -> Task:
		return Task(
			config=self.tasks_config['plan_activity_task'],
			agent=self.route_optimizer_agent(),
			verbose=True,
			output_json=Itinerary,
			context=[self.find_activity_task_instance, self.find_nearby_restaurant_task_instance, self.find_weather_forecast_task_instance]
		)

	def init_tasks(self):
		"""A helper function to initialize the tasks - useful for unit testing."""
		agents = []
		tasks = []
		if self.run_find_activity_task:
			agents.append(self.local_tour_guide())
			tasks.append(self.find_activity_task())
		if self.run_find_nearby_restaurant_task:
			agents.append(self.restaurant_scout())
			tasks.append(self.find_nearby_restaurant_task())
		if self.run_find_weather_forecast_task:
			agents.append(self.meteorology_agent())
			tasks.append(self.find_weather_forecast_task())
		if self.run_plan_activity_task:
			agents.append(self.route_optimizer_agent())
			tasks.append(self.plan_activity_task())
		return agents, tasks

	@crew
	def crew(self) -> Crew:
		"""Creates the RtAiTripPlanner crew"""

		# Initialize the agents and tasks.
		crew_agents, crew_tasks = self.init_tasks()
		return Crew(
			# agents=self.agents, # Automatically created by the @agent decorator
			# tasks=self.tasks,   # Automatically created by the @task decorator
			agents=crew_agents,
			tasks=crew_tasks,
			process=Process.sequential,
			verbose=True,
			# knowledge_sources=[self.hotspots_source],
			# task_callback=log_step,
			# step_callback=log_step,
			
			output_log_file = 'output_log.txt',
			# process=Process.hierarchical,
		)
	
	def step_callback(
		self,
		agent_output: Union[str, List[Tuple[Dict, str]], AgentFinish],
		agent_name,
		*args,
	):
		print(f"[DEBUG] Agent Name: {agent_name}")
		print(f"[DEBUG] Agent Output\n{agent_output}")




##############################################################################
# !!!!! DO NOT DELETE !!!!!
# Research for callback functions.
##############################################################################
# @callback
# def log_step(task, **kwargs):
# 	# print(f"[DEBUG] task '{type(Task)}' is starting task '{task}'")
# 	# print(f"[DEBUG] Agent '{agent.role}' completed step {tas} for task '{task.description}'")
# 	# print(f"[DEBUG] Step output: {step_output}")
# 	# print(f"[DEBUG] task.thought: {task.thought}")
# 	# print(f"[DEBUG] task.output: {task.output}")
# 	# print(f"[DEBUG] task.text: {task.text}")
# 	# print(f"[DEBUG] kwargs: {kwargs}")
# 	print("-" * 50)	


# @callback
# def log_step(task: Task, output: str):
#     """Log task completion details for monitoring."""
#     print(f"Task '{task.description}' completed")
#     print(f"Output length: {len(output)} characters")
#     print(f"Agent used: {task.agent.role}")
#     print("-" * 50)	
