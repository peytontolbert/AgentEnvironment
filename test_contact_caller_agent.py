import unittest
from unittest.mock import patch, MagicMock
import asyncio
import json
from contact_caller_agent import ContactCallerAgent

class TestContactCallerAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ContactCallerAgent()

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='[{"name": "John Doe", "called": false}]')
    def test_load_contacts(self, mock_file):
        contacts = self.agent.load_contacts()
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0]['name'], "John Doe")
        self.assertFalse(contacts[0]['called'])

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('json.dump')
    def test_save_contacts(self, mock_json_dump, mock_file):
        self.agent.contacts = [{"name": "Jane Doe", "called": True}]
        self.agent.save_contacts()
        mock_json_dump.assert_called_once_with(self.agent.contacts, mock_file())

    @patch('contact_caller_agent.OllamaInterface')
    def test_select_next_contact(self, mock_ollama):
        mock_ollama_instance = MagicMock()
        mock_ollama_instance.query_ollama.return_value = {'selected_contact': 'John Doe'}
        mock_ollama.return_value = mock_ollama_instance

        self.agent.contacts = [
            {"name": "John Doe", "called": False},
            {"name": "Jane Doe", "called": True}
        ]

        loop = asyncio.get_event_loop()
        next_contact = loop.run_until_complete(self.agent.select_next_contact())

        self.assertEqual(next_contact['name'], "John Doe")
        self.assertFalse(next_contact['called'])

    @patch('contact_caller_agent.OllamaInterface')
    @patch('builtins.print')
    @patch('builtins.input', side_effect=['Hello', 'Goodbye'])
    def test_make_call(self, mock_input, mock_print, mock_ollama):
        mock_ollama_instance = MagicMock()
        mock_ollama_instance.query_ollama.return_value = {'message': 'AI response'}
        mock_ollama.return_value = mock_ollama_instance

        contact = {"name": "John Doe", "called": False}
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.agent.make_call(contact))

        self.assertTrue(contact['called'])
        self.assertIn('call_summary', contact)
        self.assertIn('AI response', contact['call_summary'])
        self.assertIn('Hello', contact['call_summary'])
        self.assertIn('Goodbye', contact['call_summary'])

if __name__ == '__main__':
    unittest.main()
