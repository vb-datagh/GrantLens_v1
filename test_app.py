import sys
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class AppTests(unittest.TestCase):
    def test_demo_and_empty_filters(self):
        app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, '10')
        self.assertEqual(app.metric[1].value, '$475,000')
        self.assertEqual(app.metric[2].value, '4')
        app.sidebar.multiselect[0].set_value([]).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, '0')
