import logging
from typing import Dict, Any, List
import time
import json  # Added import for json
from ollama_interface import OllamaInterface
from actions import Actions
from environment_manager import EnvironmentManager
import os
from nimbus_server import update_ui
import random

class ConsciousnessEmulator:
    """
    A class to emulate consciousness by processing context, actions, and experiences.

    Attributes:
        ollama (OllamaInterface): Interface to interact with Ollama.
        logger (logging.Logger): Logger for logging information.
        actions (Actions): Actions available for the emulator.
        omniscient_data_absorber: Data absorber for retrieving recent experiences.
        max_context_size (int): Maximum size of the context.
        context (List[Dict[str, Any]]): List to store the context.
        env_manager (EnvironmentManager): Manager for environment-related operations.
    """

    def __init__(self, ollama: OllamaInterface, omniscient_data_absorber, env_manager: EnvironmentManager, max_context_size: int = 100):
        """
        Initialize the ConsciousnessEmulator with the given parameters.

        Args:
            ollama (OllamaInterface): Interface to interact with Ollama.
            omniscient_data_absorber: Data absorber for retrieving recent experiences.
            env_manager (EnvironmentManager): Manager for environment-related operations.
            max_context_size (int, optional): Maximum size of the context. Defaults to 100.
        """
        self.ollama = ollama
        self.logger = logging.getLogger(__name__)
        self.actions = Actions(ollama, env_manager)
        self.omniscient_data_absorber = omniscient_data_absorber
        self.max_context_size = max_context_size
        self.context = []
        self.env_manager = env_manager

    def update_context(self, new_entry: Dict[str, Any]):
        """
        Update the context with a new entry, ensuring it does not exceed the maximum size.

        Args:
            new_entry (Dict[str, Any]): New entry to add to the context.
        """
        self.context.append(new_entry)
        if len(self.context) > self.max_context_size:
            self.context.pop(0)  # Remove the oldest entry to maintain the context size
        self.logger.info(f"Updated context: {self.context}")

    async def emulate_consciousness(self, structured_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Emulate consciousness by processing the structured context and selecting the next action.

        Args:
            structured_context (Dict[str, Any]): Structured context data.

        Returns:
            Dict[str, Any]: Decision made by the emulator.
        """
        self.update_context(structured_context)
        self.logger.info(f"Processing structured context: {structured_context}")

        awareness = self.generate_awareness(structured_context)
        refinement_suggestions = await self.get_refinement_suggestions(structured_context)

        await self.log_chain_of_thought(structured_context, awareness, refinement_suggestions)

        selected_action = await self.select_action(awareness, structured_context['available_actions'])
        
        decision = self.create_decision(awareness, selected_action)

        self.logger.info(f"Emulated consciousness decision: {decision}")

        return decision

    async def select_action(self, awareness: Dict[str, Any], refined_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Select the next action based on the current awareness and refined actions.

        Args:
            awareness (Dict[str, Any]): Current awareness state.
            refined_actions (List[Dict[str, Any]]): List of refined actions.

        Returns:
            Dict[str, Any]: Selected action.
        """
        try:
            prompt = f"Based on the current awareness:\n{json.dumps(awareness, indent=2)}\n\nSelect the most appropriate action from these refined actions:\n{json.dumps(refined_actions, indent=2)}\n\nProvide your selection as a JSON object with 'name', 'type', and 'details' fields. The 'details' field should include any necessary information for executing the action, such as file names or specific parameters."
            response = await self.ollama.query_ollama("action_selection", prompt)
            selected_action = response.get("selected_action", {"name": "continue_project", "type": "default", "details": {}})
            self.logger.info(f"Selected action: {selected_action}")
            return selected_action
        except Exception as e:
            self.logger.error(f"Error selecting action: {e}")
            return {"name": "continue_project", "type": "default", "details": {}}

    def create_decision(self, awareness: Dict[str, Any], selected_action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a decision dictionary based on awareness and selected action.

        Args:
            awareness (Dict[str, Any]): Generated awareness state.
            selected_action (Dict[str, Any]): Selected action to execute.

        Returns:
            Dict[str, Any]: Decision dictionary.
        """
        return {
            "enhanced_awareness": awareness,
            "action": selected_action
        }

    async def get_recent_experiences(self) -> List[Dict[str, Any]]:
        """
        Retrieve recent experiences from the knowledge base.

        Returns:
            List[Dict[str, Any]]: List of recent experiences.
        """
        try:
            recent_experiences = await self.omniscient_data_absorber.knowledge_base.get_recent_experiences()
            self.logger.info(f"Retrieved {len(recent_experiences)} recent experiences")
            return recent_experiences
        except Exception as e:
            self.logger.error(f"Error retrieving recent experiences: {e}")
            return []

    async def get_refinement_suggestions(self, structured_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get suggestions for refining the consciousness emulation.

        Args:
            structured_context (Dict[str, Any]): Structured context data.

        Returns:
            Dict[str, Any]: Refinement suggestions.
        """
        try:
            refinement_suggestions = await self.ollama.query_ollama(
                "consciousness_refinement",
                "Refine consciousness emulation based on current context, recent experiences, and project state.",
                context={
                    "structured_context": structured_context,
                }
            )
            self.logger.info(f"Consciousness refinement suggestions: {refinement_suggestions}")
            return refinement_suggestions
        except Exception as e:
            self.logger.error(f"Error getting refinement suggestions: {e}")
            return {}

    async def log_chain_of_thought(self, structured_context: Dict[str, Any], awareness: Dict[str, Any], refinement_suggestions: Dict[str, Any]):
        """
        Log the chain of thought during the consciousness emulation process.

        Args:
            structured_context (Dict[str, Any]): Structured context data.
            awareness (Dict[str, Any]): Generated awareness state.
            refinement_suggestions (Dict[str, Any]): Suggestions for refinement.
        """
        try:
            await self.omniscient_data_absorber.log_chain_of_thought({
                "process": "Consciousness emulation",
                "context": self.context,  # Use the updated context
                "structured_context": structured_context,
                "awareness": awareness,
                "refinement_suggestions": refinement_suggestions,
            })
        except Exception as e:
            self.logger.error(f"Error logging chain of thought: {e}")

    def extract_and_refine_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and refine context for better awareness.

        Args:
            context (Dict[str, Any]): Initial context.

        Returns:
            Dict[str, Any]: Refined context.
        """
        refined_context = {k: v for k, v in context.items() if v}
        self.logger.debug(f"Extracted context: {context}")
        self.logger.info(f"Refined context: {refined_context}")
        return refined_context

    def refine_available_actions(self, actions: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Refine available actions based on the current context and active menu.

        Args:
            actions (List[Dict[str, Any]]): List of available actions.
            context (Dict[str, Any]): Current context.

        Returns:
            List[Dict[str, Any]]: Refined list of actions.
        """
        if not actions:
            self.logger.warning("No actions provided to refine.")
            return []

        active_menu = context.get('active_menu', 'main')
        refined_actions = []
        for action in actions:
            if self.is_action_relevant(action, context) and self.is_action_in_menu(action, active_menu):
                refined_actions.append(action)
        self.logger.debug(f"Available actions: {actions}")
        self.logger.info(f"Refined actions for {active_menu} menu: {refined_actions}")
        return refined_actions

    def is_action_in_menu(self, action: Dict[str, Any], active_menu: str) -> bool:
        """
        Determine if an action belongs to the active menu.

        Args:
            action (Dict[str, Any]): Action to evaluate.
            active_menu (str): Currently active menu.

        Returns:
            bool: True if the action belongs to the active menu, False otherwise.
        """
        menu_actions = {
            'main': ['start_new_project', 'project_retrospective', 'research_and_plan'],
            'dev': ['implement_initial_prototype', 'generate_code', 'run_code', 'write_tests', 'analyze_code'],
            'git': ['create_pull_request', 'view_pull_requests', 'merge_pull_request', 'close_pull_request'],
            'file': ['view_files', 'create_file', 'edit_file', 'save_file', 'delete_file', 'rename_file', 'move_file', 'copy_file'],
            'issue': ['create_issue', 'view_issues', 'update_issue', 'close_issue', 'reopen_issue', 'assign_issue', 'unassign_issue'],
            'test': ['run_unit_tests', 'run_integration_tests', 'run_system_tests', 'run_acceptance_tests', 'run_regression_tests', 'run_smoke_tests', 'run_performance_tests', 'run_security_tests', 'run_usability_tests', 'run_compatibility_tests', 'run_load_tests', 'run_stress_tests', 'run_reliability_tests', 'run_maintainability_tests', 'run_portability_tests', 'run_interoperability_tests', 'run_scalability_tests', 'run_availability_tests', 'run_durability_tests', 'run_recoverability_tests', 'run_installability_tests', 'run_configuration_tests', 'run_documentation_tests', 'run_localization_tests', 'run_internationalization_tests', 'run_accessibility_tests', 'run_compliance_tests', 'run_audit_tests', 'run_backup_tests', 'run_restore_tests', 'run_disaster_recovery_tests', 'run_failover_tests', 'run_failback_tests', 'run_switchover_tests', 'run_switchback_tests', 'run_hotfix_tests', 'run_patch_tests', 'run_upgrade_tests', 'run_downgrade_tests', 'run_migration_tests', 'run_conversion_tests', 'run_transformation_tests']
        }
        
        return action['name'] in menu_actions.get(active_menu, []) or active_menu == 'all'

    def is_action_relevant(self, action: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Determine if an action is relevant based on the current context.

        Args:
            action (Dict[str, Any]): Action to evaluate.
            context (Dict[str, Any]): Current context.

        Returns:
            bool: True if the action is relevant, False otherwise.
        """
        try:
            if "git" in action["type"] and not context.get("is_git_project"):
                self.logger.debug(f"Action {action['name']} is not relevant for non-git projects.")
                return False
            return True
        except (TypeError, KeyError) as e:
            self.logger.warning(f"Error determining action relevance: {e}")
            return False

    def generate_awareness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive awareness state.

        Args:
            data (Dict[str, Any]): Dictionary containing context, available actions, and recent experiences.

        Returns:
            Dict[str, Any]: Generated awareness state.
        """
        context = data.get('context', {})
        available_actions = data.get('available_actions', [])
        recent_experiences = data.get('recent_experiences', [])

        return {
            "current_state": context.get('system_status', {}),
            "refined_actions": self.refine_available_actions(available_actions, context),
            "recent_experiences": recent_experiences,
            "historical_insights": self.extract_historical_insights(recent_experiences),
            "potential_future_states": self.predict_future_states(context),
            "project_state": context.get('system_status', {}).get('project_state'),
            "current_project": context.get('system_status', {}).get('current_project')
        }

    def extract_historical_insights(self, recent_experiences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract relevant insights from recent experiences.

        Args:
            recent_experiences (List[Dict[str, Any]]): List of recent experiences.

        Returns:
            Dict[str, Any]: Extracted historical insights.
        """
        insights = {}
        for experience in recent_experiences:
            lesson = experience.get("lesson_learned")
            if lesson:
                category = self.categorize_lesson(lesson)
                if category not in insights:
                    insights[category] = []
                insights[category].append(lesson)
        return insights

    def categorize_lesson(self, lesson: str) -> str:
        """
        Categorize a lesson learned from an experience.

        Args:
            lesson (str): Lesson learned.

        Returns:
            str: Category of the lesson.
        """
        # Implement logic to categorize lessons (e.g., "coding", "project management", "problem-solving")
        return "general"  # Placeholder

    def predict_future_states(self, structured_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict potential future states based on current context, actions, and recent experiences.

        Args:
            structured_context (Dict[str, Any]): Structured context data.

        Returns:
            Dict[str, Any]: Predicted future states.
        """
        # Implement prediction logic
        return {"predicted_state": "Improved system performance"}  # Placeholder

    async def generate_project_details(self, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate project name and description based on the current context.

        Args:
            context (Dict[str, Any]): Current context.

        Returns:
            Dict[str, str]: Generated project name and description.
        """
        try:
            prompt = f"Generate a project name and description based on the following context:\n{context}"
            response = await self.ollama.query_ollama("project_details_generation", prompt)
            project_name = response.get("project_name", f"Project_{int(time.time())}")
            project_description = response.get("project_description", "This is a new project created by Nimbus.")
            return {
                "project_name": project_name,
                "project_description": project_description
            }
        except Exception as e:
            self.logger.error(f"Error generating project details: {e}")
            return {
                "project_name": f"Project_{int(time.time())}",
                "project_description": "This is a new project created by Nimbus."
            }

    async def execute_action(self, action: Dict[str, Any]):
        """
        Execute the given action.

        Args:
            action (Dict[str, Any]): Action to execute.
        """
        try:
            self.logger.info(f"Executing action: {action['name']}")
            action_type = action.get('type')
            if action_type in ['modify_file', 'create_file', 'edit_file', 'delete_file', 'rename_file', 'move_file', 'copy_file']:
                await self.handle_file_action(action)
            elif action_type in ['create_issue', 'view_issues', 'update_issue', 'close_issue', 'reopen_issue', 'assign_issue', 'unassign_issue', 'comment_on_issue', 'view_issue_comments']:
                await self.handle_issue_action(action)
            elif action_type in ['create_pull_request', 'view_pull_requests', 'merge_pull_request', 'close_pull_request', 'comment_on_pull_request', 'view_pull_request_comments', 'review_pull_request', 'approve_pull_request', 'request_changes_on_pull_request']:
                await self.handle_pull_request_action(action)
            elif action_type in ['view_code_diff', 'view_code_blame', 'view_code_history', 'view_code_annotations', 'view_code_coverage', 'run_code_coverage']:
                await self.handle_code_review_action(action)
            elif action_type in ['run_unit_tests', 'run_integration_tests', 'run_system_tests', 'run_acceptance_tests', 'run_regression_tests', 'run_smoke_tests', 'run_performance_tests', 'run_security_tests', 'run_usability_tests', 'run_compatibility_tests', 'run_load_tests', 'run_stress_tests', 'run_reliability_tests', 'run_maintainability_tests', 'run_portability_tests', 'run_interoperability_tests', 'run_scalability_tests', 'run_availability_tests', 'run_durability_tests', 'run_recoverability_tests', 'run_installability_tests', 'run_configuration_tests', 'run_documentation_tests', 'run_localization_tests', 'run_internationalization_tests', 'run_accessibility_tests', 'run_compliance_tests', 'run_audit_tests', 'run_backup_tests', 'run_restore_tests', 'run_disaster_recovery_tests', 'run_failover_tests', 'run_failback_tests', 'run_switchover_tests', 'run_switchback_tests', 'run_hotfix_tests', 'run_patch_tests', 'run_upgrade_tests', 'run_downgrade_tests', 'run_migration_tests', 'run_conversion_tests', 'run_transformation_tests']:
                await self.handle_testing_action(action)
            else:
                self.logger.warning(f"Unknown action type: {action_type}")
        except Exception as e:
            self.logger.error(f"Error executing action {action['name']}: {e}")

    async def handle_file_action(self, action: Dict[str, Any]):
        """
        Handle file-related actions.

        Args:
            action (Dict[str, Any]): Action to execute.
        """
        project_name = self.context[-1].get("current_project", {}).get("name")
        if not project_name:
            self.logger.error("No current project selected.")
            return

        if not self.env_manager.project_exists(project_name):
            self.logger.error(f"Project {project_name} does not exist.")
            return

        if action['type'] == 'create_file':
            success = self.env_manager.create_file(project_name, action['file_name'], action['content'])
        elif action['type'] == 'modify_file':
            success = self.env_manager.modify_file(project_name, action['file_name'], action['modifications'])
        elif action['type'] == 'delete_file':
            success = self.env_manager.delete_file(project_name, action['file_name'])
        elif action['type'] == 'rename_file':
            success = self.env_manager.rename_file(project_name, action['old_name'], action['new_name'])
        elif action['type'] == 'move_file':
            success = self.env_manager.move_file(project_name, action['dest_project'], action['file_name'])
        elif action['type'] == 'copy_file':
            success = self.env_manager.copy_file(project_name, action['dest_project'], action['file_name'])
        else:
            self.logger.warning(f"Unknown file action type: {action['type']}")
            return

        if success:
            self.logger.info(f"Action {action['name']} executed successfully.")
        else:
            self.logger.error(f"Action {action['name']} failed.")

    async def handle_issue_action(self, action: Dict[str, Any]):
        """
        Handle issue-related actions.

        Args:
            action (Dict[str, Any]): Action to execute.
        """
        # Implement issue handling logic here
        pass

    async def handle_pull_request_action(self, action: Dict[str, Any]):
        """
        Handle pull request-related actions.

        Args:
            action (Dict[str, Any]): Action to execute.
        """
        # Implement pull request handling logic here
        pass

    async def handle_code_review_action(self, action: Dict[str, Any]):
        """
        Handle code review-related actions.

        Args:
            action (Dict[str, Any]): Action to execute.
        """
        # Implement code review handling logic here
        pass

    async def handle_testing_action(self, action: Dict[str, Any]):
        """
        Handle testing-related actions.

        Args:
            action (Dict[str, Any]): Action to execute.
        """
        # Implement testing handling logic here
        pass

    async def analyze_feedback(self, feedback: Dict[str, Any]):
        """Analyze feedback to improve future actions."""
        try:
            analysis_result = await self.ollama.query_ollama(
                "feedback_analysis",
                f"Analyze this feedback and suggest improvements: {json.dumps(feedback)}",
                context={"task": "feedback_analysis"}
            )
            self.logger.info(f"Feedback analysis result: {analysis_result}")
            return analysis_result
        except Exception as e:
            self.logger.error(f"Error analyzing feedback: {e}")
            return {}
