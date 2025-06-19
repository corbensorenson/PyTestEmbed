# PyTestEmbed Test Syntax Guide

PyTestEmbed supports multiple test syntax formats to make testing intuitive and flexible. This guide covers all supported test arrangements from simple to advanced.

## Basic Test Syntax Rules

### Core Format
```python
test:
    expression == expected: "description"
```

**Key Requirements:**
- Test content must be indented 4 spaces from the `test:` line
- Tests must include comparison operators (`==`, `!=`, `<`, `>`, etc.)
- Tests must include expected results and descriptions
- Multiple tests can be in one block
- Trailing commas are optional (especially for the last test)

## 1. Simple Function Tests

### Basic Function Test
```python
def add(x, y):
    return x + y
test:
    add(2, 3) == 5: "basic addition",
    add(0, 0) == 0: "zero addition",
    add(-1, 1) == 0: "negative addition"
```

### Single Test (No Comma Required)
```python
def multiply(x, y):
    return x * y
test:
    multiply(3, 4) == 12: "simple multiplication"
```

## 2. Class Method Tests

### Method-Level Tests (Inside Class)
```python
class Calculator:
    def add(self, x, y):
        return x + y
    test:
        add(2, 3) == 5: "method addition",
        add(10, -5) == 5: "mixed numbers"
    
    def multiply(self, x, y):
        return x * y
    test:
        multiply(4, 5) == 20: "method multiplication"
```

### Class-Level Tests (After Class Definition)
```python
class MathUtils:
    def square(self, x):
        return x * x
    
    def cube(self, x):
        return x * x * x

test:
    square(3) * cube(2) == 72: "combined operations",
    a = square(4)
    b = cube(3)
    a + b == 43: "stored results test"
```

## 3. Multi-Statement Tests

### Setup and Assertion
```python
def process_data(data):
    return [x * 2 for x in data]
test:
    result = process_data([1, 2, 3])
    len(result) == 3: "correct length",
    result[0] == 2: "first element doubled",
    result == [2, 4, 6]: "all elements doubled"
```

### Complex Setup
```python
class DataProcessor:
    def __init__(self):
        self.data = []
    
    def add_item(self, item):
        self.data.append(item)
    
    def get_sum(self):
        return sum(self.data)

test:
    processor = DataProcessor()
    processor.add_item(10)
    processor.add_item(20)
    processor.get_sum() == 30: "sum calculation"
```

## 4. Global/Module-Level Tests

### Testing Module Functions
```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

test:
    factorial(5) == 120: "factorial calculation",
    fibonacci(6) == 8: "fibonacci sequence",
    factorial(0) == 1: "edge case zero"
```

## 5. Advanced Test Patterns

### Exception Testing
```python
def divide(x, y):
    if y == 0:
        raise ValueError("Cannot divide by zero")
    return x / y
test:
    divide(10, 2) == 5.0: "normal division",
    # Note: Exception testing syntax to be implemented
```

### Property Testing
```python
class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height
    
    @property
    def area(self):
        return self.width * self.height

test:
    rect = Rectangle(5, 3)
    rect.area == 15: "area calculation",
    rect.width == 5: "width property",
    rect.height == 3: "height property"
```

### List and Dictionary Testing
```python
def create_user_dict(name, age):
    return {"name": name, "age": age, "active": True}

test:
    user = create_user_dict("Alice", 30)
    user["name"] == "Alice": "name field",
    user["age"] == 30: "age field",
    len(user) == 3: "correct field count"
```

## 6. Test Organization Patterns

### Grouped Related Tests
```python
class StringUtils:
    def reverse(self, s):
        return s[::-1]
    test:
        reverse("hello") == "olleh": "basic reverse",
        reverse("") == "": "empty string",
        reverse("a") == "a": "single character"
    
    def capitalize_words(self, s):
        return " ".join(word.capitalize() for word in s.split())
    test:
        capitalize_words("hello world") == "Hello World": "basic capitalization",
        capitalize_words("") == "": "empty string case"
```

### Mixed Test Levels
```python
class Calculator:
    def add(self, x, y):
        return x + y
    test:
        add(1, 1) == 2: "simple addition"
    
    def subtract(self, x, y):
        return x - y
    test:
        subtract(5, 3) == 2: "simple subtraction"

# Class-level integration tests
test:
    calc = Calculator()
    result1 = calc.add(10, 5)
    result2 = calc.subtract(result1, 3)
    result2 == 12: "chained operations"

# Global utility tests
def is_even(n):
    return n % 2 == 0

test:
    is_even(4) == True: "even number",
    is_even(3) == False: "odd number"
```

## 7. Best Practices

### Descriptive Test Messages
```python
def validate_email(email):
    return "@" in email and "." in email

test:
    validate_email("user@example.com") == True: "valid email format",
    validate_email("invalid-email") == False: "missing @ symbol",
    validate_email("user@domain") == False: "missing domain extension"
```

### Edge Case Testing
```python
def safe_divide(x, y):
    return x / y if y != 0 else 0

test:
    safe_divide(10, 2) == 5.0: "normal division",
    safe_divide(10, 0) == 0: "division by zero handled",
    safe_divide(0, 5) == 0.0: "zero dividend"
```

### State Testing
```python
class Counter:
    def __init__(self):
        self.count = 0
    
    def increment(self):
        self.count += 1
    
    def reset(self):
        self.count = 0

test:
    counter = Counter()
    counter.count == 0: "initial state",
    counter.increment()
    counter.count == 1: "after increment",
    counter.increment()
    counter.count == 2: "after second increment",
    counter.reset()
    counter.count == 0: "after reset"
```

## Syntax Summary

| Test Level | `test:` Indentation | Content Indentation | Example |
|------------|-------------------|-------------------|---------|
| Function | 0 spaces | 4 spaces | Global function tests |
| Method | 4 spaces | 8 spaces | Tests inside class methods |
| Class | 0 spaces | 4 spaces | Tests after class definition |
| Global | 0 spaces | 4 spaces | Module-level tests |

## Coming Soon

- Exception testing syntax
- Parameterized tests
- Async function testing
- Mock and fixture support
- Performance testing syntax
