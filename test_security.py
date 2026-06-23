import sys
import traceback
from auth import create_user, login_user, engine
from sqlalchemy import text

def run_test(name, func, expect_exception=False, expected_exception_type=None):
    print(f"Running test: {name}...", end=" ")
    try:
        result = func()
        if expect_exception:
            print("FAILED (Expected exception, but got success)")
            return False
        if not expect_exception and result is False:
            print("FAILED (Function returned False)")
            return False
        print("PASSED")
        return True
    except Exception as e:
        if expect_exception:
            if expected_exception_type and not isinstance(e, expected_exception_type):
                print(f"FAILED (Expected {expected_exception_type.__name__}, but got {type(e).__name__}: {e})")
                return False
            print(f"PASSED (Caught expected {type(e).__name__}: {e})")
            return True
        print(f"FAILED (Unexpected exception: {e})")
        traceback.print_exc()
        return False

def setup():
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM users WHERE username LIKE 'testuser_%'"))
        conn.commit()

def teardown():
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM users WHERE username LIKE 'testuser_%'"))
        conn.commit()

def main():
    setup()
    tests_passed = 0
    total_tests = 0

    print("\n--- Testing Registration ---")
    
    # 1. Invalid Username
    total_tests += 1
    tests_passed += run_test(
        "Invalid Username (spaces)", 
        lambda: create_user("test user 1", "test@test.com", "ValidPass1!"),
        expect_exception=True, expected_exception_type=ValueError
    )

    # 2. Invalid Email
    total_tests += 1
    tests_passed += run_test(
        "Invalid Email (no @)", 
        lambda: create_user("testuser_invalid_email", "testtest.com", "ValidPass1!"),
        expect_exception=True, expected_exception_type=ValueError
    )

    # 3. Weak Passwords
    total_tests += 1
    tests_passed += run_test(
        "Weak Password (short)", 
        lambda: create_user("testuser_short_pass", "test@test.com", "Sh1!"),
        expect_exception=True, expected_exception_type=ValueError
    )
    
    total_tests += 1
    tests_passed += run_test(
        "Weak Password (no uppercase)", 
        lambda: create_user("testuser_no_upper", "test@test.com", "validpass1!"),
        expect_exception=True, expected_exception_type=ValueError
    )
    
    total_tests += 1
    tests_passed += run_test(
        "Weak Password (no number)", 
        lambda: create_user("testuser_no_num", "test@test.com", "ValidPass!"),
        expect_exception=True, expected_exception_type=ValueError
    )

    total_tests += 1
    tests_passed += run_test(
        "Weak Password (no special)", 
        lambda: create_user("testuser_no_spec", "test@test.com", "ValidPass123"),
        expect_exception=True, expected_exception_type=ValueError
    )

    # 4. Valid Registration
    total_tests += 1
    tests_passed += run_test(
        "Valid Registration", 
        lambda: create_user("testuser_valid", "valid@test.com", "ValidPass1!") is None # Returns None on success
    )

    # 5. Duplicate Registration
    total_tests += 1
    tests_passed += run_test(
        "Duplicate Username Registration", 
        lambda: create_user("testuser_valid", "another@test.com", "ValidPass1!"),
        expect_exception=True, expected_exception_type=ValueError
    )
    
    total_tests += 1
    tests_passed += run_test(
        "Duplicate Email Registration", 
        lambda: create_user("testuser_another", "valid@test.com", "ValidPass1!"),
        expect_exception=True, expected_exception_type=ValueError
    )

    print("\n--- Testing Login & Brute Force ---")
    
    # 6. Successful Login
    total_tests += 1
    tests_passed += run_test(
        "Successful Login", 
        lambda: login_user("testuser_valid", "ValidPass1!") is not None
    )

    # 7. Invalid Login
    total_tests += 1
    tests_passed += run_test(
        "Invalid Login (wrong password)", 
        lambda: login_user("testuser_valid", "WrongPass1!") is None
    )

    # 8. Brute Force Lockout
    print("\nSimulating Brute Force...")
    # We already have 1 failed attempt from the test above.
    # Let's do 4 more to reach 5 failed attempts.
    for i in range(4):
        try:
            login_user("testuser_valid", "WrongPass1!")
            print(f"Failed attempt {i+2}/5 logged.")
        except PermissionError:
            print(f"Failed attempt {i+2}/5 locked out as expected.")
        
    total_tests += 1
    tests_passed += run_test(
        "Brute Force Lockout Triggered", 
        lambda: login_user("testuser_valid", "WrongPass1!"),
        expect_exception=True, expected_exception_type=PermissionError
    )
    
    total_tests += 1
    tests_passed += run_test(
        "Cannot login even with correct password when locked", 
        lambda: login_user("testuser_valid", "ValidPass1!"),
        expect_exception=True, expected_exception_type=PermissionError
    )

    print(f"\n--- Test Summary: {tests_passed}/{total_tests} Passed ---")
    teardown()
    
    if tests_passed != total_tests:
        sys.exit(1)

if __name__ == "__main__":
    main()
