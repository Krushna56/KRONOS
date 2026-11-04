import unittest
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


class TestAuthSecurity(unittest.TestCase):
    def test_password_hashing(self):
        plain = "MySecretPass123!"
        hashed = hash_password(plain)
        self.assertNotEqual(plain, hashed)
        self.assertTrue(verify_password(plain, hashed))
        self.assertFalse(verify_password("WrongPass", hashed))

    def test_jwt_token_lifecycle(self):
        subject = "testuser_krushna"
        token = create_access_token(subject=subject)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 20)

        decoded_sub = decode_access_token(token)
        self.assertEqual(decoded_sub, subject)

    def test_invalid_token_decoding(self):
        invalid_token = "invalid.token.string"
        decoded = decode_access_token(invalid_token)
        self.assertIsNone(decoded)


if __name__ == "__main__":
    unittest.main()
