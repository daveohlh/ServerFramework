# Router Architecture & Implementation

This document covers the technical implementation details of the current RouterMixin system and the legacy AbstractEPRouter system, including the underlying `Pydantic2FastAPI` utilities and advanced router configuration options.

**IMPORTANT**: The system has migrated from `AbstractEPRouter` to `RouterMixin`. The current implementation uses BLL managers with `RouterMixin` inheritance to automatically generate routers.

## Current Architecture: RouterMixin

### RouterMixin Implementation

The `RouterMixin` class provides automatic router generation for BLL managers:

```python
class RouterMixin:
    """
    Mixin class that provides router generation functionality for BLL managers.
    
    BLL managers inherit from this class to get automatic FastAPI router generation
    with standard CRUD operations, authentication, and documentation.
    """
    
    # Router configuration ClassVars
    prefix: ClassVar[str] = "/v1/resource"
    tags: ClassVar[List[str]] = ["Resource Management"]
    auth_type: ClassVar[AuthType] = AuthType.JWT
    route_auth_overrides: ClassVar[Dict[str, AuthType]] = {}
    
    @classmethod
    def Router(cls, model_registry) -> APIRouter:
        """Generate FastAPI router from manager class."""
        # Implementation delegates to Pydantic2FastAPI utilities
```

## Legacy Architecture: AbstractEPRouter

### AbstractEPRouter Implementation

The legacy `AbstractEPRouter` inherits from FastAPI's `APIRouter` and provides automatic CRUD generation:

```python
class AbstractEPRouter(APIRouter, Generic[T]):
    """
    Abstract endpoint router implementing standard CRUD operations.
    
    Automatically generates REST endpoints following established patterns
    with consistent error handling, authentication, and documentation.
    """
```

### Current Components: RouterMixin

#### Router Configuration via ClassVars
```python
class ResourceManager(RouterMixin, AbstractLogicManager):
    # Router configuration
    prefix: ClassVar[str] = "/v1/resource"
    tags: ClassVar[List[str]] = ["Resource Management"]
    auth_type: ClassVar[AuthType] = AuthType.JWT
    route_auth_overrides: ClassVar[Dict[str, AuthType]] = {}
    routes_to_register: ClassVar[List[str]] = None  # None = all routes
    
    # Custom routes discovered via decorators
    custom_routes: ClassVar[List[Dict[str, Any]]] = []  # Auto-populated
```

### Legacy Components: AbstractEPRouter

#### Router Configuration
```python
@dataclass
class RouterConfig:
    prefix: str
    tags: List[str]
    manager_factory: Callable
    network_model_cls: Any
    manager_property: Optional[str] = None
    resource_name: Optional[str] = None
    example_overrides: Optional[Dict[str, Dict]] = None
    routes_to_register: Optional[List[str]] = None
    auth_type: AuthType = AuthType.JWT
    route_auth_overrides: Optional[Dict[str, AuthType]] = {}
    parent_router: Optional["AbstractEPRouter"] = None
    parent_param_name: Optional[str] = None
```

#### Route Registration Methods
```python
# Standard route registration methods
def _register_create_route(self) -> None
def _register_get_route(self) -> None
def _register_list_route(self) -> None
def _register_search_route(self) -> None
def _register_update_route(self) -> None
def _register_delete_route(self) -> None
def _register_batch_update_route(self) -> None
def _register_batch_delete_route(self) -> None

# Nested route registration methods
def _register_nested_create_route(self, parent_param_name: str) -> None
def _register_nested_list_route(self, parent_param_name: str) -> None
def _register_nested_search_route(self, parent_param_name: str) -> None
```

## System Entity Detection

The router automatically detects system entities through the network model:

```python
def _detect_system_entity_from_network_model(self, network_model_cls: Any) -> bool:
    """
    Detect if this is a system entity by checking the network model's Response class.
    
    Searches through:
    1. Inferred model class from NetworkModel name
    2. ResponseSingle class inheritance chain  
    3. Response class inheritance chain
    4. POST class inheritance chain
    """
```

### Detection Process
1. **Model Name Inference**: `{NetworkModel}` → `{Model}Model` in same module
2. **ResponseSingle Analysis**: Check inheritance chain for `is_system_entity`
3. **Response Analysis**: Fallback to Response class
4. **POST Analysis**: Final fallback to POST class

## Nested Router Creation

### Network Model Inference

When creating nested routers without explicit model classes:

```python
def _infer_network_model_class(
    self, child_resource_name: str, manager_property: str
) -> Optional[Any]:
    """
    Try to infer the network model class for a child resource.
    
    Searches in:
    1. logic.BLL_Auth.{ResourceName}NetworkModel
    2. logic.BLL_{ResourceName}.{ResourceName}NetworkModel
    """
```

### Manager Factory Creation

For nested resources, the parent manager factory is reused:

```python
def _create_child_manager_factory(
    self,
    child_resource_name: str,
    manager_property: str,
    child_network_model_cls: Any,
) -> Callable:
    """
    For nested routes, use the parent manager factory.
    The manager_property will be used by get_manager() to access the correct nested manager.
    """
```

## Router Tree Helper

### create_router_tree Function

For complex hierarchies with multiple nested resources:

```python
def create_router_tree(
    base_prefix: str,
    resource_name: str,
    tags: List[str],
    manager_factory: Callable,
    network_model_cls: Any,
    nested_resources: Optional[List[Dict[str, Any]]] = None,
    auth_type: AuthType = AuthType.JWT,
    example_overrides: Optional[Dict[str, Dict]] = None,
) -> Dict[str, AbstractEPRouter]:
```

### Nested Resource Configuration

```python
nested_resources = [
    {
        "name": "invitation",
        "manager_property": "invitations",  # Optional, defaults to parent.child
        "network_model_cls": InvitationNetworkModel,  # Required
        "tags": ["Team Management"],  # Optional, inherits from parent
        "auth_type": AuthType.JWT,  # Optional, inherits from parent
        "example_overrides": {...},  # Optional
        "create_mirror": True,  # Creates standalone /v1/invitation routes
    }
]
```

## Custom Route Integration

### with_custom_route Method

```python
def with_custom_route(
    self,
    method: str,
    path: str,
    endpoint: Callable,
    summary: str,
    description: str,
    response_model: Optional[Type] = None,
    status_code: int = status.HTTP_200_OK,
    responses: Optional[Dict] = None,
    dependencies: List = None,
    **kwargs,
) -> "AbstractEPRouter":
```

### Automatic Dependency Injection

The method automatically adds authentication dependencies:

```python
# Add auth dependency if not explicitly provided
if dependencies is None:
    dependencies = []
    auth_dep = get_auth_dependency(self.auth_type)
    if auth_dep:
        dependencies.append(auth_dep)
```

## Mirror Router Implementation

### create_mirror_router Method

Creates standalone routes for nested resources:

```python
def create_mirror_router(
    self,
    new_prefix: str,
    routes_to_register: Optional[List[str]] = None,
    network_model_cls: Optional[Any] = None,
) -> "AbstractEPRouter":
    """
    Create a mirror of this router with a standalone prefix.
    
    Example:
    - Original: /v1/team/{team_id}/invitation
    - Mirror: /v1/invitation
    """
```

## Request/Response Processing

### Body Data Extraction

```python
def _extract_body_data(
    self, body: Any, attribute_name: Optional[str] = None
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Extract data from a request body object."""
    if not attribute_name:
        attribute_name = self.resource_name
    
    return extract_body_data(body, attribute_name, self.resource_name_plural)
```

### Manager Access

```python
def get_manager(self, manager: Any) -> Any:
    """Get the appropriate manager (base or nested property)."""
    return get_manager(manager, self.manager_property)
```

## Error Handling Integration

### Resource Operation Errors

```python
def _handle_resource_operation_error(self, err: Exception) -> None:
    """Handle resource operation errors and raise appropriate HTTP exceptions."""
    handle_resource_operation_error(err)
```

### Standard Exception Mapping

- `ResourceNotFoundError` → 404 Not Found
- `ResourceConflictError` → 409 Conflict  
- `InvalidRequestError` → 400 Bad Request
- `PermissionDeniedError` → 403 Forbidden
- `AuthenticationError` → 401 Unauthorized

## Example Integration

### Example Generation

```python
def _generate_examples(
    self, overrides: Optional[Dict[str, Dict]] = None
) -> Dict[str, Dict[str, Any]]:
    """Generate examples for documentation with optional overrides."""
    examples = ExampleGenerator.generate_operation_examples(
        self.network_model_cls, self.resource_name
    )
    
    # Apply overrides if provided
    if overrides:
        for op_name, override in overrides.items():
            if op_name in examples:
                examples[op_name].update(override)
    
    return examples
```

### Example Response Creation

```python
def _create_example_response(self, operation: str) -> Optional[Dict[str, Any]]:
    """Create an example response for documentation."""
    return create_example_response(self.examples, operation)
```

## Advanced Configuration

### Route Auth Override Inheritance

System entities automatically inherit auth overrides:

```python
if is_system_entity:
    route_auth_overrides = {
        "create": AuthType.API_KEY,
        "update": AuthType.API_KEY,
        "delete": AuthType.API_KEY,
        "batch_update": AuthType.API_KEY,
        "batch_delete": AuthType.API_KEY,
        **route_auth_overrides,  # User overrides take precedence
    }
```

### Resource Name Derivation

```python
# Derive resource names if not provided
if not resource_name:
    resource_name = prefix.split("/")[-1]
    resource_name = stringcase.snakecase(resource_name)

self.resource_name = resource_name
self.resource_name_plural = inflection.plural(resource_name)
```

## Integration with Pydantic2FastAPI

The router delegates core functionality to the `Pydantic2FastAPI` library:

```python
# Route registration functions from Pydantic2FastAPI:
register_create_route(...)
register_get_route(...)
register_list_route(...)
register_search_route(...)
register_update_route(...)
register_delete_route(...)
register_batch_update_route(...)
register_batch_delete_route(...)

# Nested route registration:
register_nested_create_route(...)
register_nested_list_route(...)
register_nested_search_route(...)
```

## Performance Considerations

### Router Initialization

1. **System Entity Detection**: One-time check during initialization
2. **Example Generation**: Cached results for repeated use
3. **Route Registration**: Only registers selected routes
4. **Manager Factory**: Lightweight factory function calls

### Runtime Performance

- **Authentication**: Dependency injection with caching
- **Body Processing**: Efficient data extraction
- **Error Handling**: Fast exception mapping
- **Documentation**: Pre-generated examples

## Best Practices

### Router Design

1. **Single Responsibility**: One router per resource type
2. **Consistent Naming**: Follow resource naming conventions
3. **Manager Delegation**: Keep logic in managers, not routers
4. **Authentication Strategy**: Use appropriate auth types per operation

### Implementation Guidelines

1. **System Detection**: Let auto-detection handle system entities
2. **Nested Resources**: Use explicit network model classes when possible
3. **Custom Routes**: Use `with_custom_route` for consistency
4. **Error Handling**: Raise manager exceptions for automatic conversion
5. **Testing**: Use AbstractEPTest for comprehensive coverage