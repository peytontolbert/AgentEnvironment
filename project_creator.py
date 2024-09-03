import asyncio
from typing import Dict, Any, List
from ollama_interface import OllamaInterface
from knowledge_base import KnowledgeBase

class ProjectCreator:
    def __init__(self, ollama: OllamaInterface, knowledge_base: KnowledgeBase):
        self.ollama = ollama
        self.knowledge_base = knowledge_base

    async def create_project(self, idea: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new project based on the given idea, utilizing Ollama and the knowledge base.
        """
        # Retrieve relevant knowledge from the knowledge base
        relevant_knowledge = await self.knowledge_base.get_relevant_knowledge(idea)

        # Generate project details using Ollama
        project_details = await self.generate_project_details(idea, relevant_knowledge)

        # Create project structure
        project_structure = await self.create_project_structure(project_details)

        # Generate initial code files
        code_files = await self.generate_initial_code(project_details, project_structure)

        return {
            "idea": idea,
            "details": project_details,
            "structure": project_structure,
            "code_files": code_files
        }

    async def generate_project_details(self, idea: Dict[str, Any], relevant_knowledge: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Given the following project idea and relevant knowledge, generate detailed project specifications:

        Idea: {idea}
        Relevant Knowledge: {relevant_knowledge}

        Please provide:
        1. Project name
        2. Project description
        3. Key features (list of 3-5 features)
        4. Technology stack
        5. Project goals
        6. Potential challenges
        """
        response = await self.ollama.query_ollama("project_details", prompt)
        return response.get("project_details", {})

    async def create_project_structure(self, project_details: Dict[str, Any]) -> List[str]:
        prompt = f"""
        Based on the following project details, suggest a project structure (list of directories and files):

        Project Details: {project_details}

        Provide a list of directories and files that would be suitable for this project.
        """
        response = await self.ollama.query_ollama("project_structure", prompt)
        return response.get("project_structure", [])

    async def generate_initial_code(self, project_details: Dict[str, Any], project_structure: List[str]) -> Dict[str, str]:
        code_files = {}
        for file_path in project_structure:
            if file_path.endswith(('.py', '.js', '.html', '.css')):
                prompt = f"""
                Generate initial code for the file {file_path} based on the following project details:

                Project Details: {project_details}

                Provide the content for this file, including appropriate imports, classes, and functions.
                """
                response = await self.ollama.query_ollama(f"generate_code_{file_path}", prompt)
                code_files[file_path] = response.get("code", "")

        return code_files

# ... existing code ...