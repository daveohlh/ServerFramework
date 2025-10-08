# Request Context Management

## Overview
Context variable system for managing request-specific user information and timezone data throughout the application lifecycle using Python's contextvars for thread-safe request isolation.

## Core Components

### Context Variables (`RequestContext.py`)
Thread-safe context management using Python's contextvars module.

**Key Features:**
- Request-scoped user information storage
- Thread-safe context isolation
- Timezone-aware request handling
- Clean context lifecycle management

### Context Management

#### User Context Storage
Request-specific user information management.

**Context Variable:**
- **_request_user_context**: ContextVar storing user information dictionary

**Data Structure:**
```python
{
    "id": "user-id",
    "email": "user@example.com",
    "timezone": "America/New_York",
    # Additional user attributes
}
```

### API Functions

#### Context Setters
Functions for setting request context information.

**set_request_user(user_info: Dict[str, Any])**
- Sets current request's user information
- Accepts dictionary with user attributes
- Thread-safe context variable assignment

#### Context Getters
Functions for retrieving request context information.

**get_request_user() -> Optional[Dict[str, Any]]**
- Retrieves current request's user information
- Returns None if no context set
- Thread-safe context variable access

**get_user_timezone() -> str**
- Extracts user's timezone from context
- Returns user timezone if available
- Defaults to "UTC" if not specified

#### Context Cleanup
Functions for managing context lifecycle.

**clear_request_context()**
- Clears all request context data
- Resets context variables to None
- Used for cleanup between requests

### Integration Patterns

#### Middleware Integration
Integration with FastAPI middleware for automatic context management.

**Request Flow:**
1. Authentication middleware sets user context
2. Request handlers access user context
3. Context automatically isolated per request
4. Cleanup performed after request completion

#### Business Logic Integration
Access to user context throughout the application stack.

**Usage Pattern:**
```python
from lib.RequestContext import get_request_user, get_user_timezone

def business_operation():
    user = get_request_user()
    timezone = get_user_timezone()
    
    if user:
        # Use user context for operation
        user_id = user["id"]
        # ... business logic
```

#### GraphQL Integration
Context variable access within GraphQL resolvers.

**Features:**
- Automatic user context propagation
- Timezone-aware operations
- Clean separation from FastAPI request objects

### Context Isolation

#### Thread Safety
Built-in thread safety through contextvars.

**Features:**
- Per-request context isolation
- No cross-request contamination
- Automatic context inheritance in async operations
- Safe concurrent request handling

#### Memory Management
Efficient context variable memory management.

**Features:**
- Automatic cleanup after request completion
- No memory leaks from long-lived contexts
- Minimal overhead per request

### Usage Guidelines

#### Setting Context
**Best Practices:**
- Set context early in request lifecycle
- Include all necessary user information
- Validate user data before setting context

#### Accessing Context
**Best Practices:**
- Always check for None returns
- Handle missing context gracefully
- Use timezone-aware operations when available

#### Context Cleanup
**Best Practices:**
- Clear context in error handlers
- Ensure cleanup in all exit paths
- Monitor for context leaks in testing

### Error Handling

#### Missing Context
Graceful handling of missing or invalid context.

**Strategies:**
- Default values for missing information
- Optional context access patterns
- Clear error messages for debugging

#### Context Validation
Validation of context data integrity.

**Validation Points:**
- User information completeness
- Timezone validity
- Required field presence

### Testing Support

#### Test Context Management
Utilities for managing context in test environments.

**Features:**
- Mock context setup
- Test user creation
- Context isolation between tests
- Cleanup verification

### Performance Considerations

#### Context Variable Overhead
Minimal performance impact of context variables.

**Optimizations:**
- Lazy context evaluation
- Efficient memory usage
- Fast context access
- Minimal serialization overhead

## Best Practices

1. **Early Setup**: Set request context as early as possible in the request lifecycle
2. **Validation**: Validate user context data before setting
3. **Graceful Degradation**: Handle missing context gracefully with appropriate defaults
4. **Cleanup**: Ensure proper context cleanup in all code paths
5. **Testing**: Use isolated context for each test case
6. **Documentation**: Document context requirements for each operation
7. **Security**: Sanitize context data to prevent information leakage