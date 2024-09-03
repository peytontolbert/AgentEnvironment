import logging
from typing import Dict, Any, List, Optional
from ollama_interface import OllamaInterface
import time
import json
import asyncio
from functools import lru_cache

class NimbusGuideError(Exception):
    """Custom exception class for NimbusGuide-specific errors."""
    pass

class ProjectProgress:
    def __init__(self, name: str):
        self.name = name
        self.stages_completed: List[str] = []
        self.current_stage: str = 'planning'
        self.challenges_faced: List[str] = []
        self.actions_performed: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {
            'start_time': time.time(),
            'total_actions': 0,
            'errors_encountered': 0,
            'tests_written': 0,
            'commits_made': 0
        }
        self.stage_requirements: Dict[str, List[str]] = {
            'planning': ['research_and_plan.md'],
            'implementation': ['main.py', 'README.md'],
            'testing': ['test_main.py'],
            'review': ['code_analysis.md']
        }

    def add_action(self, action_data: Dict[str, Any]):
        self.actions_performed.append(action_data)
        self.metrics['total_actions'] += 1

    def update_stage(self, new_stage: str):
        if self.current_stage != new_stage:
            self.stages_completed.append(self.current_stage)
            self.current_stage = new_stage

    def add_challenge(self, challenge: str):
        self.challenges_faced.append(challenge)

    def get_recent_actions(self, n: int = 5) -> List[Dict[str, Any]]:
        return self.actions_performed[-n:]

    def analyze_progress(self) -> Dict[str, Any]:
        return {
            'action_frequency': len(self.actions_performed) / (time.time() - self.metrics['start_time']),
            'error_rate': self.metrics['errors_encountered'] / max(self.metrics['total_actions'], 1),
            'test_coverage': self.metrics['tests_written'] / max(self.metrics['total_actions'], 1),
            'commit_frequency': self.metrics['commits_made'] / max(self.metrics['total_actions'], 1)
        }

    def is_stage_complete(self, stage: str, project_files: List[str]) -> bool:
        required_files = self.stage_requirements.get(stage, [])
        return all(required_file in project_files for required_file in required_files)

class NimbusGuide:
    def __init__(self, ollama_interface: OllamaInterface):
        self.logger = logging.getLogger(__name__)
        self.ollama_interface = ollama_interface
        self.progress_tracker: Dict[str, ProjectProgress] = {}
        self.progress_log_file = "nimbus_progress_log.json"
        self.guidance_cache: Dict[str, Dict[str, Any]] = {}

    async def update_progress(self, action_name: str, result: Dict[str, Any], context: Dict[str, Any]):
        try:
            current_project_name = context.get('current_project', {}).get('name', 'unknown_project')
            current_project = self.progress_tracker.get(current_project_name)
            
            if not current_project:
                current_project = ProjectProgress(current_project_name)
                self.progress_tracker[current_project_name] = current_project
            
            action_data = {
                'action': action_name,
                'result': result,
                'timestamp': time.time(),
                'project_state': context.get('project_state', 'unknown'),
                'files_affected': context.get('files_affected', []),
                'code_changes': context.get('code_changes', {}),
                'performance_metrics': context.get('performance_metrics', {}),
                'errors_encountered': context.get('errors_encountered', [])
            }
            
            current_project.add_action(action_data)
            
            if result.get('stage'):
                current_project.update_stage(result['stage'])
            
            if context.get('challenges_faced'):
                current_project.add_challenge(context['challenges_faced'])
            
            # Log detailed progress information
            self.logger.info(f"Project: {current_project_name}, Stage: {current_project.current_stage}, Action: {action_name}, Result: {result.get('status')}")
            
            # Log performance metrics
            self.logger.info(f"Performance Metrics: {action_data['performance_metrics']}")
            
            # Log any errors encountered
            if action_data['errors_encountered']:
                self.logger.warning(f"Errors Encountered: {action_data['errors_encountered']}")
            
            await self.save_progress_to_file()
            self.logger.info(f"Updated progress for project: {current_project_name}")
        except Exception as e:
            self.logger.error(f"Error updating progress: {e}")
            raise NimbusGuideError(f"Failed to update progress: {e}")

    async def save_progress_to_file(self):
        """Save the current progress tracker to a JSON file."""
        try:
            progress_data = {name: vars(progress) for name, progress in self.progress_tracker.items()}
            async with asyncio.Lock():
                with open(self.progress_log_file, 'w') as f:
                    json.dump(progress_data, f, indent=2, default=str)
            self.logger.info(f"Progress saved to {self.progress_log_file}")
        except Exception as e:
            self.logger.error(f"Error saving progress to file: {e}")
            raise NimbusGuideError(f"Failed to save progress to file: {e}")

    @lru_cache(maxsize=32)
    def get_project_progress(self, project_name: str) -> ProjectProgress:
        """Get project progress with caching."""
        return self.progress_tracker.get(project_name, ProjectProgress(project_name))

    async def provide_guidance(self, nimbus_context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide guidance based on the current Nimbus context."""
        try:
            current_project = nimbus_context.get('system_status', {}).get('current_project')
            if current_project:
                project_progress = self.progress_tracker.get(current_project['name'])
                if project_progress:
                    current_stage = project_progress.current_stage
                    recent_actions = project_progress.get_recent_actions(5)
                    
                    self.logger.info(f"Providing guidance for project: {current_project['name']}, Current stage: {current_stage}")
                    self.logger.info(f"Recent actions: {recent_actions}")
                    
                    # Analyze progress and provide specific recommendations
                    progress_analysis = project_progress.analyze_progress()
                    self.logger.info(f"Progress analysis: {progress_analysis}")
                    
                    # Generate recommendations based on the current stage and progress
                    recommendations = self.generate_recommendations(current_stage, progress_analysis)
                    
                    return {
                        "recommended_action": recommendations[0] if recommendations else None,
                        "alternative_actions": recommendations[1:],
                        "progress_analysis": progress_analysis
                    }
            
            # Default guidance if no project is active
            return await super().provide_guidance(nimbus_context)
        except Exception as e:
            self.logger.error(f"Error providing guidance: {e}")
            return self.generate_fallback_guidance()

    def generate_fallback_guidance(self) -> Dict[str, Any]:
        """Generate fallback guidance when an error occurs."""
        return {
            "next_priority": "Resolve system issues",
            "potential_challenges": ["System encountered an unexpected state"],
            "tips_and_suggestions": ["Review system logs", "Check for any missing or corrupted data"],
            "areas_needing_attention": ["System stability", "Error handling"],
            "recommended_action": "analyze_project_state",
            "specific_recommendations": ["Perform a system health check"]
        }

    def generate_recommendations(self, current_stage: str, progress_analysis: Dict[str, Any]) -> List[str]:
        # Implement logic to generate recommendations based on the current stage and progress analysis
        # This is a placeholder implementation
        if current_stage == 'planning':
            return ['research_and_plan', 'create_file']
        elif current_stage == 'implementation':
            return ['implement_initial_prototype', 'generate_code', 'edit_file']
        elif current_stage == 'testing':
            return ['write_tests', 'run_code', 'analyze_code']
        elif current_stage == 'review':
            return ['analyze_code', 'project_retrospective']
        else:
            return []