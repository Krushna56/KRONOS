import unittest
from app.core.config import settings


class TestConfiguration(unittest.TestCase):
    def test_settings_loaded(self):
        self.assertIsNotNone(settings.APP_NAME)
        self.assertIsNotNone(settings.DATABASE_URL)
        self.assertIsNotNone(settings.JWT_SECRET)
        self.assertEqual(settings.JWT_ALGORITHM, "HS256")


if __name__ == "__main__":
    unittest.main()