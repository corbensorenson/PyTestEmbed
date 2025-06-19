"""
PyTestEmbed Django Example

Demonstrates PyTestEmbed usage in a Django web application
with models, views, and utilities.
"""

from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import json


class User(models.Model):
    """User model with PyTestEmbed tests and documentation."""
    
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_display_name(self):
        """Get user's display name."""
        return self.username.title()
    test:
        user = User(username="john_doe")
        user.get_display_name() == "John_Doe": "Username title case"
    doc:
        Returns the username in title case for display purposes.
        
        Returns:
            str: Username with first letter capitalized
    
    def is_email_verified(self):
        """Check if user's email is verified."""
        # In real app, this would check verification status
        return self.email and "@" in self.email
    test:
        user_with_email = User(email="test@example.com")
        user_with_email.is_email_verified() == True: "Valid email verified",
        user_without_email = User(email="")
        user_without_email.is_email_verified() == False: "Empty email not verified"
    doc:
        Checks if the user's email address is verified.
        
        Returns:
            bool: True if email is verified, False otherwise
    
    def get_profile_data(self):
        """Get user profile data for API responses."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "display_name": self.get_display_name(),
            "is_active": self.is_active,
            "email_verified": self.is_email_verified()
        }
    test:
        user = User(id=1, username="testuser", email="test@example.com", is_active=True)
        profile = user.get_profile_data()
        profile["username"] == "testuser": "Username in profile",
        profile["display_name"] == "Testuser": "Display name in profile",
        profile["email_verified"] == True: "Email verification in profile"
    doc:
        Returns a dictionary containing user profile information.
        
        Returns:
            dict: User profile data including:
                - id: User ID
                - username: Username
                - email: Email address
                - display_name: Formatted display name
                - is_active: Account status
                - email_verified: Email verification status


def validate_user_data(data):
    """Validate user registration data."""
    errors = []
    
    if not data.get("username"):
        errors.append("Username is required")
    elif len(data["username"]) < 3:
        errors.append("Username must be at least 3 characters")
    
    if not data.get("email"):
        errors.append("Email is required")
    elif "@" not in data["email"]:
        errors.append("Invalid email format")
    
    return errors
test:
    validate_user_data({"username": "john", "email": "john@example.com"}) == []: "Valid data",
    validate_user_data({}) == ["Username is required", "Email is required"]: "Missing data",
    validate_user_data({"username": "jo", "email": "invalid"}) == ["Username must be at least 3 characters", "Invalid email format"]: "Invalid data"
doc:
    Validates user registration data and returns any errors found.
    
    Args:
        data (dict): User data to validate containing:
            - username: Desired username
            - email: Email address
    
    Returns:
        list: List of error messages, empty if valid
    
    Examples:
        >>> validate_user_data({"username": "john", "email": "john@example.com"})
        []
        
        >>> validate_user_data({"username": "jo"})
        ["Username must be at least 3 characters", "Email is required"]


def create_user_view(request):
    """Django view for creating a new user."""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    errors = validate_user_data(data)
    if errors:
        return JsonResponse({"errors": errors}, status=400)
    
    try:
        user = User.objects.create(
            username=data["username"],
            email=data["email"]
        )
        return JsonResponse(user.get_profile_data(), status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
test:
    # Note: In real tests, you'd use Django's test framework
    # These are simplified examples for demonstration
    from django.test import RequestFactory
    factory = RequestFactory()
    
    # Valid request test
    valid_data = {"username": "newuser", "email": "new@example.com"}
    request = factory.post("/users/", json.dumps(valid_data), content_type="application/json")
    # response = create_user_view(request)
    # response.status_code == 201: "User created successfully"
    
    # Invalid data test
    invalid_data = {"username": "x"}
    request = factory.post("/users/", json.dumps(invalid_data), content_type="application/json")
    # response = create_user_view(request)
    # response.status_code == 400: "Validation errors returned"
doc:
    Django view for creating new user accounts via POST request.
    
    Accepts JSON data with username and email, validates the data,
    and creates a new user if validation passes.
    
    Args:
        request (HttpRequest): Django request object
    
    Returns:
        JsonResponse: JSON response with:
            - Success (201): User profile data
            - Validation error (400): List of validation errors
            - Server error (500): Error message
    
    Request Format:
        POST /users/
        Content-Type: application/json
        
        {
            "username": "desired_username",
            "email": "user@example.com"
        }
    
    Response Format:
        Success (201):
        {
            "id": 1,
            "username": "desired_username",
            "email": "user@example.com",
            "display_name": "Desired_Username",
            "is_active": true,
            "email_verified": true
        }
        
        Error (400):
        {
            "errors": ["Username is required", "Invalid email format"]
        }


def format_api_response(data, status="success", message=None):
    """Format consistent API responses."""
    response = {
        "status": status,
        "data": data
    }
    
    if message:
        response["message"] = message
    
    return response
test:
    format_api_response({"id": 1}, "success")["status"] == "success": "Success status",
    format_api_response({"id": 1}, "success")["data"]["id"] == 1: "Data included",
    format_api_response({}, "error", "Something went wrong")["message"] == "Something went wrong": "Error message included"
doc:
    Formats API responses in a consistent structure.
    
    Args:
        data (any): Response data to include
        status (str): Response status ('success', 'error', etc.)
        message (str, optional): Optional message to include
    
    Returns:
        dict: Formatted response with status, data, and optional message
    
    Examples:
        >>> format_api_response({"user_id": 1}, "success")
        {"status": "success", "data": {"user_id": 1}}
        
        >>> format_api_response({}, "error", "User not found")
        {"status": "error", "data": {}, "message": "User not found"}


def paginate_queryset(queryset, page=1, per_page=20):
    """Paginate a Django queryset."""
    total_count = queryset.count()
    start = (page - 1) * per_page
    end = start + per_page
    
    items = list(queryset[start:end])
    
    return {
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_count": total_count,
            "total_pages": (total_count + per_page - 1) // per_page,
            "has_next": end < total_count,
            "has_prev": page > 1
        }
    }
test:
    # Mock queryset for testing
    class MockQuerySet:
        def __init__(self, items):
            self.items = items
        def count(self):
            return len(self.items)
        def __getitem__(self, key):
            return self.items[key]
    
    mock_qs = MockQuerySet([1, 2, 3, 4, 5])
    result = paginate_queryset(mock_qs, page=1, per_page=2)
    result["items"] == [1, 2]: "First page items",
    result["pagination"]["total_count"] == 5: "Total count correct",
    result["pagination"]["has_next"] == True: "Has next page",
    result["pagination"]["has_prev"] == False: "No previous page"
doc:
    Paginates a Django queryset and returns items with pagination metadata.
    
    Args:
        queryset: Django queryset to paginate
        page (int): Page number (1-based)
        per_page (int): Items per page
    
    Returns:
        dict: Paginated result containing:
            - items: List of items for current page
            - pagination: Metadata about pagination
    
    Examples:
        >>> paginate_queryset(User.objects.all(), page=1, per_page=10)
        {
            "items": [...],
            "pagination": {
                "page": 1,
                "per_page": 10,
                "total_count": 25,
                "total_pages": 3,
                "has_next": True,
                "has_prev": False
            }
        }
