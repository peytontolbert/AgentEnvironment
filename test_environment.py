import unittest
from environment_manager import EnvironmentManager
import tempfile
import os

class TestEnvironment(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_manager = EnvironmentManager(self.temp_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_create_project(self):
        project_name = "test_project"
        project_path = self.env_manager.create_project(project_name)
        self.assertTrue(os.path.exists(project_path))

    def test_create_file(self):
        project_name = "test_project"
        self.env_manager.create_project(project_name)
        file_name = "test_file.txt"
        content = "Hello, World!"
        success = self.env_manager.create_file(project_name, file_name, content)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, project_name, file_name)))

    def test_read_file(self):
        project_name = "test_project"
        self.env_manager.create_project(project_name)
        file_name = "test_file.txt"
        content = "Hello, World!"
        self.env_manager.create_file(project_name, file_name, content)
        read_content = self.env_manager.read_file(project_name, file_name)
        self.assertEqual(content, read_content)

    def test_modify_file(self):
        project_name = "test_project"
        self.env_manager.create_project(project_name)
        file_name = "test_file.txt"
        content = "Hello, World!"
        self.env_manager.create_file(project_name, file_name, content)
        modifications = {"Hello": "Hi"}
        success = self.env_manager.modify_file(project_name, file_name, modifications)
        self.assertTrue(success)
        modified_content = self.env_manager.read_file(project_name, file_name)
        self.assertEqual(modified_content, "Hi, World!")

    # Add more tests for other EnvironmentManager methods

if __name__ == '__main__':
    unittest.main()