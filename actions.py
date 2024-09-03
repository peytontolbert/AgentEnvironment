import subprocess
import logging
import os
import shutil
from ollama_interface import OllamaInterface
from environment_manager import EnvironmentManager

class Actions:
    def __init__(self, ollama_interface: OllamaInterface, env_manager: EnvironmentManager):
        self.logger = logging.getLogger(__name__)
        self.ollama_interface = ollama_interface
        self.env_manager = env_manager
        self.context = {
            "project_state": "idle",  # Can be "idle", "in_progress", or "completed"
            "current_project": None,
            "recent_actions": []
        }
        self.action_log_file = "action_log.txt"
        self.current_tasks = []  # Add this line to initialize current_tasks

    def get_available_actions(self):
        actions = {
            "Project Management": [
                {"name": "start_new_project", "type": "project_management", "description": "Start a new project."},\
                {"name": "project_retrospective", "type": "project_management", "description": "Review the completed project."}
            ],
            "Code Development": [
                {"name": "research_and_plan", "type": "code_development", "description": "Conduct research and plan potential projects."},\
                {"name": "implement_initial_prototype", "type": "code_development", "description": "Implement an initial prototype based on research."},\
                {"name": "generate_code", "type": "code_development", "description": "Generate code based on specifications."},\
                {"name": "run_code", "type": "code_development", "description": "Run the generated code."},\
                {"name": "write_tests", "type": "code_development", "description": "Write unit tests for the code."},\
                {"name": "analyze_code", "type": "code_development", "description": "Analyze the code and suggest improvements."}
            ],
            "File Management": [
                {"name": "view_files", "type": "file_management", "description": "View the list of files in the current project."},\
                {"name": "create_file", "type": "file_management", "description": "Create a new file in the current project."},\
                {"name": "edit_file", "type": "file_management", "description": "Edit an existing file in the current project."},\
                {"name": "save_file", "type": "file_management", "description": "Save changes to a file in the current project."},\
                {"name": "delete_file", "type": "file_management", "description": "Delete a file from the current project."},\
                {"name": "rename_file", "type": "file_management", "description": "Rename a file in the current project."},\
                {"name": "move_file", "type": "file_management", "description": "Move a file to a different directory in the project."},\
                {"name": "copy_file", "type": "file_management", "description": "Copy a file to a different directory in the project."},\
                {"name": "search_in_files", "type": "file_management", "description": "Search for a specific text in the project files."},\
                {"name": "view_file_content", "type": "file_management", "description": "View the content of a specific file."}
            ],
            "Git Operations": [
                {"name": "commit_changes", "type": "git", "description": "Commit changes to the version control system."},\
                {"name": "push_changes", "type": "git", "description": "Push committed changes to the remote repository."},\
                {"name": "pull_changes", "type": "git", "description": "Pull the latest changes from the remote repository."},\
                {"name": "merge_branches", "type": "git", "description": "Merge different branches in the version control system."},\
                {"name": "resolve_conflicts", "type": "git", "description": "Resolve merge conflicts in the project files."},\
                {"name": "create_branch", "type": "git", "description": "Create a new branch in the version control system."},\
                {"name": "delete_branch", "type": "git", "description": "Delete a branch in the version control system."},\
                {"name": "switch_branch", "type": "git", "description": "Switch to a different branch in the version control system."},\
                {"name": "view_commit_history", "type": "git", "description": "View the commit history of the project."},\
                {"name": "revert_commit", "type": "git", "description": "Revert to a previous commit in the version control system."},\
                {"name": "stash_changes", "type": "git", "description": "Stash uncommitted changes in the project."},\
                {"name": "apply_stash", "type": "git", "description": "Apply stashed changes to the project."},\
                {"name": "delete_stash", "type": "git", "description": "Delete a stash in the version control system."},\
                {"name": "view_stash_list", "type": "git", "description": "View the list of stashes in the version control system."},\
                {"name": "create_tag", "type": "git", "description": "Create a new tag in the version control system."},\
                {"name": "delete_tag", "type": "git", "description": "Delete a tag in the version control system."},\
                {"name": "view_tags", "type": "git", "description": "View the list of tags in the version control system."},\
                {"name": "checkout_tag", "type": "git", "description": "Checkout a specific tag in the version control system."},\
                {"name": "create_release", "type": "git", "description": "Create a new release in the version control system."},\
                {"name": "delete_release", "type": "git", "description": "Delete a release in the version control system."},\
                {"name": "view_releases", "type": "git", "description": "View the list of releases in the version control system."},\
                {"name": "checkout_release", "type": "git", "description": "Checkout a specific release in the version control system."}
            ],
            "Issue Tracking": [
                {"name": "create_issue", "type": "issue_tracking", "description": "Create a new issue in the issue tracking system."},\
                {"name": "view_issues", "type": "issue_tracking", "description": "View the list of issues in the issue tracking system."},\
                {"name": "update_issue", "type": "issue_tracking", "description": "Update an existing issue in the issue tracking system."},\
                {"name": "close_issue", "type": "issue_tracking", "description": "Close an issue in the issue tracking system."},\
                {"name": "reopen_issue", "type": "issue_tracking", "description": "Reopen a closed issue in the issue tracking system."},\
                {"name": "assign_issue", "type": "issue_tracking", "description": "Assign an issue to a team member."},\
                {"name": "unassign_issue", "type": "issue_tracking", "description": "Unassign an issue from a team member."},\
                {"name": "comment_on_issue", "type": "issue_tracking", "description": "Comment on an issue in the issue tracking system."},\
                {"name": "view_issue_comments", "type": "issue_tracking", "description": "View the comments on an issue in the issue tracking system."}
            ],
            "Pull Requests": [
                {"name": "create_pull_request", "type": "pull_requests", "description": "Create a new pull request in the version control system."},\
                {"name": "view_pull_requests", "type": "pull_requests", "description": "View the list of pull requests in the version control system."},\
                {"name": "merge_pull_request", "type": "pull_requests", "description": "Merge a pull request in the version control system."},\
                {"name": "close_pull_request", "type": "pull_requests", "description": "Close a pull request in the version control system."},\
                {"name": "comment_on_pull_request", "type": "pull_requests", "description": "Comment on a pull request in the version control system."},\
                {"name": "view_pull_request_comments", "type": "pull_requests", "description": "View the comments on a pull request in the version control system."},\
                {"name": "review_pull_request", "type": "pull_requests", "description": "Review a pull request in the version control system."},\
                {"name": "approve_pull_request", "type": "pull_requests", "description": "Approve a pull request in the version control system."},\
                {"name": "request_changes_on_pull_request", "type": "pull_requests", "description": "Request changes on a pull request in the version control system."}
            ],
            "Code Review": [
                {"name": "view_code_diff", "type": "code_review", "description": "View the code differences between commits or branches."},\
                {"name": "view_code_blame", "type": "code_review", "description": "View the blame information for a specific file."},\
                {"name": "view_code_history", "type": "code_review", "description": "View the history of changes for a specific file."},\
                {"name": "view_code_annotations", "type": "code_review", "description": "View the annotations for a specific file."},\
                {"name": "view_code_coverage", "type": "code_review", "description": "View the code coverage report for the project."},\
                {"name": "run_code_coverage", "type": "code_review", "description": "Run the code coverage analysis for the project."}
            ],
            "Testing": [
                {"name": "view_test_results", "type": "testing", "description": "View the results of the unit tests."},\
                {"name": "run_unit_tests", "type": "testing", "description": "Run the unit tests for the project."},\
                {"name": "run_integration_tests", "type": "testing", "description": "Run the integration tests for the project."},\
                {"name": "run_system_tests", "type": "testing", "description": "Run the system tests for the project."},\
                {"name": "run_acceptance_tests", "type": "testing", "description": "Run the acceptance tests for the project."},\
                {"name": "run_regression_tests", "type": "testing", "description": "Run the regression tests for the project."},\
                {"name": "run_smoke_tests", "type": "testing", "description": "Run the smoke tests for the project."},\
                {"name": "run_performance_tests", "type": "testing", "description": "Run the performance tests for the project."},\
                {"name": "run_security_tests", "type": "testing", "description": "Run the security tests for the project."},\
                {"name": "run_usability_tests", "type": "testing", "description": "Run the usability tests for the project."},\
                {"name": "run_compatibility_tests", "type": "testing", "description": "Run the compatibility tests for the project."},\
                {"name": "run_load_tests", "type": "testing", "description": "Run the load tests for the project."},\
                {"name": "run_stress_tests", "type": "testing", "description": "Run the stress tests for the project."},\
                {"name": "run_reliability_tests", "type": "testing", "description": "Run the reliability tests for the project."},\
                {"name": "run_maintainability_tests", "type": "testing", "description": "Run the maintainability tests for the project."},\
                {"name": "run_portability_tests", "type": "testing", "description": "Run the portability tests for the project."},\
                {"name": "run_interoperability_tests", "type": "testing", "description": "Run the interoperability tests for the project."},\
                {"name": "run_scalability_tests", "type": "testing", "description": "Run the scalability tests for the project."},\
                {"name": "run_availability_tests", "type": "testing", "description": "Run the availability tests for the project."},\
                {"name": "run_durability_tests", "type": "testing", "description": "Run the durability tests for the project."},\
                {"name": "run_recoverability_tests", "type": "testing", "description": "Run the recoverability tests for the project."},\
                {"name": "run_installability_tests", "type": "testing", "description": "Run the installability tests for the project."},\
                {"name": "run_configuration_tests", "type": "testing", "description": "Run the configuration tests for the project."},\
                {"name": "run_documentation_tests", "type": "testing", "description": "Run the documentation tests for the project."},\
                {"name": "run_localization_tests", "type": "testing", "description": "Run the localization tests for the project."},\
                {"name": "run_internationalization_tests", "type": "testing", "description": "Run the internationalization tests for the project."},\
                {"name": "run_accessibility_tests", "type": "testing", "description": "Run the accessibility tests for the project."},\
                {"name": "run_compliance_tests", "type": "testing", "description": "Run the compliance tests for the project."},\
                {"name": "run_audit_tests", "type": "testing", "description": "Run the audit tests for the project."},\
                {"name": "run_backup_tests", "type": "testing", "description": "Run the backup tests for the project."},\
                {"name": "run_restore_tests", "type": "testing", "description": "Run the restore tests for the project."},\
                {"name": "run_disaster_recovery_tests", "type": "testing", "description": "Run the disaster recovery tests for the project."},\
                {"name": "run_failover_tests", "type": "testing", "description": "Run the failover tests for the project."},\
                {"name": "run_failback_tests", "type": "testing", "description": "Run the failback tests for the project."},\
                {"name": "run_switchover_tests", "type": "testing", "description": "Run the switchover tests for the project."},\
                {"name": "run_switchback_tests", "type": "testing", "description": "Run the switchback tests for the project."},\
                {"name": "run_hotfix_tests", "type": "testing", "description": "Run the hotfix tests for the project."},\
                {"name": "run_patch_tests", "type": "testing", "description": "Run the patch tests for the project."},\
                {"name": "run_upgrade_tests", "type": "testing", "description": "Run the upgrade tests for the project."},\
                {"name": "run_downgrade_tests", "type": "testing", "description": "Run the downgrade tests for the project."},\
                {"name": "run_migration_tests", "type": "testing", "description": "Run the migration tests for the project."},\
                {"name": "run_conversion_tests", "type": "testing", "description": "Run the conversion tests for the project."},\
                {"name": "run_transformation_tests", "type": "testing", "description": "Run the transformation tests for the project."}
                ]
                }
        # Flatten the dictionary to a list of actions
        return [action for category in actions.values() for action in category]

    async def execute_action(self, action):
        action_name = action.get("name")
        action_method = getattr(self, action_name, None)
        if action_method:
            try:
                result = await action_method(action.get("details", {}))
                self.context["recent_actions"].append(action_name)
                self.logger.info(f"Executed action: {action_name}")
                self.log_action_result(action_name, result)
            except Exception as e:
                self.logger.error(f"Error executing action {action_name}: {e}")
                self.log_action_result(action_name, {"error": str(e)})
        else:
            self.logger.warning(f"Unknown action: {action_name}")

    def log_action_result(self, action_name, result):
        with open(self.action_log_file, "a") as log_file:
            log_file.write(f"Action: {action_name}\nResult: {result}\n\n")
        # Save to a persistent storage
        self.save_action_to_persistent_storage(action_name, result)

    def save_action_to_persistent_storage(self, action_name, result):
        # Implement logic to save action and result to a persistent storage
        # For example, save to a database or a JSON file
        with open("persistent_action_log.json", "a") as persistent_log_file:
            import json
            log_entry = {"action": action_name, "result": result}
            persistent_log_file.write(json.dumps(log_entry) + "\n")

    async def start_new_project(self, details):
        if self.context["project_state"] == "in_progress":
            self.logger.warning("Cannot start a new project while another is in progress.")
            return {"status": "failed", "reason": "Project already in progress"}
        self.logger.info("Starting a new project...")
        self.context["project_state"] = "in_progress"
        self.context["current_project"] = details.get("project_name", "Unnamed Project")
        # Implement logic to initialize the project
        await self.create_file({"file_name": "README.md", "content": f"# {self.context['current_project']}\n\nProject description goes here."})
        await self.create_file({"file_name": "main.py", "content": "# Main entry point for the project\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()"})
        await self.create_file({"file_name": "requirements.txt", "content": "# List project dependencies here"})
        return {"status": "success", "message": "Project initialized with essential files"}

    async def research_and_plan(self, details):
        """
        Conduct research and plan potential projects.
        """
        self.logger.info("Conducting research and planning potential projects...")
        research_prompt = "Research and suggest potential AI projects that could be implemented."
        research_results = await self.ollama_interface.query_ollama(self.ollama_interface.system_prompt, research_prompt)
        
        research_file = "research_and_plan.md"
        content = f"# Research and Planning\n\n{research_results['research']}\n\n## Potential Projects\n\n{research_results['potential_projects']}"
        self.env_manager.create_file(self.context["current_project"], research_file, content)
        
        self.logger.info(f"Research and planning results saved to {research_file}")
        return {"status": "success", "file": research_file, "stage": "planning"}

    async def implement_initial_prototype(self, details):
        """
        Implement an initial prototype based on the research and planning.
        """
        self.logger.info("Implementing initial prototype...")
        research_file = "research_and_plan.md"
        
        if not self.env_manager.file_exists(self.context["current_project"], research_file):
            self.logger.warning("Research file not found. Conducting quick research...")
            await self.research_and_plan({})
        
        research_content = self.env_manager.read_file(self.context["current_project"], research_file)
        
        prototype_prompt = f"Based on this research:\n\n{research_content}\n\nImplement an initial prototype for the most promising project idea."
        prototype_code = await self.ollama_interface.generate_code(prototype_prompt)
        
        main_file = "main.py"
        existing_content = self.env_manager.read_file(self.context["current_project"], main_file)
        updated_content = f"{existing_content}\n\n# Prototype implementation\n{prototype_code}"
        self.env_manager.modify_file(self.context["current_project"], main_file, {"content": updated_content})
        
        self.logger.info(f"Initial prototype implemented and saved to {main_file}")
        return {"status": "success", "file": main_file, "message": "Initial prototype implemented in main.py", "stage": "implementation"}

    async def generate_code(self, details):
        """
        Generate code based on the provided specification.
        """
        self.logger.info(f"Generating code with details: {details}")
        spec = details.get("spec", "Generate a simple Python script")
        file_name = details.get("file_name", "generated_code.py")
        code = await self.ollama_interface.generate_code(spec)
        self.logger.info(f"Generated code: {code}")
        
        project_name = self.context.get("current_project")
        if project_name:
            success = self.env_manager.create_file(project_name, file_name, code)
            if success:
                self.logger.info(f"Saved generated code to {file_name}")
                return {"status": "success", "code": code, "file_name": file_name}
            else:
                self.logger.error(f"Failed to save generated code to {file_name}")
                return {"status": "failed", "reason": "Failed to save generated code"}
        else:
            self.logger.error("No current project to save generated code")
            return {"status": "failed", "reason": "No current project"}

    async def run_code(self, details):
        self.logger.info("Running the code...")
        file_name = details.get("file_name")
        if not file_name:
            self.logger.error("No file name provided for code execution.")
            return {"status": "failed", "reason": "No file name provided"}

        project_name = self.context.get("current_project")
        if not project_name:
            self.logger.error("No current project selected for code execution.")
            return {"status": "failed", "reason": "No current project"}

        try:
            file_path = self.env_manager.get_file_path(project_name, file_name)
            result = subprocess.run(["python", file_path], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                output = result.stdout
                status = "success"
            else:
                output = result.stderr
                status = "error"
            self.logger.info(f"Code execution output: {output}")
            return {"status": status, "output": output, "return_code": result.returncode}
        except subprocess.TimeoutExpired:
            self.logger.error("Code execution timed out")
            return {"status": "timeout", "output": "Execution timed out after 30 seconds"}
        except Exception as e:
            self.logger.error(f"Error executing code in {file_name}: {e}")
            return {"status": "error", "output": str(e)}

    async def write_tests(self, details):
        self.logger.info("Writing unit tests...")
        file_name = details.get("file_name")
        if not file_name:
            self.logger.error("No file name provided for writing tests.")
            return {"status": "failed", "reason": "No file name provided"}

        project_name = self.context.get("current_project")
        if not project_name:
            self.logger.error("No current project selected for writing tests.")
            return {"status": "failed", "reason": "No current project"}

        try:
            code = self.env_manager.read_file(project_name, file_name)
            test_prompt = f"Write unit tests for the following code:\n\n{code}\n\nProvide the tests in a format ready to be saved as a separate test file."
            test_code = await self.ollama_interface.generate_code(test_prompt)
            
            test_dir = "tests"
            if not self.env_manager.file_exists(project_name, test_dir):
                self.env_manager.create_file(project_name, test_dir, "")  # Create tests directory
            test_file_name = f"{test_dir}/test_{file_name}"
            success = self.env_manager.create_file(project_name, test_file_name, test_code)
            
            if success:
                self.logger.info(f"Unit tests written and saved to {test_file_name}")
                return {"status": "success", "file_name": test_file_name, "stage": "testing"}
            else:
                self.logger.error(f"Failed to save unit tests to {test_file_name}")
                return {"status": "failed", "reason": "Failed to save unit tests"}
        except Exception as e:
            self.logger.error(f"Error writing tests for {file_name}: {e}")
            return {"status": "failed", "reason": str(e)}

    async def analyze_code(self, details):
        """
        Analyze the code and provide suggestions for improvement.
       """
        self.logger.info("Analyzing code...")
        file_name = details.get("file_name")
        if not file_name:
            self.logger.error("No file name provided for code analysis.")
            return {"status": "failed", "reason": "No file name provided"}

        project_name = self.context.get("current_project")
        if not project_name:
            self.logger.error("No current project selected for code analysis.")
            return {"status": "failed", "reason": "No current project"}

        try:
            code = self.env_manager.read_file(project_name, file_name)
            analysis = await self.ollama_interface.analyze_code(code)
            analysis["code_style"] = await self.check_code_style(code)
            analysis["complexity"] = await self.calculate_complexity(code)
            self.logger.info(f"Code analysis for {file_name}: {analysis}")
            return {"status": "success", "analysis": analysis, "stage": "review"}
        except Exception as e:
            self.logger.error(f"Error analyzing code in {file_name}: {e}")
            return {"status": "failed", "reason": str(e)}

    async def check_code_style(self, code):
        # Implement basic code style checks
        style_issues = []
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            if len(line) > 100:
                style_issues.append(f"Line {i} is too long ({len(line)} > 100 characters)")
            if line.strip().startswith("import") and " as " not in line:
                style_issues.append(f"Line {i}: Consider using 'import ... as ...' for clarity")
        return style_issues

    async def calculate_complexity(self, code):
        # Implement a basic complexity calculation (e.g., counting if/else statements, loops)
        complexity = 0
        for line in code.split("\n"):
            if any(keyword in line for keyword in ["if", "for", "while", "except"]):
                complexity += 1
        return complexity

    async def project_retrospective(self, details):
        self.logger.info("Conducting project retrospective...")
        # Implement project retrospective logic
        self.context["project_state"] = "idle"
        self.context["current_project"] = None
        return {"status": "success"}

    async def view_files(self, details):
        self.logger.info("Viewing files in the current project...")
        project_name = self.context["current_project"]
        if project_name:
            files = self.env_manager.list_files(project_name)
            self.logger.info(f"Files in project {project_name}: {files}")
            return {"status": "success", "files": files}
        else:
            self.logger.warning("No current project to view files.")
            return {"status": "failed", "reason": "No current project"}

    async def create_file(self, details):
        """
        Create a new file in the current project.
       """
        self.logger.info("Creating a new file...")
        file_name = details.get("file_name")
        content = details.get("content", "")
        if not file_name:
            self.logger.error("No file name provided for file creation.")
            return {"status": "failed", "reason": "No file name provided"}

        project_name = self.context.get("current_project")
        if not project_name:
            self.logger.error("No current project selected for file creation.")
            return {"status": "failed", "reason": "No current project"}

        try:
            if file_name.endswith('.py'):
                content = "# -*- coding: utf-8 -*-\n\n" + content
            elif file_name == 'README.md':
                content = f"# {self.context['current_project']}\n\n{content}"
            success = self.env_manager.create_file(project_name, file_name, content)
            if success:
                self.logger.info(f"Created file: {file_name}")
                return {"status": "success", "file_path": self.env_manager.get_file_path(project_name, file_name)}
            else:
                self.logger.error(f"Failed to create file: {file_name}")
                return {"status": "failed", "reason": "Failed to create file"}
        except Exception as e:
            self.logger.error(f"Error creating file {file_name}: {e}")
            return {"status": "failed", "reason": str(e)}

    async def edit_file(self, details):
        """
        Edit an existing file in the current project.
       """
        self.logger.info("Editing an existing file...")
        file_name = details.get("file_name")
        new_content = details.get("new_content")
        if not file_name or new_content is None:
            self.logger.error("File name or new content not provided for editing.")
            return {"status": "failed", "reason": "Missing file name or new content"}

        project_name = self.context.get("current_project")
        if not project_name:
            self.logger.error("No current project selected for file editing.")
            return {"status": "failed", "reason": "No current project"}

        try:
            success = self.env_manager.modify_file(project_name, file_name, {"content": new_content})
            if success:
                self.logger.info(f"Edited file: {file_name}")
                return {"status": "success"}
            else:
                self.logger.error(f"Failed to edit file: {file_name}")
                return {"status": "failed", "reason": "Failed to edit file"}
        except Exception as e:
            self.logger.error(f"Error editing file {file_name}: {e}")
            return {"status": "failed", "reason": str(e)}

    async def save_file(self, details):
        """
        Save changes to a file.
        """
        self.logger.info("Saving changes to a file...")
        project_name = self.context["current_project"]
        if project_name:
            file_name = details.get("file_name")
            content = details.get("content", "")
            success = self.env_manager.create_file(project_name, file_name, content)
            if success:
                self.logger.info(f"Saved changes to file: {file_name}")
                return {"status": "success"}
            else:
                self.logger.error(f"Failed to save file: {file_name}")
                return {"status": "failed", "reason": "Failed to save file"}
        else:
            self.logger.warning("No current project to save file.")
            return {"status": "failed", "reason": "No current project"}

    async def delete_file(self, details):
        """
        Delete a file from the current project.
        """
        self.logger.info("Deleting a file...")
        project_name = self.context["current_project"]
        if project_name:
            file_name = details.get("file_name")
            success = self.env_manager.delete_file(project_name, file_name)
            if success:
                self.logger.info(f"Deleted file: {file_name}")
                return {"status": "success"}
            else:
                self.logger.error(f"Failed to delete file: {file_name}")
                return {"status": "failed", "reason": "Failed to delete file"}
        else:
            self.logger.warning("No current project to delete file.")
            return {"status": "failed", "reason": "No current project"}

    async def rename_file(self, details):
        """
        Rename a file in the current project.
        """
        self.logger.info("Renaming a file...")
        project_name = self.context["current_project"]
        if project_name:
            old_file_name = details.get("old_file_name")
            new_file_name = details.get("new_file_name")
            success = self.env_manager.rename_file(project_name, old_file_name, new_file_name)
            if success:
                self.logger.info(f"Renamed file: {old_file_name} to {new_file_name}")
                return {"status": "success"}
            else:
                self.logger.error(f"Failed to rename file: {old_file_name}")
                return {"status": "failed", "reason": "Failed to rename file"}
        else:
            self.logger.warning("No current project to rename file.")
            return {"status": "failed", "reason": "No current project"}

    async def move_file(self, details):
        """
        Move a file to a different project.
        """
        self.logger.info("Moving a file...")
        project_name = self.context["current_project"]
        if project_name:
            file_name = details.get("file_name")
            dest_project = details.get("destination_project")
            success = self.env_manager.move_file(project_name, dest_project, file_name)
            if success:
                self.logger.info(f"Moved file: {file_name} to project: {dest_project}")
                return {"status": "success"}
            else:
                self.logger.error(f"Failed to move file: {file_name}")
                return {"status": "failed", "reason": "Failed to move file"}
        else:
            self.logger.warning("No current project to move file.")
            return {"status": "failed", "reason": "No current project"}

    async def copy_file(self, details):
        """
        Copy a file to a different project.
        """
        self.logger.info("Copying a file...")
        project_name = self.context["current_project"]
        if project_name:
            file_name = details.get("file_name")
            dest_project = details.get("destination_project")
            success = self.env_manager.copy_file(project_name, dest_project, file_name)
            if success:
                self.logger.info(f"Copied file: {file_name} to project: {dest_project}")
                return {"status": "success"}
            else:
                self.logger.error(f"Failed to copy file: {file_name}")
                return {"status": "failed", "reason": "Failed to copy file"}
        else:
            self.logger.warning("No current project to copy file.")
            return {"status": "failed", "reason": "No current project"}

    async def search_in_files(self, details):
        """
        Search for text in files within the current project.
        """
        self.logger.info("Searching in files...")
        project_name = self.context["current_project"]
        if project_name:
            search_text = details.get("search_text")
            results = []
            for file_name in self.env_manager.list_files(project_name):
                content = self.env_manager.read_file(project_name, file_name)
                if search_text in content:
                    results.append(file_name)
            self.logger.info(f"Search results: {results}")
            return {"status": "success", "results": results}
        else:
            self.logger.warning("No current project to search in files.")
            return {"status": "failed", "reason": "No current project"}

    async def view_file_content(self, details):
        """
        View the content of a file in the current project.
        """
        self.logger.info("Viewing file content...")
        project_name = self.context["current_project"]
        if project_name:
            file_name = details.get("file_name")
            content = self.env_manager.read_file(project_name, file_name)
            if content:
                self.logger.info(f"File content: {content}")
                return {"status": "success", "content": content}
            else:
                self.logger.error(f"Failed to read file: {file_name}")
                return {"status": "failed", "reason": "Failed to read file"}
        else:
            self.logger.warning("No current project to view file content.")
            return {"status": "failed", "reason": "No current project"}

    async def commit_changes(self, details):
        """
        Commit changes to the current project.
        """
        self.logger.info("Committing changes...")
        project_name = self.context["current_project"]
        if project_name:
            commit_message = details.get("commit_message", "No commit message provided.")
            subprocess.run(["git", "add", "."], cwd=project_name, check=True)
            subprocess.run(["git", "commit", "-m", commit_message], cwd=project_name, check=True)
            self.logger.info("Changes committed successfully.")
            return {"status": "success"}
        else:
            self.logger.warning("No current project to commit changes.")
            return {"status": "failed", "reason": "No current project"}

    async def push_changes(self, details):
        """
        Push changes to the current project.
        """
        self.logger.info("Pushing changes...")
        project_name = self.context["current_project"]
        if project_name:
            subprocess.run(["git", "push"], cwd=project_name, check=True)
            self.logger.info("Changes pushed successfully.")
        else:
            self.logger.warning("No current project to push changes.")

    async def pull_changes(self, details):
        """
        Pull changes from the current project.
        """
        self.logger.info("Pulling changes...")
        project_name = self.context["current_project"]
        if project_name:
            subprocess.run(["git", "pull"], cwd=project_name, check=True)
            self.logger.info("Changes pulled successfully.")
        else:
            self.logger.warning("No current project to pull changes.")

    async def merge_branches(self, details):
        """
        Merge branches in the current project.
        """
        self.logger.info("Merging branches...")
        project_name = self.context["current_project"]
        if project_name:
            branch_name = details.get("branch_name")
            subprocess.run(["git", "merge", branch_name], cwd=project_name, check=True)
            self.logger.info(f"Branch {branch_name} merged successfully.")
        else:
            self.logger.warning("No current project to merge branches.")

    async def resolve_conflicts(self, details):
        """
        Resolve merge conflicts in the current project.
        """
        self.logger.info("Resolving merge conflicts...")
        project_name = self.context["current_project"]
        if project_name:
            subprocess.run(["git", "mergetool"], cwd=project_name, check=True)
            self.logger.info("Merge conflicts resolved successfully.")
        else:
            self.logger.warning("No current project to resolve merge conflicts.")

    async def create_branch(self, details):
        """
        Create a new branch in the current project.
        """
        self.logger.info("Creating a new branch...")
        project_name = self.context["current_project"]
        if project_name:
            branch_name = details.get("branch_name")
            subprocess.run(["git", "checkout", "-b", branch_name], cwd=project_name, check=True)
            self.logger.info(f"Branch {branch_name} created successfully.")
        else:
            self.logger.warning("No current project to create branch.")

    async def delete_branch(self, details):
        self.logger.info("Deleting a branch...")
        project_name = self.context["current_project"]
        if project_name:
            branch_name = details.get("branch_name")
            subprocess.run(["git", "branch", "-d", branch_name], cwd=project_name, check=True)
            self.logger.info(f"Branch {branch_name} deleted successfully.")
        else:
            self.logger.warning("No current project to delete branch.")

    async def switch_branch(self, details):
        self.logger.info("Switching to a different branch...")
        project_name = self.context["current_project"]
        if project_name:
            branch_name = details.get("branch_name")
            subprocess.run(["git", "checkout", branch_name], cwd=project_name, check=True)
            self.logger.info(f"Switched to branch {branch_name} successfully.")
        else:
            self.logger.warning("No current project to switch branch.")

    def get_current_tasks(self):
        """
        Get the list of current tasks.

        Returns:
            List[Dict[str, Any]]: List of current tasks.
        """
        return self.current_tasks

    def add_task(self, task):
        """
        Add a new task to the current tasks list.

        Args:
            task (Dict[str, Any]): Task to add.
        """
        self.current_tasks.append(task)

    def remove_task(self, task_id):
        """
        Remove a task from the current tasks list.

        Args:
            task_id (str): ID of the task to remove.
        """
        self.current_tasks = [task for task in self.current_tasks if task.get('id') != task_id]

    def update_task(self, task_id, updates):
        """
        Update a task in the current tasks list.

        Args:
            task_id (str): ID of the task to update.
            updates (Dict[str, Any]): Updates to apply to the task.
        """
        for task in self.current_tasks:
            if task.get('id') == task_id:
                task.update(updates)
                break

    def prioritize_actions(self):
        """
        Prioritize actions based on the current context and project state.
        """
        available_actions = self.get_available_actions()
        project_state = self.context.get("project_state", "idle")
        
        def priority_score(action):
            if project_state == "idle" and action["name"] in ["start_new_project", "continue_project"]:
                return 10
            elif project_state == "in_progress":
                if action["type"] == "code_development":
                    return 8
                elif action["type"] == "file_management":
                    return 7
                elif action["type"] == "git":
                    return 6
            elif project_state == "review":
                if action["type"] == "testing":
                    return 9
                elif action["name"] == "analyze_code":
                    return 8
            return 5  # Default priority

        prioritized_actions = sorted(available_actions, key=priority_score, reverse=True)
        return prioritized_actions
