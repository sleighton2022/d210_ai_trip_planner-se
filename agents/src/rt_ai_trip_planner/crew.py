from datetime import datetime
import json
import os
import time
from typing import List, Tuple, Dict, Union
from crewai import LLM, Agent, Crew, Process, Task
from crewai.tasks import TaskOutput
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool, ScrapeWebsiteTool, WebsiteSearchTool
# from langchain_core.agents import AgentFinish

from .model import ActivityToRestaurantAssocsContainer, Itinerary, RecommendedActivitiesContainer, RoutePlanningInput, WeatherForecastsContainer
from .tools.attractions_search_tool import AttractionsSearchTool
from .tools.weather_tool import WeatherOpenMeteoSearchTool
from .tools.route_planning_input_generator_tool import RoutePlanningInputGeneratorTool
from .tools.route_planning_input_generator_with_container_tool import RoutePlanningInputGeneratorWithContainerTool
from .tools.route_planning_input_loader_tool import RoutePlanningInputLoaderTool
from .tools.mocked_weather_tool import MockedWeatherSearchTool
from .tools.restaurants_search_tool import NearbyRestaurantsSearchTool

from crewai.agents.parser import AgentFinish
from crewai.agents.crew_agent_executor import ToolResult

from .utils.guardrails_utils import GuardrailsUtils

# Uncomment the following line to enable logging from crewai.
# import rt_ai_trip_planner.utils.app_logging


@CrewBase
class RtAiTripPlanner():
	"""The RtAiTripPlanner crew class."""

	# Define the configuration files.
	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	# Customize LLM with a temperature of 0 to ensure deterministic outputs.
	llm = LLM(
		model=os.getenv('OPENAI_MODEL_NAME'),
    	temperature=0.1
	)

	# Experiment: Use crewai csv-related knowledge-source and search-tool.
	# hotspots_source = CSVKnowledgeSource(file_paths=["./data/MVP_Data.csv"])
	# hotspots_csv_search_tool = CSVSearchTool(csv='./data/MVP_Data.csv')

	# Define the agents' tools.
	web_search_tool = WebsiteSearchTool()
	seper_dev_tool = SerperDevTool()
	scrape_website_tool = ScrapeWebsiteTool()
	weather_open_meteo_search_tool = WeatherOpenMeteoSearchTool(result_as_answer=True)
	attractions_search_tool = AttractionsSearchTool(result_as_answer=True)
	route_planning_input_generator_tool = RoutePlanningInputGeneratorTool(result_as_answer=True)
	route_planning_input_generator_with_container_tool = RoutePlanningInputGeneratorWithContainerTool(result_as_answer=True)
	route_planning_input_loader_tool = RoutePlanningInputLoaderTool(result_as_answer=True)
	mocked_weather_search_tool = MockedWeatherSearchTool()
	nearby_restaurants_search_tool = NearbyRestaurantsSearchTool()

	# Define the log file name for task completion.
	TASK_COMPLETE_LOG_FILE = "task_complete_logs.txt"
	

	def __init__(self,                                                                                                                                     
			  run_find_weather_forecast_task=True, run_find_activity_task=True, run_find_nearby_restaurant_task=True,
			  run_generate_route_planning_input_task=True, run_prepare_route_planning_input_task=False,
			  run_plan_activity_task=True):
		# Initialize the flags to control the tasks.
		print(f"\n\nCrew RtAiTripPlanner initialized with the following tasks:")
		print(f"  - run_find_activity_task: {run_find_activity_task}")
		print(f"  - run_find_nearby_restaurant_task: {run_find_nearby_restaurant_task}")
		print(f"  - run_find_weather_forecast_task: {run_find_weather_forecast_task}")
		print(f"  - run_generate_report_task: {run_generate_route_planning_input_task}")
		print(f"  - run_prepare_route_planning_input_task: {run_prepare_route_planning_input_task}")
		print(f"  - run_plan_activity_task: {run_plan_activity_task}")

		# Initialize the start time.
		current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")		
		self.start_time = time.time()
		with open(self.TASK_COMPLETE_LOG_FILE, "a") as log_file:
			print(f"\n\nCrew RtAiTripPlanner started at: {current_time}, start_time: {self.start_time}", file=log_file)

		self.run_find_activity_task = run_find_activity_task
		self.run_find_nearby_restaurant_task = run_find_nearby_restaurant_task
		self.run_find_weather_forecast_task = run_find_weather_forecast_task
		self.run_generate_report_task = run_generate_route_planning_input_task
		self.run_prepare_route_planning_input_task = run_prepare_route_planning_input_task
		self.run_plan_activity_task = run_plan_activity_task
		

	###########################################################################
	# Define the agents.
	###########################################################################
	local_tour_guide_instance = None
	restaurant_scout_instance = None
	meteorology_agent_instance = None
	route_optimizer_agent_instance = None
	route_planning_input_generator_agent_instance = None
	route_planning_input_agent_instance = None


	@agent
	def meteorology_agent(self) -> Agent:	
		if self.meteorology_agent_instance is not None: return self.meteorology_agent_instance
		self.meteorology_agent_instance = Agent(
			config=self.agents_config['meteorology_agent'],
			tools=[self.weather_open_meteo_search_tool],
			# tools=[self.mocked_weather_search_tool],
			max_iter=2, # avoid too many back-and-forth.
			verbose=True,
			allow_delegation=False,
			llm=self.llm,
			# step_callback=lambda step: self.step_callback(step, "Meteorology Agent"),
		)
		return self.meteorology_agent_instance

	@agent
	def local_tour_guide(self) -> Agent:
		if self.local_tour_guide_instance is not None: return self.local_tour_guide_instance
		self.local_tour_guide_instance = Agent(
			config=self.agents_config['local_tour_guide'],
			# tools=[self.activity_df_search_tool, self.web_search_tool, self.seper_dev_tool],
			# tools = [self.activity_df_search_tool],
			tools = [self.attractions_search_tool],
			max_iter=2, # avoid too many back-and-forth.
			verbose=True,
			allow_delegation=False,
			llm=None, #self.llm,
			# knowledge_sources=[self.hotspots_source],
			# callback=log_step,
			# step_callback=lambda step: self.step_callback(step, "Local Tour Agent"),
		)
		return self.local_tour_guide_instance

	@agent
	def restaurant_scout(self) -> Agent:
		if self.restaurant_scout_instance is not None: return self.restaurant_scout_instance
		self.restaurant_scout_instance = Agent(
			config=self.agents_config['restaurant_scout'],
			# tools=[self.seper_dev_tool, self.scrape_website_tool],
			# tools=[self.seper_dev_tool],
			tools=[self.nearby_restaurants_search_tool],
			verbose=True,
			allow_delegation=False,
			llm=self.llm,
		)
		return self.restaurant_scout_instance
	
	@agent
	def route_optimizer_agent(self) -> Agent:
		if self.route_optimizer_agent_instance is not None: return self.route_optimizer_agent_instance
		self.route_optimizer_agent_instance = Agent(
			config=self.agents_config['route_optimizer_agent'],
			# tools=[self.nearby_restaurants_search_tool, self.seper_dev_tool],
			# tools=[self.seper_dev_tool],
			# max_iter=2, # avoid too many back-and-forth.
			verbose=True,
			allow_delegation=False,
			llm=self.llm,
			# step_callback=lambda step: self.step_callback(step, "Route Optimizer Agent"),
			# step_callback=lambda step: self.print_agent_output(step, "Route Optimizer Agent"),
		)
		return self.route_optimizer_agent_instance
	
	@agent
	def route_planning_input_generator_agent(self) -> Agent:
		if self.route_planning_input_generator_agent_instance is not None: return self.route_planning_input_generator_agent_instance
		self.route_planning_input_generator_agent_instance = Agent(
			config=self.agents_config['route_planning_input_generator_agent'],
			# tools=[self.route_planning_input_generator_tool],			
			tools=[self.route_planning_input_generator_with_container_tool],
			verbose=True,
			allow_delegation=False,
			llm=self.llm,
			function_calling_llm=self.llm,
			max_execution_time=5,
			max_iter=2, # avoid too many back-and-forth.
			# step_callback=lambda step: self.print_agent_output(step, "Report Generator Agent"),
		)
		return self.route_planning_input_generator_agent_instance
	
	@agent
	def route_planning_input_loader_agent(self) -> Agent:
		if self.route_planning_input_agent_instance is not None: return self.route_planning_input_agent_instance
		self.route_planning_input_agent_instance = Agent(
			config=self.agents_config['route_planning_input_loader_agent'],
			tools=[self.route_planning_input_loader_tool],
			# max_iter=2, # avoid too many back-and-forth.
			verbose=True,
			allow_delegation=False,
			llm=self.llm,
			# step_callback=lambda step: self.step_callback(step, "Route Planning Input Agent"),
		)
		return self.route_planning_input_agent_instance

	
	###########################################################################
	# Define the tasks.
	###########################################################################

	# Declare task instances that need to be referenced in other task.
	# keep: Utilize internet search tools and recommendation engines to gather the information.
	find_activity_task_instance = None
	find_weather_forecast_task_instance = None
	find_nearby_restaurant_task_instance = None
	generate_route_planning_input_task_instance = None
	load_route_planning_input_task_instance = None
	plan_activity_task_instance = None


	@task
	def find_weather_forecast_task(self) -> Task:
		if self.find_weather_forecast_task_instance is not None: return self.find_weather_forecast_task_instance
		self.find_weather_forecast_task_instance = Task(
			config=self.tasks_config['find_weather_forecast_task'],
			agent=self.meteorology_agent(),
			verbose=True,
			output_json=WeatherForecastsContainer,
			async_execution=True,
			callback=self.on_task_complete,
		)
		return self.find_weather_forecast_task_instance

	@task
	def find_activity_task(self) -> Task:
		if self.find_activity_task_instance is not None: return self.find_activity_task_instance
		self.find_activity_task_instance = Task(
			config=self.tasks_config['find_activity_task'],
			agent=self.local_tour_guide(),
			verbose=True,
			guardrail=GuardrailsUtils.validate_activities,
			output_json=RecommendedActivitiesContainer,
			callback=self.on_task_complete,
		)
		return self.find_activity_task_instance
	
	@task
	def find_nearby_restaurant_task(self) -> Task:
		if self.find_nearby_restaurant_task_instance is not None: return self.find_nearby_restaurant_task_instance
		self.find_nearby_restaurant_task_instance = Task(
			config=self.tasks_config['find_nearby_restaurant_task'],
			agent=self.restaurant_scout(),
			verbose=True,			
			output_json=ActivityToRestaurantAssocsContainer,
			async_execution=True,
			callback=self.on_task_complete,
			context=[self.find_activity_task_instance]
		)
		return self.find_nearby_restaurant_task_instance
	
	@task
	def generate_route_planning_input_task(self) -> Task:
		if self.generate_route_planning_input_task_instance is not None: return self.generate_route_planning_input_task_instance
		self.generate_route_planning_input_task_instance = Task(
			config=self.tasks_config['generate_route_planning_input_task'],
			agent=self.route_planning_input_generator_agent(),
			verbose=True,
			max_retries=0,
			output_json=RoutePlanningInput,
			callback=self.on_task_complete,
			context=[self.find_weather_forecast_task_instance, self.find_activity_task_instance, self.find_nearby_restaurant_task_instance]
		)
		return self.generate_route_planning_input_task_instance
	
	@task
	def load_route_planning_input_task(self) -> Task:
		if self.load_route_planning_input_task_instance is not None: return self.load_route_planning_input_task_instance
		self.load_route_planning_input_task_instance = Task(
			config=self.tasks_config['load_route_planning_input_task'],
			agent=self.route_planning_input_loader_agent(),
			verbose=True,
			output_json=RoutePlanningInput,
			callback=self.on_task_complete,
		)
		return self.load_route_planning_input_task_instance

	@task
	def plan_activity_task(self) -> Task:
		if self.plan_activity_task_instance is not None: return self.plan_activity_task_instance

		# Set context based on if the run_prepare_route_planning_input_task is running or not.
		plan_activity_task_context = []
		if self.run_prepare_route_planning_input_task:
			plan_activity_task_context = [self.load_route_planning_input_task_instance]
		else:
			# plan_activity_task_context = [self.find_weather_forecast_task_instance, self.find_activity_task_instance, self.find_nearby_restaurant_task_instance]
			plan_activity_task_context = [self.load_route_planning_input_task_instance]

		self.plan_activity_task_instance = Task(
			config=self.tasks_config['plan_activity_task'],
			agent=self.route_optimizer_agent(),
			verbose=True,
			output_json=Itinerary,
			callback=self.on_task_complete,
			guardrail=GuardrailsUtils.validate_itinerary,
			context=plan_activity_task_context,
			# context=[self.find_activity_task_instance, self.find_nearby_restaurant_task_instance, self.find_weather_forecast_task_instance]
			# context=[self.find_activity_task_instance, self.find_weather_forecast_task_instance]
			# context=[self.prepare_route_planning_input_task_instance]
		)
		return self.plan_activity_task_instance


	def init_tasks(self):
		"""A helper function to initialize the tasks - useful for unit testing."""
		agents = []
		tasks = []
		if self.run_find_weather_forecast_task:
			agents.append(self.meteorology_agent())
			tasks.append(self.find_weather_forecast_task())		
		if self.run_find_activity_task:
			agents.append(self.local_tour_guide())
			tasks.append(self.find_activity_task())
		if self.run_find_nearby_restaurant_task:
			agents.append(self.restaurant_scout())
			tasks.append(self.find_nearby_restaurant_task())
		if self.run_generate_report_task:
			agents.append(self.route_planning_input_generator_agent())
			tasks.append(self.generate_route_planning_input_task())
		if self.run_prepare_route_planning_input_task:
			agents.append(self.route_planning_input_loader_agent())
			tasks.append(self.prepare_route_planning_input_task())
		if self.run_plan_activity_task:
			agents.append(self.route_optimizer_agent())
			tasks.append(self.plan_activity_task())
		return agents, tasks

	@crew
	def crew(self) -> Crew:
		"""Creates the RtAiTripPlanner crew"""

		# Initialize the agents and tasks.
		crew_agents, crew_tasks = self.init_tasks()
		
		# crew_agents = self.agents # Automatically created by the @agent decorator			
		# crew_tasks = self.tasks # Automatically created by the @task decorator
		
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

	def on_task_complete(self, task_output: TaskOutput):
		"""Callback function to log the task completion."""
		# Current time.
		current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		
		# This apprach does not work if there is any async task.
		new_start_time = time.time()
		elapsed_time = new_start_time - self.start_time
		self.start_time = new_start_time
		
		with open(self.TASK_COMPLETE_LOG_FILE, "a") as log_file:
			print(f"Elapse Time: {(elapsed_time/60):.4f} min for Task: '{task_output.name}", file=log_file)
			print(f"Task completed at: {current_time}...Task Summary: '{task_output.summary}", file=log_file)			
			# print(f"Task Summary: '{task_result.summary}'", file=log_file)
			print(f"Agent used: {task_output.agent}", file=log_file)			
			print(f"Output length: {len(task_output.raw)} characters", file=log_file)
			print(f"Pydantic: {task_output.pydantic}", file=log_file)
			print(f"Json Dict: {task_output.json_dict}", file=log_file)
			print(f"Result (raw): '{task_output.raw}'", file=log_file)
			print("-" * 50, file=log_file)
	
	def step_callback(
		self,
		agent_output: Union[str, List[Tuple[Dict, str]], AgentFinish],
		agent_name,
		*args,
	):
		print(f"[DEBUG] Agent Name: {agent_name}")
		print(f"[DEBUG] Agent Output\n{agent_output}")

	call_number = 0
	agent_finishes  = []

	def print_agent_output(
			self, 
			agent_output: Union[str, List[Tuple[Dict, str]], AgentFinish], 
			agent_name: str,
			*args,
		):
		
		self.call_number  # Declare call_number as a global variable
		self.call_number += 1
		with open("crew_callback_logs.txt", "a") as log_file:
			# Try to parse the output if it is a JSON string
			if isinstance(agent_output, str):
				try:
					agent_output = json.loads(agent_output)  # Attempt to parse the JSON string
				except json.JSONDecodeError:
					pass  # If there's an error, leave agent_output as is

			# Check if the output is a list of tuples as in the first case
			if isinstance(agent_output, list) and all(isinstance(item, tuple) for item in agent_output):
				print(f"-{self.call_number}----Dict------------------------------------------", file=log_file)
				for action, description in agent_output:
					# Print attributes based on assumed structure
					print(f"Agent Name: {agent_name}", file=log_file)
					print(f"Tool used: {getattr(action, 'tool', 'Unknown')}", file=log_file)
					print(f"Tool input: {getattr(action, 'tool_input', 'Unknown')}", file=log_file)
					print(f"Action log: {getattr(action, 'log', 'Unknown')}", file=log_file)
					print(f"Description: {description}", file=log_file)
					print("--------------------------------------------------", file=log_file)

			# Check if the output is a dictionary as in the second case
			elif isinstance(agent_output, AgentFinish):
				print(f"-{self.call_number}----AgentFinish---------------------------------------", file=log_file)
				print(f"Agent Name: {agent_name}", file=log_file)
				self.agent_finishes.append(agent_output)
				# Extracting 'output' and 'log' from the nested 'return_values' if they exist

				# output = agent_output.return_values
				output = agent_output.text
				print(f"AgentFinish Output: {output}", file=log_file)

				# log = agent_output.get('log', 'No log available')
				# print(f"AgentFinish Output: {output['output']}", file=log_file)
				# print(f"Log: {log}", file=log_file)
				# print(f"AgentFinish: {agent_output}", file=log_file)
				print("--------------------------------------------------", file=log_file)

			# Handle unexpected formats
			else:
				# If the format is unknown, print out the input directly
				print(f"-{self.call_number}-Unknown format of agent_output:", file=log_file)

				print(f"Type of agent_output: {type(agent_output)}", file=log_file)
				print(f"Class Name: {agent_output.__class__.__name__}", file=log_file)
				print(agent_output, file=log_file)

				print(f"checking if agent_output is an instance of AgentFinish: {isinstance(agent_output, AgentFinish)}", file=log_file)
				if isinstance(agent_output, AgentFinish):
					print(agent_output.text, file=log_file)
				
				print(f"checking if agent_output is an instance of ToolResult: {isinstance(agent_output, ToolResult)}", file=log_file)
				if isinstance(agent_output, ToolResult):
					print(agent_output.result, file=log_file)








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
