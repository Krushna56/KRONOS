from app.core.security import verify_password, hash_password

class AuthService:
    @staticmethod
    def hash_password_str(password: str) -> str:
        return hash_password(password)

    @staticmethod
    def verify_password_str(plain: str, hashed: str) -> bool:
        return verify_password(plain, hashed)
