from knowledge_base import KnowledgeBase
from ollama_interface import OllamaInterface
from omniscient_data_absorber import OmniscientDataAbsorber
from actions import Actions
from tutorial_manager import TutorialManager
from nimbus_server import start_server, update_ui  # Import the server functions
from nimbus_guide import NimbusGuide
from environment_manager import EnvironmentManager
import asyncio
import logging
import time
import os
import subprocess
import random
import json

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

class Nimbus:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.project_dir = os.path.join(os.getcwd(), "nimbus_projects")
        os.makedirs(self.project_dir, exist_ok=True)
        self.env_manager = EnvironmentManager(self.project_dir)
        self.knowledge_base = KnowledgeBase()
        self.ollama_interface = OllamaInterface(knowledge_base=self.knowledge_base)
        self.actions = Actions(self.ollama_interface, self.env_manager)
        self.data_absorber = OmniscientDataAbsorber(self.knowledge_base, self.ollama_interface, self.env_manager)
        self.logger = setup_logger("Nimbus")
        self.memory_file = 'nimbus_memory.pkl'
        self.save_interval = 150  # Save every 5 minutes
        self.state = "welcome"  # Initial state
        self.last_save_time = time.time()  # Track the last save time
        self.current_project = None
        self.current_project_files = []  # Track files in the current project
        self.help_topics = self.load_help_topics()
        self.tutorial_manager = TutorialManager()
        self.server_started = False  # Flag to track if the server has been started
        self.guide = NimbusGuide(self.ollama_interface)
        self.active_menu = 'main'  # Track the active menu
        self.project_stages = ['planning', 'implementation', 'testing', 'review']
        self.current_stage = None

    async def start(self):
        """
        Start the Nimbus operation cycle.
        """
        if not self.server_started:
            start_server()  # Start the web server
            self.server_started = True
        await self.initialize_system()
        while True:
            await self.main_loop()
            await asyncio.sleep(1)

    async def initialize_system(self):
        """
        Initialize the system with necessary setups and checks.
        """
        self.logger.info("Welcome to Nimbus, your autonomous software assistant!")
        self.logger.info("Initializing Nimbus System...")
        update_ui({"status": "Initializing Nimbus System"})  # Update UI
        if self.knowledge_base.load_memory_state(self.memory_file):
            self.logger.info("Loaded existing memory state.")
            update_ui({"status": "Loaded existing memory state"})  # Update UI
        else:
            self.logger.info("No existing memory state found. Setting up new environment.")
            update_ui({"status": "Setting up new environment"})  # Update UI
            await self.knowledge_base.setup_new_environment()
            await self.data_absorber.absorb_knowledge()
            await self.data_absorber.initialize_consciousness()
        self.logger.info("System initialized.")
        update_ui({"status": "System initialized"})  # Update UI
        await self.update_context()  # Update context after initialization

    async def update_context(self):
        """
        Update the context dynamically based on real-time data and Nimbus interactions.
        """
        self.context = await self.gather_context()
        self.logger.info(f"Updated context: {self.context}")

    async def main_loop(self):
        """
        Main loop where Nimbus autonomously decides on actions.
        """
        while True:
            structured_context = await self.gather_structured_context()
            decision = await self.make_decision(structured_context)
            
            action = decision['action']
            self.logger.info(f"Decided action: {action['name']}")
            update_ui({"action": action['name']})  # Update UI with the decided action
            
            if action['name'] in ['continue_project', 'start_new_project']:
                await self.execute_action(action['name'])
                if self.current_project:
                    await self.project_loop()
            else:
                await self.execute_action(action['name'])
            
            await self.check_and_save_memory()
            await asyncio.sleep(1)

    async def project_loop(self):
        """
        Project loop where Nimbus performs actions within the project.
        """
        self.logger.info(f"Entering project loop for: {self.current_project['name']}")
        update_ui({"status": f"Working on project: {self.current_project['name']}"})
        
        self.active_menu = 'dev'
        update_ui({"active_menu": "dev"})

        project_stages = ['planning', 'implementation', 'testing', 'review']
        current_stage = 'planning'

        while self.current_project:
            structured_context = await self.gather_structured_context()
            decision = await self.make_decision(structured_context, current_stage)
            
            action = decision['action']
            self.logger.info(f"Project action: {action['name']}")
            update_ui({"project_action": action['name']})

            if action['name'] == 'exit_project':
                await self.execute_exit_project()
                break
            elif action['name'] in ['start_new_project', 'continue_project']:
                self.logger.warning("Already in a project. Ignoring start_new_project or continue_project action.")
                update_ui({"warning": "Already in a project. Continuing current project."})
                continue
            
            result = await self.execute_project_action(action)
            
            # Update project stage based on action results
            current_stage = self.update_project_stage(current_stage, action['name'], result, project_stages)
            
            if current_stage == 'review' and self.is_project_complete():
                self.logger.info("Project completed. Exiting project loop.")
                update_ui({"status": "Project completed. Exiting project."})
                await self.execute_exit_project()
                break

            await asyncio.sleep(1)

        self.logger.info("Project loop ended. Returning to main loop.")
        update_ui({"status": "Project completed. Returning to main menu."})

    async def execute_project_action(self, action):
        """
        Execute a project-specific action.
        """
        self.logger.info(f"Executing project action: {action['name']}")
        update_ui({"executing_project_action": action['name']})
        
        try:
            if not self.is_action_valid(action['name']):
                self.logger.warning(f"Action {action['name']} is not valid in the current project state.")
                update_ui({"warning": f"Action {action['name']} is not valid in the current project state."})
                return

            method_name = f"execute_{action['name']}"
            if hasattr(self, method_name):
                result = await getattr(self, method_name)(action['details'])
            else:
                self.logger.warning(f"No specific method found for project action {action['name']}. Executing generic action.")
                result = await self.actions.execute_action(action)
            
                self.logger.warning(f"No specific method found for project action {action}. Executing generic action.")
                action_details = self.get_action_details(action)
                await self.actions.execute_action({"name": action, **action_details})
        except Exception as e:
            self.logger.error(f"Error executing project action {action}: {e}")
        
        feedback = await self.collect_feedback()
        await self.learn_from_feedback(feedback)
        update_ui({"project_action_completed": action})

    def is_action_valid(self, action_name):
        """
        Check if the action is valid for the current project state.
        """
        if not self.current_project:
            return action_name in ['start_new_project', 'continue_project']

        if not self.current_project_files:
            return action_name in ['create_file', 'generate_code', 'exit_project']

        if action_name in ['run_code', 'write_tests', 'analyze_code']:
            return any(file.endswith('.py') for file in self.current_project_files)

        return True

    async def save_project(self):
        """
        Save the current project state.
        """
        if self.current_project:
            self.logger.info(f"Saving project: {self.current_project['name']}")
            update_ui({"status": f"Saving project: {self.current_project['name']}"})
            # Implement project saving logic here
            self.knowledge_base.set_project_state("saved")
            self.logger.info("Project saved successfully.")
            update_ui({"status": "Project saved successfully"})

    async def execute_exit_project(self):
        """
        Exit the current project.
        """
        await self.save_project()
        self.current_project = None
        self.current_project_files = []
        self.knowledge_base.set_project_state("idle")
        self.active_menu = 'main'
        self.logger.info("Exited project.")
        update_ui({"status": "Exited project", "active_menu": "main"})

    async def make_decision(self, structured_context):
        """
        Use the Consciousness Emulator and NimbusGuide to decide the next action.
        """
        guidance = await self.guide.provide_guidance(structured_context)
        self.logger.info(f"Guidance received: {guidance}")
        
        structured_context['guide_suggestions'] = guidance
        
        if self.current_stage == 'planning':
            preferred_actions = ['research_and_plan', 'create_file']
        elif self.current_stage == 'implementation':
            preferred_actions = ['implement_initial_prototype', 'generate_code', 'edit_file']
        elif self.current_stage == 'testing':
            preferred_actions = ['write_tests', 'run_code', 'analyze_code']
        elif self.current_stage == 'review':
            preferred_actions = ['analyze_code', 'project_retrospective']
        else:
            preferred_actions = []

        available_actions = structured_context['available_actions']
        filtered_actions = [action for action in available_actions if action['name'] in preferred_actions]
        
        if filtered_actions:
            decision = {'action': random.choice(filtered_actions)}
        else:
            decision = await self.data_absorber.consciousness_emulator.emulate_consciousness(structured_context)
        
        return decision

    async def update_project_stage(self, action_result):
        if self.current_stage == 'planning' and action_result.get('status') == 'success':
            if action_result.get('file') == 'research_and_plan.md':
                self.current_stage = 'implementation'
        elif self.current_stage == 'implementation' and action_result.get('status') == 'success':
            if action_result.get('file') == 'main.py':
                self.current_stage = 'testing'
        elif self.current_stage == 'testing' and action_result.get('status') == 'success':
            if 'test_' in action_result.get('file_name', ''):
                self.current_stage = 'review'
        update_ui({"project_stage": self.current_stage})

    def is_project_complete(self):
        return self.current_stage == 'review' and all([
            self.env_manager.file_exists(self.current_project['name'], 'README.md'),
            self.env_manager.file_exists(self.current_project['name'], 'main.py'),
            any(file.startswith('test_') for file in self.env_manager.list_files(self.current_project['name']))
        ])

    async def execute_action(self, action_name):
        self.logger.info(f"Executing action: {action_name}")
        update_ui({"executing_action": action_name})
        
        try:
            method_name = f"execute_{action_name}"
            if hasattr(self, method_name):
                result = await getattr(self, method_name)()
            else:
                self.logger.warning(f"No specific method found for action {action_name}. Executing generic action.")
                result = await self.actions.execute_action({"name": action_name})
            
            # Update project state based on action result
            await self.update_project_state(action_name, result)
            
            # Collect context for progress tracking
            context = self.collect_action_context(action_name, result)
            
            # Update the guide with the executed action, its result, and context
            await self.guide.update_progress(action_name, result, context)
            
            feedback = await self.collect_feedback()
            await self.learn_from_feedback(feedback)
            update_ui({"action_completed": action_name})
        except Exception as e:
            self.logger.error(f"Error executing action {action_name}: {e}")
            # Update progress with error information
            await self.guide.update_progress(action_name, {"error": str(e)}, {"errors_encountered": [str(e)]})

    def collect_action_context(self, action_name, result):
        """
        Collect context information for the executed action.
        """
        context = {
            "current_project": self.current_project,
            "project_state": self.knowledge_base.get_project_state(),
            "files_affected": [],  # You'd need to implement logic to track affected files
            "code_changes": {},    # You'd need to implement logic to track code changes
            "performance_metrics": self.get_performance_metrics(),
            "errors_encountered": []
        }
        
        # Add action-specific context
        if action_name == "write_tests":
            context["tests_written"] = result.get("tests_written", 0)
        elif action_name == "commit_changes":
            context["commit_made"] = True
        
        return context

    async def get_performance_metrics(self):
        """
        Get current performance metrics asynchronously.
        """
        # Implement logic to gather performance metrics
        return {
            "memory_usage": 0,  # Placeholder
            "cpu_usage": 0,     # Placeholder
            "execution_time": 0 # Placeholder
        }

    async def update_project_state(self, action_name, result):
        current_state = self.knowledge_base.get_project_state()
        if action_name in ['start_new_project', 'continue_project']:
            self.knowledge_base.set_project_state("in_progress")
        elif action_name == 'review_project':
            self.knowledge_base.set_project_state("review")
        elif action_name == 'project_retrospective':
            self.knowledge_base.set_project_state("completed")
        # Add more state transitions based on actions and their results

    async def execute_analyze_project_state(self):
        """
        Analyze the current project state and suggest next steps.
        """
        project_state = self.knowledge_base.get_project_state()
        project_files = self.current_project_files
        recent_actions = self.actions.context.get('recent_actions', [])
        
        analysis = await self.ollama_interface.analyze_project_state(project_state, project_files, recent_actions)
        self.logger.info(f"Project state analysis: {analysis}")
        update_ui({"project_analysis": analysis})
        
        return analysis

    async def execute_start_new_project(self):
        await self.start_new_project()

    async def execute_continue_project(self):
        """
        Continue working on a project or prompt for project selection if none is selected.
        """
        if not self.current_project:
            project_selected = await self.select_project_to_continue()
            if not project_selected:
                self.logger.warning("No project selected to continue. Consider starting a new project.")
                update_ui({"warning": "No project selected to continue. Consider starting a new project."})
                return

        project_name = self.current_project['name']
        project_state = self.knowledge_base.get_project_state()
        
        if project_state != "in_progress" and project_state != "saved":
            self.logger.warning(f"Invalid project state: {project_state} for project {project_name}. Starting a new project.")
            update_ui({"warning": f"Invalid project state: {project_state} for project {project_name}. Starting a new project."})
            await self.reset_project_state()
            await self.start_new_project()
        else:
            try:
                self.current_project_files = self.env_manager.list_files(project_name)
                if not self.current_project_files:
                    raise FileNotFoundError(f"No project files found for {project_name}.")
                
                self.logger.info(f"Continuing project: {project_name}")
                update_ui({"status": f"Continuing project: {project_name}"})
                
                if not self.check_project_environment():
                    raise EnvironmentError(f"Project environment for {project_name} is not properly set up.")
                
                self.knowledge_base.set_project_state("in_progress")
                await self.project_loop()
            except (FileNotFoundError, EnvironmentError) as e:
                self.logger.error(f"Error continuing project {project_name}: {str(e)}")
                update_ui({"error": f"Error continuing project {project_name}: {str(e)}"})
                await self.reset_project_state()
                await self.start_new_project()

    async def select_project_to_continue(self) -> bool:
        """
        Prompt for project selection from existing projects.
        
        Returns:
            bool: True if a project was selected, False otherwise.
        """
        existing_projects = self.env_manager.list_projects()
        if not existing_projects:
            self.logger.warning("No existing projects found.")
            update_ui({"warning": "No existing projects found."})
            return False

        self.logger.info("Selecting a project to continue...")
        update_ui({"status": "Selecting a project to continue"})

        # Here, you would typically interact with the user to select a project
        # For this example, we'll just select the first project in the list
        selected_project = existing_projects[0]
        
        project_path = self.env_manager.get_project_path(selected_project)
        self.current_project = {
            "name": selected_project,
            "path": project_path
        }
        self.logger.info(f"Selected project: {selected_project}")
        update_ui({"selected_project": selected_project})
        return True

    def check_project_environment(self):
        """
        Perform a basic check of the project environment.
        """
        if not self.current_project:
            return False
        if not self.env_manager.project_exists(self.current_project['name']):
            return False
        if not self.current_project_files:
            return False
        # Add more checks as needed
        return True

    async def reset_project_state(self):
        """
        Reset the project state and clear current project information.
        """
        self.logger.info("Resetting project state.")
        update_ui({"status": "Resetting project state"})
        self.knowledge_base.set_project_state("idle")
        self.current_project = None
        self.current_project_files = []

    async def execute_review_project(self):
        await self.review_project()

    async def execute_get_help(self):
        topic = self.data_absorber.consciousness_emulator.awareness.get('top_priorities', [{}])[0].get('topic', 'general')
        help_info = self.get_help(topic)
        self.logger.info(f"Help info: {help_info}")
        update_ui({"help_info": help_info})  # Update UI with help info

    async def execute_interactive_tutorial(self):
        await self.interactive_tutorial()

    async def execute_load_tutorial(self):
        tutorial_name = self.data_absorber.consciousness_emulator.awareness.get('top_priorities', [{}])[0].get('tutorial_name', 'default')
        tutorial_content = self.tutorial_manager.load_tutorial(tutorial_name)
        self.logger.info(f"Loaded tutorial: {tutorial_content}")
        update_ui({"tutorial": tutorial_content})  # Update UI with tutorial content

    async def check_and_save_memory(self):
        """
        Check if it's time to save the memory state and save if necessary.
        """
        current_time = time.time()
        if current_time - self.last_save_time >= self.save_interval:
            await self.save_memory_state()
            self.last_save_time = current_time

    async def start_new_project(self):
        """
        Start a new project.
        """
        self.logger.info("Starting a new project...")
        update_ui({"status": "Starting a new project"})

        # Generate project name and description using consciousness emulator
        context = await self.data_absorber.prepare_data_for_consciousness()
        project_details = await self.data_absorber.consciousness_emulator.generate_project_details(context)
        project_name = project_details.get("project_name", f"Project_{int(time.time())}")
        project_description = project_details.get("project_description", "This is a new project created by Nimbus.")

        # Create project directory
        project_path = self.env_manager.get_project_path(project_name)
        self.env_manager.create_project(project_name)

        # Save project details
        self.current_project = {
            "name": project_name,
            "description": project_description,
            "path": project_path
        }
        self.current_project_files = []  # Reset file tracking for new project

        # Create initial project structure
        await self.create_initial_project_structure(project_name, project_description)

        # Set project state
        self.knowledge_base.set_project_state("in_progress")
        self.knowledge_base.set_current_project(self.current_project)

        self.logger.info(f"Created new project: {project_name}")
        self.logger.info(f"Project description: {project_description}")
        update_ui({
            "new_project": {
                "name": project_name,
                "description": project_description,
                "path": project_path
            }
        })

        self.current_stage = 'planning'
        update_ui({"project_stage": self.current_stage})

        await self.project_loop()

    async def create_initial_project_structure(self, project_name, project_description):
        """
        Create initial project structure and files.
        """
        # Create README.md
        readme_content = f"# {project_name}\n\n{project_description}\n"
        self.env_manager.create_file(project_name, "README.md", readme_content)
        self.current_project_files.append("README.md")

        # Create src directory
        self.env_manager.create_directory(project_name, "src")

        # Create main.py
        main_content = "# Main entry point for the project\n\ndef main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()"
        self.env_manager.create_file(project_name, "src/main.py", main_content)
        self.current_project_files.append("src/main.py")

        # Create tests directory
        self.env_manager.create_directory(project_name, "tests")

        # Create requirements.txt
        self.env_manager.create_file(project_name, "requirements.txt", "# List project dependencies here\n")
        self.current_project_files.append("requirements.txt")

        self.logger.info(f"Created initial project structure for {project_name}")

    async def review_project(self):
        """
        Review the completed project.
        """
        if self.knowledge_base.get_project_state() != "in_progress":
            self.logger.warning("No project in progress. Cannot review.")
            update_ui({"warning": "No project in progress to review"})  # Update UI with warning
            return

        if self.current_project:
            self.logger.info(f"Reviewing project: {self.current_project['name']}")
            update_ui({"status": f"Reviewing project: {self.current_project['name']}"})  # Update UI
            await self.actions.project_retrospective(self.current_project)
            self.current_project = None
            self.knowledge_base.set_project_state("idle")  # Set project state
            update_ui({"status": "Project review completed"})  # Update UI
        else:
            self.logger.info("No project to review.")
            update_ui({"warning": "No project to review"})  # Update UI with warning

    async def generate_code(self, spec):
        """
        Generate code based on the given specification and save it to the project directory.
        """
        self.logger.info(f"Generating code for spec: {spec}")
        code = await self.ollama_interface.generate_code(spec)
        file_name = f"generated_code_{int(time.time())}.py"
        self.env_manager.create_file(self.current_project['name'], file_name, code)
        self.current_project_files.append(file_name)  # Track the generated file
        self.logger.info(f"Code generated and saved to {file_name}")

    async def run_code(self):
        """
        Run the generated code and capture the output.
        """
        self.logger.info("Running the generated code...")
        for file in self.current_project_files:
            if file.endswith('.py'):
                code_file = self.env_manager.get_file_path(self.current_project['name'], file)
                result = subprocess.run(["python", code_file], capture_output=True, text=True)
                output_file = f"output_{file}.log"
                self.env_manager.create_file(self.current_project['name'], output_file, result.stdout)
                self.current_project_files.append(output_file)  # Track the output file
                self.logger.info(f"Code executed. Output saved to {output_file}")

    async def write_tests(self):
        """
        Write unit tests for the generated code.
        """
        self.logger.info("Writing unit tests...")
        # Implement test writing logic here
        pass

    async def analyze_code(self):
        """
        Analyze the code and provide suggestions for improvement.
        """
        self.logger.info("Analyzing code...")
        for file in self.current_project_files:
            if file.endswith('.py'):
                code = self.env_manager.read_file(self.current_project['name'], file)
                analysis = await self.ollama_interface.analyze_code(code)
                self.logger.info(f"Code analysis for {file}: {analysis}")

    async def save_memory_state(self):
        """Asynchronously save the memory state."""
        recent_experiences = await self.knowledge_base.get_recent_experiences()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.knowledge_base.save_memory_state, recent_experiences, self.memory_file)

    async def gather_context(self):
        """
        Gather necessary context for decision making.
        """
        return await self.data_absorber.prepare_data_for_consciousness()

    async def collect_feedback(self):
        """
        Collect feedback from various components.
        """
        return await self.ollama_interface.collect_feedback()

    async def learn_from_feedback(self, feedback):
        """
        Update systems based on feedback to improve future performance.
        """
        await self.knowledge_base.learn_from_experience(feedback)
        await self.data_absorber.log_chain_of_thought("Learning from feedback", {"feedback": feedback})

    async def research_and_plan(self):
        """
        Conduct research and plan potential projects.
        """
        self.logger.info("Conducting research and planning potential projects...")
        research_prompt = "Research and suggest potential AI projects that could be implemented."
        research_results = await self.ollama_interface.query_ollama(self.ollama_interface.system_prompt, research_prompt)
        
        research_file = "research_and_plan.json"
        self.env_manager.create_file(self.current_project['name'], research_file, json.dumps(research_results, indent=2))
        
        self.current_project_files.append(research_file)  # Track the research file
        self.logger.info(f"Research and planning results saved to {research_file}")

    async def implement_initial_prototype(self):
        """
        Implement an initial prototype based on the research and planning.
        """
        self.logger.info("Implementing initial prototype...")
        research_file = "research_and_plan.json"
        
        if not self.env_manager.file_exists(self.current_project['name'], research_file):
            self.logger.warning("Research file not found. Conducting quick research...")
            await self.research_and_plan()
        
        research_results = json.loads(self.env_manager.read_file(self.current_project['name'], research_file))
        
        prototype_prompt = f"Based on this research: {json.dumps(research_results)}, implement an initial prototype for the most promising project idea."
        prototype_code = await self.ollama_interface.generate_code(prototype_prompt)
        
        prototype_file = "initial_prototype.py"
        self.env_manager.create_file(self.current_project['name'], prototype_file, prototype_code)
        
        self.current_project_files.append(prototype_file)  # Track the prototype file
        self.logger.info(f"Initial prototype implemented and saved to {prototype_file}")

    def load_help_topics(self):
        """
        Load help topics from a predefined file or dictionary.
        """
        help_topics = {
            "start_new_project": "To start a new project, use the 'start_new_project' action. This will create a new project directory and initialize the project state.",
            "continue_project": "To continue working on the current project, use the 'continue_project' action. This will load the current project files and state.",
            "review_project": "To review the completed project, use the 'review_project' action. This will conduct a project retrospective and reset the project state.",
            # Add more help topics as needed
        }
        return help_topics

    def get_help(self, topic):
        """
        Get help information for a specific topic.
        """
        return self.help_topics.get(topic, "Help topic not found.")

    async def interactive_tutorial(self):
        """
        Provide an interactive tutorial to onboard Nimbus and provide ongoing support.
        """
        self.logger.info("Starting interactive tutorial...")
        update_ui({"status": "Starting interactive tutorial"})  # Update UI

        tutorial_content = self.tutorial_manager.load_tutorial("nimbus_intro")
        if not tutorial_content:
            self.logger.error("Failed to load tutorial content")
            return

        for step in tutorial_content['steps']:
            self.logger.info(step['description'])
            update_ui({"tutorial_step": step['description']})

            if 'action' in step:
                await self.execute_action(step['action'])

            if 'user_input' in step:
                # Implement user input logic here
                pass

            await asyncio.sleep(2)

        self.logger.info("Interactive tutorial completed.")
        update_ui({"status": "Interactive tutorial completed"})  # Update UI

    async def gather_structured_context(self):
        """
        Gather and maintain a structured context for Nimbus.
        """
        context = await self.gather_context()
        recent_experiences = await self.knowledge_base.get_recent_experiences()
        available_actions = await self.get_available_actions()

        return {
            "system_status": {
                "state": self.state,
                "project_state": self.knowledge_base.get_project_state(),
                "current_project": self.current_project,
                "current_project_files": self.current_project_files,
            },
            "recent_experiences": recent_experiences,
            "long_term_memory": await self.knowledge_base.get_longterm_memory(),
            "current_tasks": self.actions.get_current_tasks(),
            "performance_metrics": await self.get_performance_metrics(),
            "user_feedback": await self.get_user_feedback(),
            "available_actions": available_actions,
            "environment": {
                "project_directory": self.project_dir,
                "current_project_files": self.current_project_files,
            },
            "consciousness_state": {
                "awareness": self.data_absorber.consciousness_emulator.generate_awareness(data = {
                    "context": context,
                    "available_actions": available_actions,
                    "recent_experiences": recent_experiences
                }),
                "historical_insights": self.data_absorber.consciousness_emulator.extract_historical_insights(recent_experiences),
            },
            "guide_progress_tracker": self.guide.progress_tracker
        }

    async def get_user_feedback(self):
        """
        Get recent user feedback.
        """
        # Implement logic to gather user feedback
        return "No recent user feedback available"

    async def shutdown(self):
        """Shutdown Nimbus and close connections."""
        self.knowledge_base.close()
        # Add any other cleanup code here

    async def get_available_actions(self):
        """
        Get available actions based on the current project state.
        """
        available_actions = []
        if self.current_project:
            if self.current_project_files:
                available_actions.extend([
                    {"name": "edit_file", "type": "file_management"},
                    {"name": "delete_file", "type": "file_management"},
                    {"name": "analyze_code", "type": "code_development"},
                ])
            available_actions.extend([
                {"name": "create_file", "type": "file_management"},
                {"name": "write_tests", "type": "code_development"},
                {"name": "run_code", "type": "code_development"},
                {"name": "commit_changes", "type": "git"},
                {"name": "exit_project", "type": "project_management"}
            ])
        else:
            available_actions.extend([
                {"name": "start_new_project", "type": "project_management"},
                {"name": "continue_project", "type": "project_management"},
            ])
        return available_actions

    # Add this method to switch between menus
    async def switch_menu(self, menu_name):
        """
        Switch to a different menu within a project.
        """
        if self.current_project:
            self.active_menu = menu_name
            update_ui({"active_menu": menu_name})
            self.logger.info(f"Switched to {menu_name} menu")
        else:
            self.logger.warning("Cannot switch menu outside of a project")

if __name__ == "__main__":
    nimbus = Nimbus()
    try:
        asyncio.run(nimbus.start())
    finally:
        asyncio.run(nimbus.shutdown())






















































































































































































































































































































































































