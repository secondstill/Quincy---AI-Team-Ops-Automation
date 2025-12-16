from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

try:
    print("Hashing 'admin123'...")
    hash = pwd_context.hash("admin123")
    print(f"Hash: {hash}")
    print("Verifying...")
    valid = pwd_context.verify("admin123", hash)
    print(f"Valid: {valid}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
