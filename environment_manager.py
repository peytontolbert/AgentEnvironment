import os
import shutil
import logging
from typing import Dict, Any, List

class EnvironmentManager:
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.logger = logging.getLogger(__name__)

    def create_project(self, project_name: str) -> str:
        project_path = os.path.join(self.base_path, project_name)
        os.makedirs(project_path, exist_ok=True)
        self.logger.info(f"Created project: {project_path}")
        return project_path

    def list_projects(self) -> List[str]:
        return [d for d in os.listdir(self.base_path) if os.path.isdir(os.path.join(self.base_path, d))]

    def create_file(self, project_name: str, file_name: str, content: str) -> bool:
        if not self.project_exists(project_name):
            self.logger.error(f"Project {project_name} does not exist")
            return False
        file_path = self.get_file_path(project_name, file_name)
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            self.logger.info(f"Created file: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error creating file {file_path}: {e}")
            return False

    def read_file(self, project_name: str, file_name: str) -> str:
        file_path = os.path.join(self.base_path, project_name, file_name)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            self.logger.info(f"Read file: {file_path}")
            return content
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return ""

    def modify_file(self, project_name: str, file_name: str, modifications: Dict[str, Any]) -> bool:
        file_path = os.path.join(self.base_path, project_name, file_name)
        try:
            content = self.read_file(project_name, file_name)
            if not content:
                return False
            for key, value in modifications.items():
                content = content.replace(key, value)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            self.logger.info(f"Modified file: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error modifying file {file_path}: {e}")
            return False

    def delete_file(self, project_name: str, file_name: str) -> bool:
        file_path = os.path.join(self.base_path, project_name, file_name)
        try:
            os.remove(file_path)
            self.logger.info(f"Deleted file: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting file {file_path}: {e}")
            return False

    def list_files(self, project_name: str) -> List[str]:
        project_path = os.path.join(self.base_path, project_name)
        return [f for f in os.listdir(project_path) if os.path.isfile(os.path.join(project_path, f))]

    def rename_file(self, project_name: str, old_name: str, new_name: str) -> bool:
        old_path = os.path.join(self.base_path, project_name, old_name)
        new_path = os.path.join(self.base_path, project_name, new_name)
        try:
            os.rename(old_path, new_path)
            self.logger.info(f"Renamed file: {old_path} to {new_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error renaming file {old_path}: {e}")
            return False

    def move_file(self, source_project: str, dest_project: str, file_name: str) -> bool:
        source_path = os.path.join(self.base_path, source_project, file_name)
        dest_path = os.path.join(self.base_path, dest_project, file_name)
        try:
            shutil.move(source_path, dest_path)
            self.logger.info(f"Moved file: {source_path} to {dest_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error moving file {source_path}: {e}")
            return False

    def copy_file(self, source_project: str, dest_project: str, file_name: str) -> bool:
        source_path = os.path.join(self.base_path, source_project, file_name)
        dest_path = os.path.join(self.base_path, dest_project, file_name)
        try:
            shutil.copy2(source_path, dest_path)
            self.logger.info(f"Copied file: {source_path} to {dest_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error copying file {source_path}: {e}")
            return False

    def get_project_path(self, project_name: str) -> str:
        return os.path.join(self.base_path, project_name)

    def get_file_path(self, project_name: str, file_name: str) -> str:
        return os.path.join(self.get_project_path(project_name), file_name)

    def project_exists(self, project_name: str) -> bool:
        return os.path.isdir(self.get_project_path(project_name))

    def file_exists(self, project_name: str, file_name: str) -> bool:
        return os.path.isfile(self.get_file_path(project_name, file_name))