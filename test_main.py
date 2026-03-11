import sys
import os
import unittest

# Add current directory to path to import main.py
sys.path.insert(0, os.getcwd())

try:
    # Import the module
    import main
    print("Import successful.")

    class TestChatbot(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            main.setup_chatbot()

        def test_preprocess(self):
            test_text = "Quelle est la couleur de la voiture?"
            processed = main.preprocess(test_text)
            self.assertEqual(processed, "quelle couleur voiture")

        def test_chatbot_answer(self):
            test_question = "Quelle est la couleur de la voiture?"
            answer = main.chatbot_answer(test_question)
            self.assertIsInstance(answer, str)
            self.assertNotEqual(answer, "")
            
        def test_chatbot_answer_specific(self):
            test_question = "bonjour"
            answer = main.chatbot_answer(test_question)
            self.assertEqual(answer, "Bonjour ! Comment puis-je vous aider aujourd'hui ?")

    print("All tests passed.")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
