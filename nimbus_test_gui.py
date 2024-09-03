import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import asyncio
from nimbus import Nimbus
import os

class NimbusTestGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Nimbus Test Interface")
        self.nimbus = Nimbus()
        self.setup_ui()

    def setup_ui(self):
        # Main frame
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(padx=10, pady=10)

        # Action buttons frame
        self.action_frame = tk.Frame(self.main_frame)
        self.action_frame.pack(pady=10)

        # Project listbox
        self.project_listbox = tk.Listbox(self.main_frame, width=50, height=10)
        self.project_listbox.pack(pady=10)

        # Output text area
        self.output_area = scrolledtext.ScrolledText(self.main_frame, wrap=tk.WORD, width=60, height=20)
        self.output_area.pack(padx=10, pady=10)

        # Initially load main menu actions
        self.load_main_menu_actions()

    def load_main_menu_actions(self):
        for widget in self.action_frame.winfo_children():
            widget.destroy()

        actions = [
            ("Start New Project", self.start_new_project),
            ("Continue Project", self.continue_project),
            ("Get Help", self.get_help),
            ("Interactive Tutorial", self.interactive_tutorial)
        ]

        for action, command in actions:
            tk.Button(self.action_frame, text=action, command=command).pack(side=tk.LEFT, padx=5)

        self.load_existing_projects()

    def load_project_actions(self):
        for widget in self.action_frame.winfo_children():
            widget.destroy()

        actions = [
            ("Edit File", self.edit_file),
            ("Create File", self.create_file),
            ("Delete File", self.delete_file),
            ("Run Code", self.run_code),
            ("Analyze Code", self.analyze_code),
            ("Write Tests", self.write_tests),
            ("Commit Changes", self.commit_changes),
            ("Exit Project", self.exit_project)
        ]

        for action, command in actions:
            tk.Button(self.action_frame, text=action, command=command).pack(side=tk.LEFT, padx=5)

    def load_existing_projects(self):
        self.project_listbox.delete(0, tk.END)
        if os.path.exists(self.nimbus.project_dir):
            projects = [d for d in os.listdir(self.nimbus.project_dir) if os.path.isdir(os.path.join(self.nimbus.project_dir, d))]
            for project in projects:
                self.project_listbox.insert(tk.END, project)
        else:
            self.update_output(f"Project directory not found: {self.nimbus.project_dir}")

    def update_output(self, message):
        self.output_area.insert(tk.END, message + "\n")
        self.output_area.see(tk.END)

    def start_new_project(self):
        project_name = simpledialog.askstring("New Project", "Enter project name:")
        if project_name:
            self.update_output(f"Starting new project: {project_name}")
            asyncio.run(self.nimbus.execute_start_new_project())
            self.nimbus.current_project = {"name": project_name, "path": os.path.join(self.nimbus.project_dir, project_name)}
            self.load_project_actions()

    def continue_project(self):
        selected = self.project_listbox.curselection()
        if selected:
            project_name = self.project_listbox.get(selected[0])
            self.update_output(f"Continuing project: {project_name}")
            project_path = os.path.join(self.nimbus.project_dir, project_name)
            if os.path.exists(project_path):
                self.nimbus.current_project = {"name": project_name, "path": project_path}
                asyncio.run(self.nimbus.execute_continue_project())
                self.load_project_actions()
            else:
                messagebox.showerror("Project Not Found", f"The project directory for '{project_name}' does not exist.")
        else:
            messagebox.showwarning("No Project Selected", "Please select a project to continue.")

    def get_help(self):
        self.update_output("Getting help...")
        asyncio.run(self.nimbus.execute_get_help())

    def interactive_tutorial(self):
        self.update_output("Starting interactive tutorial...")
        asyncio.run(self.nimbus.execute_interactive_tutorial())

    def edit_file(self):
        self.update_output("Editing file...")
        # Implement file editing logic

    def create_file(self):
        file_name = simpledialog.askstring("Create File", "Enter file name:")
        if file_name:
            self.update_output(f"Creating file: {file_name}")
            # Implement file creation logic

    def delete_file(self):
        file_name = simpledialog.askstring("Delete File", "Enter file name to delete:")
        if file_name:
            self.update_output(f"Deleting file: {file_name}")
            # Implement file deletion logic

    def run_code(self):
        self.update_output("Running code...")
        asyncio.run(self.nimbus.run_code())

    def analyze_code(self):
        self.update_output("Analyzing code...")
        asyncio.run(self.nimbus.analyze_code())

    def write_tests(self):
        self.update_output("Writing tests...")
        asyncio.run(self.nimbus.write_tests())

    def commit_changes(self):
        self.update_output("Committing changes...")
        # Implement commit changes logic

    def exit_project(self):
        self.update_output("Exiting project...")
        asyncio.run(self.nimbus.execute_exit_project())
        self.load_main_menu_actions()

def main():
    root = tk.Tk()
    NimbusTestGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()