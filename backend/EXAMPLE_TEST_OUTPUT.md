# Example Test Output

## Expected Output When Running Tests

### Full Test Suite Run
```bash
$ pytest test_app.py -v

============================= test session starts ==============================
platform linux -- Python 3.11.2, pytest-7.4.3, pluggy-1.5.0
cachedir: .pytest_cache
rootdir: /path/to/backend
plugins: flask-1.3.0, cov-4.1.0, mock-3.12.0
collected 64 items

test_app.py::TestHealthEndpoint::test_health_returns_ok_status PASSED     [  1%]
test_app.py::TestHealthEndpoint::test_health_returns_timestamp PASSED     [  3%]
test_app.py::TestHealthEndpoint::test_health_response_format PASSED       [  4%]
test_app.py::TestLoginEndpoint::test_login_successful_with_valid_credentials PASSED [  6%]
test_app.py::TestLoginEndpoint::test_login_fails_with_invalid_credentials PASSED [  7%]
test_app.py::TestLoginEndpoint::test_login_with_empty_username PASSED     [  9%]
test_app.py::TestLoginEndpoint::test_login_with_empty_password PASSED     [ 10%]
test_app.py::TestLoginEndpoint::test_login_with_missing_username PASSED   [ 12%]
test_app.py::TestLoginEndpoint::test_login_with_missing_password PASSED   [ 14%]
test_app.py::TestLoginEndpoint::test_login_with_no_json_body PASSED       [ 15%]
test_app.py::TestLoginEndpoint::test_login_with_invalid_json PASSED       [ 17%]
test_app.py::TestLoginEndpoint::test_login_prevents_sql_injection_in_username PASSED [ 18%]
test_app.py::TestLoginEndpoint::test_login_with_special_characters_in_username PASSED [ 20%]
test_app.py::TestLoginEndpoint::test_login_with_unicode_characters PASSED [ 21%]
test_app.py::TestLoginEndpoint::test_login_token_format PASSED            [ 23%]
test_app.py::TestLoginEndpoint::test_login_closes_database_connection PASSED [ 25%]
test_app.py::TestLoginEndpoint::test_login_with_very_long_username PASSED [ 26%]
test_app.py::TestLoginEndpoint::test_login_with_very_long_password PASSED [ 28%]
... [remaining tests] ...

======================== 64 passed in 2.34s =================================
```

### With Coverage Report
```bash
$ pytest test_app.py -v --cov=app --cov-report=term-missing

============================= test session starts ==============================
collected 64 items

test_app.py::TestHealthEndpoint::test_health_returns_ok_status PASSED     [  1%]
... [all tests] ...
======================== 64 passed in 2.34s =================================

---------- coverage: platform linux, python 3.11.2-final-0 ----------
Name     Stmts   Miss  Cover   Missing
--------------------------------------
app.py      28      2    93%   11, 52
--------------------------------------
TOTAL       28      2    93%

Coverage HTML written to dir htmlcov
```

### Running Specific Test Class
```bash
$ pytest test_app.py::TestLoginEndpoint -v

============================= test session starts ==============================
collected 19 items

test_app.py::TestLoginEndpoint::test_login_successful_with_valid_credentials PASSED
test_app.py::TestLoginEndpoint::test_login_fails_with_invalid_credentials PASSED
test_app.py::TestLoginEndpoint::test_login_with_empty_username PASSED
test_app.py::TestLoginEndpoint::test_login_with_empty_password PASSED
test_app.py::TestLoginEndpoint::test_login_with_missing_username PASSED
test_app.py::TestLoginEndpoint::test_login_with_missing_password PASSED
test_app.py::TestLoginEndpoint::test_login_with_no_json_body PASSED
test_app.py::TestLoginEndpoint::test_login_with_invalid_json PASSED
test_app.py::TestLoginEndpoint::test_login_prevents_sql_injection_in_username PASSED
test_app.py::TestLoginEndpoint::test_login_with_special_characters_in_username PASSED
test_app.py::TestLoginEndpoint::test_login_with_unicode_characters PASSED
test_app.py::TestLoginEndpoint::test_login_token_format PASSED
test_app.py::TestLoginEndpoint::test_login_closes_database_connection PASSED
test_app.py::TestLoginEndpoint::test_login_with_very_long_username PASSED
test_app.py::TestLoginEndpoint::test_login_with_very_long_password PASSED

======================== 19 passed in 0.89s =================================
```

### Running Single Test
```bash
$ pytest test_app.py::TestLoginEndpoint::test_login_prevents_sql_injection_in_username -v

============================= test session starts ==============================
collected 1 item

test_app.py::TestLoginEndpoint::test_login_prevents_sql_injection_in_username PASSED

======================== 1 passed in 0.12s ==================================
```

### Test Failure Example (if security fix was reverted)
```bash
$ pytest test_app.py::TestLoginEndpoint::test_login_prevents_sql_injection_in_username -v

============================= test session starts ==============================
collected 1 item

test_app.py::TestLoginEndpoint::test_login_prevents_sql_injection_in_username FAILED

=================================== FAILURES ===================================
_____ TestLoginEndpoint.test_login_prevents_sql_injection_in_username _____

    def test_login_prevents_sql_injection_in_username(self, mock_get_db, client):
        """Test that SQL injection attempts are prevented (security test)."""
        ...
        # Should use parameterized query, not string concatenation
        mock_cursor.execute.assert_called_once_with(
            "SELECT password FROM users WHERE username=?", 
            (malicious_username,)
        )
>       assert response.status_code == 401
E       AssertionError: assert 200 == 401
E        +  where 200 = <Response 43 bytes [200 OK]>.status_code

test_app.py:198: AssertionError
======================== 1 failed in 0.15s ==================================
```

## Coverage Report (HTML)
After running with `--cov-report=html`, open `htmlcov/index.html` in a browser: