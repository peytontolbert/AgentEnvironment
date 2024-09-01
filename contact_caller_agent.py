import asyncio
import json
from typing import Dict, List
from ollama_interface import OllamaInterface
from workflow_executor import WorkflowExecutor

class ContactCallerAgent:
    def __init__(self):
        self.ollama = OllamaInterface()
        self.workflow_executor = WorkflowExecutor()
        self.contacts = self.load_contacts()

    def load_contacts(self) -> List[Dict[str, any]]:
        try:
            with open('contacts.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_contacts(self):
        with open('contacts.json', 'w') as f:
            json.dump(self.contacts, f)

    async def select_next_contact(self) -> Dict[str, any]:
        uncalled_contacts = [c for c in self.contacts if not c.get('called', False)]
        if not uncalled_contacts:
            return None
        
        context = {"uncalled_contacts": uncalled_contacts}
        selection = await self.ollama.query_ollama(
            "contact_selection",
            "Select the next contact to call based on priority and other factors.",
            context=context
        )
        return next((c for c in uncalled_contacts if c['name'] == selection['selected_contact']), None)

    async def make_call(self, contact: Dict[str, any]):
        print(f"Calling {contact['name']}...")
        
        # Simulated call stages
        stages = ['introduction', 'explanation', 'closeout']
        conversation_history = []

        for stage in stages:
            context = {
                "contact": contact,
                "stage": stage,
                "conversation_history": conversation_history
            }
            
            response = await self.ollama.query_ollama(
                f"call_{stage}",
                f"Generate a response for the {stage} stage of the call.",
                context=context
            )
            
            print(f"Agent: {response['message']}")
            conversation_history.append({"role": "agent", "content": response['message']})
            
            # Simulate user response (in a real scenario, this would be transcribed audio)
            user_response = input(f"{contact['name']}: ")
            conversation_history.append({"role": "user", "content": user_response})

        contact['called'] = True
        contact['call_summary'] = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
        self.save_contacts()

    async def run(self):
        while True:
            contact = await self.select_next_contact()
            if not contact:
                print("All contacts have been called.")
                break
            
            await self.make_call(contact)

if __name__ == "__main__":
    agent = ContactCallerAgent()
    asyncio.run(agent.run())
