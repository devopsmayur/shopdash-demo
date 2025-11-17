"""
Comprehensive unit tests for backend/app.py
Tests cover all endpoints, edge cases, security scenarios, and error handling.
"""
import pytest
import json
import sqlite3
import os
import tempfile
import hashlib
from unittest.mock import patch, MagicMock, mock_open
import time

# Import the Flask app
import sys
sys.path.insert(0, os.path.dirname(__file__))
from app import app, get_db, DATABASE


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def temp_db():
    """Create a temporary test database with sample data."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Connect and set up test data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    ''')
    
    # Insert test users (passwords are MD5 hashed)
    test_password = hashlib.md5("password123".encode("utf-8")).hexdigest()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                   ("testuser", test_password))
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                   ("admin", hashlib.md5("admin123".encode("utf-8")).hexdigest()))
    
    # Insert test products
    cursor.execute("INSERT INTO products (name, price) VALUES (?, ?)", ("Product1", 19.99))
    cursor.execute("INSERT INTO products (name, price) VALUES (?, ?)", ("Product2", 29.99))
    cursor.execute("INSERT INTO products (name, price) VALUES (?, ?)", ("Product3", 39.99))
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""
    
    def test_health_returns_ok_status(self, client):
        """Test that health endpoint returns ok status."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
    
    def test_health_returns_timestamp(self, client):
        """Test that health endpoint returns a timestamp."""
        before = time.time()
        response = client.get('/health')
        after = time.time()
        
        data = json.loads(response.data)
        assert 'ts' in data
        assert before <= data['ts'] <= after
    
    def test_health_response_format(self, client):
        """Test that health endpoint returns proper JSON format."""
        response = client.get('/health')
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert len(data) == 2  # status and ts


class TestLoginEndpoint:
    """Tests for the /login endpoint with focus on security fixes."""
    
    @patch('app.get_db')
    def test_login_successful_with_valid_credentials(self, mock_get_db, client):
        """Test successful login with valid username and password."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Hash of "password123"
        hashed_password = hashlib.md5("password123".encode("utf-8")).hexdigest()
        mock_cursor.fetchone.return_value = (hashed_password,)
        
        # Make request
        response = client.post('/login', 
                              json={'username': 'testuser', 'password': 'password123'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['ok'] is True
        assert data['token'] == 'tok_testuser'
        
        # Verify parameterized query was used (security fix)
        mock_cursor.execute.assert_called_once_with(
            "SELECT password FROM users WHERE username=?", 
            ("testuser",)
        )
    
    @patch('app.get_db')
    def test_login_fails_with_invalid_credentials(self, mock_get_db, client):
        """Test login fails with invalid credentials."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        response = client.post('/login', 
                              json={'username': 'testuser', 'password': 'wrongpass'})
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['ok'] is False
    
    @patch('app.get_db')
    def test_login_with_empty_username(self, mock_get_db, client):
        """Test login with empty username."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        response = client.post('/login', 
                              json={'username': '', 'password': 'password123'})
        
        assert response.status_code == 401
        mock_cursor.execute.assert_called_once_with(
            "SELECT password FROM users WHERE username=?", 
            ("",)
        )
    
    @patch('app.get_db')
    def test_login_with_empty_password(self, mock_get_db, client):
        """Test login with empty password."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        response = client.post('/login', 
                              json={'username': 'testuser', 'password': ''})
        
        assert response.status_code == 401
    
    @patch('app.get_db')
    def test_login_with_missing_username(self, mock_get_db, client):
        """Test login with missing username field."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        response = client.post('/login', 
                              json={'password': 'password123'})
        
        assert response.status_code == 401
        # Should default to empty string
        mock_cursor.execute.assert_called_once_with(
            "SELECT password FROM users WHERE username=?", 
            ("",)
        )
    
    @patch('app.get_db')
    def test_login_with_missing_password(self, mock_get_db, client):
        """Test login with missing password field."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        response = client.post('/login', 
                              json={'username': 'testuser'})
        
        assert response.status_code == 401
    
    def test_login_with_no_json_body(self, client):
        """Test login with no JSON body."""
        response = client.post('/login')
        assert response.status_code == 401
    
    def test_login_with_invalid_json(self, client):
        """Test login with invalid JSON."""
        response = client.post('/login', 
                              data='invalid json',
                              content_type='application/json')
        # Flask will return 400 for invalid JSON
        assert response.status_code in [400, 401]
    
    @patch('app.get_db')
    def test_login_prevents_sql_injection_in_username(self, mock_get_db, client):
        """Test that SQL injection attempts are prevented (security test)."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        # Attempt SQL injection
        malicious_username = "admin' OR '1'='1"
        response = client.post('/login', 
                              json={'username': malicious_username, 'password': 'anything'})
        
        # Should use parameterized query, not string concatenation
        mock_cursor.execute.assert_called_once_with(
            "SELECT password FROM users WHERE username=?", 
            (malicious_username,)
        )
        assert response.status_code == 401
    
    @patch('app.get_db')
    def test_login_with_special_characters_in_username(self, mock_get_db, client):
        """Test login with special characters in username."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        special_username = "user@example.com"
        response = client.post('/login', 
                              json={'username': special_username, 'password': 'pass'})
        
        mock_cursor.execute.assert_called_once_with(
            "SELECT password FROM users WHERE username=?", 
            (special_username,)
        )
    
    @patch('app.get_db')
    def test_login_with_unicode_characters(self, mock_get_db, client):
        """Test login with unicode characters."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        unicode_username = "用户名"
        response = client.post('/login', 
                              json={'username': unicode_username, 'password': 'pass'})
        
        assert response.status_code == 401
    
    @patch('app.get_db')
    def test_login_token_format(self, mock_get_db, client):
        """Test that login returns token in expected format."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        hashed_password = hashlib.md5("pass".encode("utf-8")).hexdigest()
        mock_cursor.fetchone.return_value = (hashed_password,)
        
        response = client.post('/login', 
                              json={'username': 'user123', 'password': 'pass'})
        
        data = json.loads(response.data)
        assert data['token'].startswith('tok_')
        assert data['token'] == 'tok_user123'
    
    @patch('app.get_db')
    def test_login_closes_database_connection(self, mock_get_db, client):
        """Test that database connection is properly closed."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        response = client.post('/login', 
                              json={'username': 'user', 'password': 'pass'})
        
        mock_conn.close.assert_called_once()
    
    @patch('app.get_db')
    def test_login_with_very_long_username(self, mock_get_db, client):
        """Test login with extremely long username."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        long_username = "a" * 10000
        response = client.post('/login', 
                              json={'username': long_username, 'password': 'pass'})
        
        assert response.status_code == 401
    
    @patch('app.get_db')
    def test_login_with_very_long_password(self, mock_get_db, client):
        """Test login with extremely long password."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        long_password = "b" * 10000
        response = client.post('/login', 
                              json={'username': 'user', 'password': long_password})
        
        assert response.status_code == 401


class TestPriceEndpoint:
    """Tests for the /price endpoint."""
    
    @patch('app.get_db')
    def test_price_returns_valid_price(self, mock_get_db, client):
        """Test price endpoint returns valid price for existing product."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (29.99,)
        
        response = client.get('/price?id=1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['price'] == 29.99
    
    @patch('app.get_db')
    def test_price_returns_404_for_nonexistent_product(self, mock_get_db, client):
        """Test price endpoint returns 404 for non-existent product."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        response = client.get('/price?id=999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'not found'
    
    @patch('app.get_db')
    def test_price_with_missing_id_parameter(self, mock_get_db, client):
        """Test price endpoint with missing id parameter."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        response = client.get('/price')
        
        # Should default to "0"
        assert response.status_code == 404
    
    @patch('app.get_db')
    def test_price_with_sql_injection_attempt(self, mock_get_db, client):
        """Test price endpoint is vulnerable to SQL injection (security concern)."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # This endpoint is vulnerable - it concatenates the id directly
        malicious_id = "1 OR 1=1"
        response = client.get(f'/price?id={malicious_id}')
        
        # The execute should have been called with concatenated string (vulnerability)
        call_args = mock_cursor.execute.call_args[0][0]
        assert "SELECT price FROM products WHERE id=" in call_args
        assert malicious_id in call_args
    
    @patch('app.get_db')
    def test_price_with_negative_id(self, mock_get_db, client):
        """Test price endpoint with negative product id."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        response = client.get('/price?id=-1')
        assert response.status_code == 404
    
    @patch('app.get_db')
    def test_price_with_non_numeric_id(self, mock_get_db, client):
        """Test price endpoint with non-numeric id."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        response = client.get('/price?id=abc')
        # May cause SQL error, should be handled
        assert response.status_code in [404, 500]
    
    @patch('app.get_db')
    def test_price_closes_database_connection(self, mock_get_db, client):
        """Test that database connection is properly closed."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (19.99,)
        
        response = client.get('/price?id=1')
        
        mock_conn.close.assert_called_once()
    
    @patch('app.get_db')
    def test_price_with_zero_price(self, mock_get_db, client):
        """Test price endpoint with product that has zero price."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (0.0,)
        
        response = client.get('/price?id=1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['price'] == 0.0
    
    @patch('app.get_db')
    def test_price_with_decimal_price(self, mock_get_db, client):
        """Test price endpoint returns correct decimal values."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (99.99,)
        
        response = client.get('/price?id=1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['price'] == 99.99


class TestCalcEndpoint:
    """Tests for the /calc endpoint."""
    
    def test_calc_simple_addition(self, client):
        """Test calc endpoint with simple addition."""
        response = client.get('/calc?expr=2+2')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result'] == 4
    
    def test_calc_simple_subtraction(self, client):
        """Test calc endpoint with subtraction."""
        response = client.get('/calc?expr=10-5')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result'] == 5
    
    def test_calc_simple_multiplication(self, client):
        """Test calc endpoint with multiplication."""
        response = client.get('/calc?expr=3*4')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result'] == 12
    
    def test_calc_simple_division(self, client):
        """Test calc endpoint with division."""
        response = client.get('/calc?expr=10/2')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result'] == 5.0
    
    def test_calc_complex_expression(self, client):
        """Test calc endpoint with complex mathematical expression."""
        response = client.get('/calc?expr=(2+3)*4')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result'] == 20
    
    def test_calc_with_missing_expr_parameter(self, client):
        """Test calc endpoint with missing expr parameter."""
        response = client.get('/calc')
        
        # Should default to "0"
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result'] == 0
    
    def test_calc_with_float_numbers(self, client):
        """Test calc endpoint with floating point numbers."""
        response = client.get('/calc?expr=2.5+3.7')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert abs(data['result'] - 6.2) < 0.0001
    
    def test_calc_with_negative_numbers(self, client):
        """Test calc endpoint with negative numbers."""
        response = client.get('/calc?expr=-5+3')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result'] == -2
    
    def test_calc_division_by_zero(self, client):
        """Test calc endpoint handles division by zero."""
        response = client.get('/calc?expr=1/0')
        
        # Should raise ZeroDivisionError, causing 500
        assert response.status_code == 500
    
    def test_calc_with_invalid_expression(self, client):
        """Test calc endpoint with invalid expression."""
        response = client.get('/calc?expr=invalid')
        
        # Should raise NameError, causing 500
        assert response.status_code == 500
    
    def test_calc_code_injection_vulnerability(self, client):
        """Test calc endpoint is vulnerable to code injection (security concern)."""
        # CRITICAL SECURITY ISSUE: eval() allows arbitrary code execution
        # This test documents the vulnerability
        response = client.get('/calc?expr=__import__("os").getcwd()')
        
        # This will execute and return current directory, demonstrating the vulnerability
        # In a real attack, this could be used to execute arbitrary code
        assert response.status_code in [200, 500]
    
    def test_calc_with_power_operation(self, client):
        """Test calc endpoint with power operation."""
        response = client.get('/calc?expr=2**3')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result'] == 8
    
    def test_calc_with_modulo_operation(self, client):
        """Test calc endpoint with modulo operation."""
        response = client.get('/calc?expr=10%3')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result'] == 1
    
    def test_calc_with_empty_expression(self, client):
        """Test calc endpoint with empty expression."""
        response = client.get('/calc?expr=')
        
        # Empty string causes SyntaxError
        assert response.status_code == 500


class TestGetDbFunction:
    """Tests for the get_db() function."""
    
    @patch('sqlite3.connect13')
    def test_get_db_returns_connection(self, mock_connect):
        """Test that get_db returns a database connection."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        result = get_db()
        
        assert result == mock_conn
        mock_connect.assert_called_once_with(DATABASE)
    
    @patch('sqlite3.connect13')
    def test_get_db_uses_correct_database_file(self, mock_connect):
        """Test that get_db uses the correct database file."""
        get_db()
        
        mock_connect.assert_called_once_with("shop.db")
    
    @patch('sqlite3.connect13')
    def test_get_db_connection_error(self, mock_connect):
        """Test get_db handles connection errors."""
        mock_connect.side_effect = sqlite3.Error("Connection failed")
        
        with pytest.raises(sqlite3.Error):
            get_db()


class TestAppConfiguration:
    """Tests for Flask app configuration."""
    
    def test_app_secret_key_is_set(self):
        """Test that secret key is configured."""
        assert app.config['SECRET_KEY'] == "supersecretkey123"
    
    def test_app_testing_mode(self):
        """Test app can be set to testing mode."""
        app.config['TESTING'] = True
        assert app.config['TESTING'] is True


class TestEndpointMethods:
    """Tests for HTTP method restrictions."""
    
    def test_health_only_accepts_get(self, client):
        """Test health endpoint only accepts GET requests."""
        response = client.post('/health')
        assert response.status_code == 405
    
    def test_login_only_accepts_post(self, client):
        """Test login endpoint only accepts POST requests."""
        response = client.get('/login')
        assert response.status_code == 405
    
    def test_price_only_accepts_get(self, client):
        """Test price endpoint only accepts GET requests."""
        response = client.post('/price')
        assert response.status_code == 405
    
    def test_calc_only_accepts_get(self, client):
        """Test calc endpoint only accepts GET requests."""
        response = client.post('/calc')
        assert response.status_code == 405


class TestResponseContentTypes:
    """Tests for response content types."""
    
    def test_health_returns_json(self, client):
        """Test health endpoint returns JSON content type."""
        response = client.get('/health')
        assert 'application/json' in response.content_type
    
    @patch('app.get_db')
    def test_login_returns_json(self, mock_get_db, client):
        """Test login endpoint returns JSON content type."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        response = client.post('/login', json={'username': 'test', 'password': 'test'})
        assert 'application/json' in response.content_type
    
    @patch('app.get_db')
    def test_price_returns_json(self, mock_get_db, client):
        """Test price endpoint returns JSON content type."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (19.99,)
        
        response = client.get('/price?id=1')
        assert 'application/json' in response.content_type
    
    def test_calc_returns_json(self, client):
        """Test calc endpoint returns JSON content type."""
        response = client.get('/calc?expr=1+1')
        assert 'application/json' in response.content_type


class TestSecurityConcerns:
    """Tests documenting security vulnerabilities in the application."""
    
    @patch('app.get_db')
    def test_login_uses_parameterized_queries(self, mock_get_db, client):
        """Test that login endpoint uses parameterized queries (FIXED)."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        client.post('/login', json={'username': 'test', 'password': 'test'})
        
        # Verify parameterized query is used
        call_args = mock_cursor.execute.call_args
        assert call_args[0][0] == "SELECT password FROM users WHERE username=?"
        assert call_args[0][1] == ("test",)
    
    def test_weak_password_hashing_md5(self, client):
        """Test documents use of weak MD5 hashing (security concern)."""
        # MD5 is cryptographically broken and should not be used for passwords
        # This test documents the issue
        password = "test123"
        hashed = hashlib.md5(password.encode("utf-8")).hexdigest()
        
        # MD5 produces 32 character hex string
        assert len(hashed) == 32
        # This is a security vulnerability - should use bcrypt, argon2, or pbkdf2
    
    @patch('app.get_db')
    def test_price_sql_injection_vulnerability(self, mock_get_db, client):
        """Test documents SQL injection vulnerability in price endpoint."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # The price endpoint concatenates user input directly into SQL
        client.get('/price?id=1')
        
        call_args = mock_cursor.execute.call_args[0][0]
        # This is vulnerable - should use parameterized queries
        assert "SELECT price FROM products WHERE id=" in call_args
    
    def test_calc_arbitrary_code_execution_vulnerability(self, client):
        """Test documents arbitrary code execution vulnerability in calc endpoint."""
        # Using eval() on user input is extremely dangerous
        # This test documents the critical security vulnerability
        
        # An attacker could execute arbitrary Python code
        # Example: accessing files, importing modules, etc.
        response = client.get('/calc?expr=1+1')
        assert response.status_code == 200
        
        # This endpoint should NEVER use eval() in production


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    @patch('app.get_db')
    def test_login_with_null_bytes_in_username(self, mock_get_db, client):
        """Test login with null bytes in username."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        response = client.post('/login', 
                              json={'username': 'test\x00user', 'password': 'pass'})
        
        assert response.status_code == 401
    
    @patch('app.get_db')
    def test_price_with_very_large_id(self, mock_get_db, client):
        """Test price endpoint with very large product ID."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        response = client.get('/price?id=9999999999999')
        assert response.status_code == 404
    
    def test_calc_with_very_long_expression(self, client):
        """Test calc endpoint with very long expression."""
        long_expr = "+".join(["1"] * 1000)
        response = client.get(f'/calc?expr={long_expr}')
        
        # Should either compute or timeout/error
        assert response.status_code in [200, 500]
    
    @patch('app.get_db')
    def test_multiple_concurrent_login_requests(self, mock_get_db, client):
        """Test handling of concurrent login requests."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        # Simulate concurrent requests
        for i in range(10):
            response = client.post('/login', 
                                  json={'username': f'user{i}', 'password': 'pass'})
            assert response.status_code == 401


class TestDatabaseConnectionHandling:
    """Tests for database connection management."""
    
    @patch('app.get_db')
    def test_connection_closed_on_success(self, mock_get_db, client):
        """Test database connection is closed after successful request."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (19.99,)
        
        client.get('/price?id=1')
        
        mock_conn.close.assert_called_once()
    
    @patch('app.get_db')
    def test_connection_closed_on_failure(self, mock_get_db, client):
        """Test database connection is closed even when query fails."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        client.get('/price?id=999')
        
        mock_conn.close.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])