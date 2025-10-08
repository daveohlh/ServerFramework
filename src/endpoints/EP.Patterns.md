# Endpoint Layer Patterns & Usage Guide

This document covers common patterns and best practices for using the endpoint layer abstractions in real-world scenarios.

**IMPORTANT**: This system has migrated from the legacy `AbstractEPRouter` pattern to a new `RouterMixin` approach. The current implementation automatically generates routers from BLL managers using the `RouterMixin` class.

## Quick Start (Current Pattern)

### Basic Manager with RouterMixin

```python
from lib.Pydantic2FastAPI import RouterMixin, AuthType
from logic.AbstractLogicManager import AbstractLogicManager
from typing import ClassVar, List, Dict

class ResourceManager(RouterMixin, AbstractLogicManager):
    # Router configuration via ClassVars
    prefix: ClassVar[str] = "/v1/resource"
    tags: ClassVar[List[str]] = ["Resource Management"]
    auth_type: ClassVar[AuthType] = AuthType.JWT
    route_auth_overrides: ClassVar[Dict[str, AuthType]] = {}
    
    # Standard CRUD methods implemented here
    def create(self, **kwargs): ...
    def get(self, id: str, **kwargs): ...
    def list(self, **kwargs): ...
    # etc.
    
    # Router automatically available via .Router(model_registry) class method
```

### Legacy Basic Router Setup (Deprecated)

```python
# Legacy pattern - still functional but not used in main app
from endpoints.AbstractEndpointRouter import AbstractEPRouter
from lib.Pydantic2FastAPI import AuthType

resource_router = AbstractEPRouter(
    model_registry=model_registry,
    prefix="/v1/resource",
    tags=["Resource Management"],
    manager_factory=get_resource_manager,
    manager_cls=ResourceManager,
    resource_name="resource",
    auth_type=AuthType.JWT,
)
```

### System Entity Setup (Current)

```python
# System entities automatically use API key auth for writes
class ExtensionManager(RouterMixin, AbstractLogicManager):
    prefix: ClassVar[str] = "/v1/extension"
    tags: ClassVar[List[str]] = ["Extensions"]
    auth_type: ClassVar[AuthType] = AuthType.JWT  # Default for reads
    
    # System entities auto-detected via BaseModel.is_system_entity attribute
    # Automatically applies API key auth for writes: create, update, delete, batch_*
```

### Legacy System Entity Setup

```python
# Legacy pattern - still functional
system_router = AbstractEPRouter(
    model_registry=model_registry,
    prefix="/v1/extension",
    tags=["Extensions"],
    manager_factory=get_extension_manager,
    manager_cls=ExtensionManager,
    # System entities auto-detected via manager_cls.BaseModel.is_system_entity
)
```

## Authentication Patterns

### Authentication Types

- **JWT**: Default for user operations (`AuthType.JWT`)
- **API Key**: System operations (`AuthType.API_KEY`)  
- **Basic**: Login only (`AuthType.BASIC`)
- **None**: Public endpoints (`AuthType.NONE`)

### Route-Specific Authentication (Current)

```python
class ResourceManager(RouterMixin, AbstractLogicManager):
    auth_type: ClassVar[AuthType] = AuthType.JWT  # Default
    route_auth_overrides: ClassVar[Dict[str, AuthType]] = {
        "create": AuthType.API_KEY,  # Override specific operations
        "update": AuthType.API_KEY,
        "delete": AuthType.API_KEY,
    }
```

### Legacy Route-Specific Authentication

```python
router = AbstractEPRouter(
    auth_type=AuthType.JWT,  # Default
    route_auth_overrides={
        "create": AuthType.API_KEY,  # Override specific operations
        "update": AuthType.API_KEY,
        "delete": AuthType.API_KEY,
    }
)
```

### System Entity Auto-Configuration

Entities with `is_system_entity=True` automatically get API key authentication for write operations:

```python
# Automatically applied:
route_auth_overrides = {
    "create": AuthType.API_KEY,
    "update": AuthType.API_KEY,
    "delete": AuthType.API_KEY,
    "batch_update": AuthType.API_KEY,
    "batch_delete": AuthType.API_KEY,
}
```

## Standard Routes

AbstractEPRouter automatically generates:

| Route        | Method | Path                  | Description           |
|--------------|--------|-----------------------|-----------------------|
| create       | POST   | `/v1/resource`        | Create resource(s)    |
| get          | GET    | `/v1/resource/{id}`   | Get single resource   |
| list         | GET    | `/v1/resource`        | List with filters     |
| search       | POST   | `/v1/resource/search` | Complex search        |
| update       | PUT    | `/v1/resource/{id}`   | Update single         |
| delete       | DELETE | `/v1/resource/{id}`   | Delete single         |
| batch_update | PUT    | `/v1/resource`        | Update multiple       |
| batch_delete | DELETE | `/v1/resource`        | Delete multiple       |

### Route Selection

```python
router = AbstractEPRouter(
    routes_to_register=["get", "list", "search"],  # Subset only
)
```

## Nested Resources

### Parent-Child Relationships

```python
# Parent router
team_router = AbstractEPRouter(
    prefix="/v1/team",
    manager_factory=get_team_manager,
    network_model_cls=TeamNetworkModel,
)

# Nested child router
invitation_router = team_router.create_nested_router(
    parent_prefix="/v1/team",
    parent_param_name="team_id",
    child_resource_name="invitation",
    manager_property="invitations",  # Path on parent manager
    child_network_model_cls=InvitationNetworkModel,
)
```

### Network Model Inference

Child models are automatically inferred when not provided:

```python
# Searches in order:
# 1. logic.BLL_Auth.{Resource}NetworkModel
# 2. logic.BLL_{Resource}.{Resource}NetworkModel
```

### Mirror Routers

Provide both nested and standalone access:

```python
# Original: /v1/team/{team_id}/invitation
# Mirror: /v1/invitation
mirror_router = invitation_router.create_mirror_router("/v1/invitation")
```

## Request/Response Patterns

### Standard Formats

**Single Resource Request:**
```json
{"resource_name": {"field1": "value1", "field2": "value2"}}
```

**Single Resource Response:**
```json
{"resource_name": {"id": "uuid", "field1": "value1", "created_at": "2024-01-01T00:00:00Z"}}
```

**List Response:**
```json
{"resource_name_plural": [{"id": "uuid1", "field1": "value1"}, {"id": "uuid2", "field1": "value2"}]}
```

### Batch Operations

**Batch Create:**
```json
{"resource_name_plural": [{"field1": "value1"}, {"field1": "value2"}]}
```

**Batch Update:**
```json
{"resource_name": {"field1": "new_value"}, "target_ids": ["id1", "id2"]}
```

**Batch Delete:**
```json
{"target_ids": ["id1", "id2"]}
```

## Custom Routes

### Current Pattern: Method Decorators

```python
class ResourceManager(RouterMixin, AbstractLogicManager):
    # Custom routes via method decorators
    @custom_route(method="post", path="/{id}/activate")
    def activate(self, id: str) -> ResourceModel:
        """Activate a resource."""
        # Implementation here
        return self.get(id)
    
    @static_route(method="get", path="/status")
    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Get system status."""
        return {"status": "active"}
```

### Legacy Custom Routes

#### Direct Route Addition
```python
@router.post("/{id}/activate")
async def activate_resource(
    id: str = Path(...),
    manager = Depends(get_resource_manager),
):
    return manager.activate(id)
```

#### Helper Method
```python
router.with_custom_route(
    method="post",
    path="/{id}/activate",
    endpoint=activate_resource,
    summary="Activate resource",
    description="Activates the specified resource",
)
```

## Example Generation

### Automatic Examples
Examples are generated automatically using intelligent field name patterns:

```python
# Auto-generated based on field names and types
examples = ExampleGenerator.generate_operation_examples(
    NetworkModel, "resource_name"
)
```

### Custom Overrides
```python
router = AbstractEPRouter(
    example_overrides={
        "get": {"resource": {"name": "Custom Example"}},
        "create": {"resource": {"email": "demo@example.com"}}
    }
)
```

## Manager Factory Patterns

### Standard Factory
```python
def get_resource_manager(
    user: User = Depends(UserManager.auth),
    target_user_id: Optional[str] = Query(None),
    target_team_id: Optional[str] = Query(None),
):
    return ResourceManager(
        requester_id=user.id,
        target_user_id=target_user_id or user.id,
        target_team_id=target_team_id,
        db_manager=get_db_manager()
    )
```

### System Factory
```python
def get_system_manager(auth_user=Depends(api_key_auth)):
    return SystemManager(
        requester_id=auth_user.id if auth_user else None,
        db_manager=get_db_manager()
    )
```

## Network Model Structure

Required pattern for router compatibility:

```python
class ResourceNetworkModel:
    class POST(BaseModel):
        resource: ResourceCreateModel  # Field name = resource_name
        
    class PUT(BaseModel):
        resource: ResourceUpdateModel  # Field name = resource_name
        
    class SEARCH(BaseModel):
        resource: ResourceSearchModel  # Field name = resource_name
        
    class ResponseSingle(BaseModel):
        resource: ResourceResponseModel  # Field name = resource_name
        
    class ResponsePlural(BaseModel):
        resources: List[ResourceResponseModel]  # Plural form
```

## Organization Patterns

### Single Router Module
```python
# EP_Resource.py

# 1. Factory functions
def get_resource_manager(): ...

# 2. Router creation
resource_router = AbstractEPRouter(...)

# 3. Custom routes
@resource_router.post("/custom")
async def custom_endpoint(): ...

# 4. Export
router = APIRouter()
router.include_router(resource_router)
```

### Complex Domain Module
```python
# EP_Provider.py - Multiple related resources

provider_router = AbstractEPRouter(...)
instance_router = AbstractEPRouter(...)
extension_router = AbstractEPRouter(...)

router = APIRouter()
router.include_router(provider_router)
router.include_router(instance_router)
router.include_router(extension_router)
```

## Error Handling

Consistent error responses through manager exceptions:

```python
# In managers, raise these for automatic HTTP conversion:
raise ResourceNotFoundError("resource", resource_id)     # → 404
raise ResourceConflictError("resource", "already exists") # → 409  
raise InvalidRequestError("Invalid data")                # → 400
```

## Common Patterns

### Router Trees
For complex hierarchies:

```python
routers = create_router_tree(
    base_prefix="/v1/team",
    resource_name="team",
    tags=["Team Management"],
    manager_factory=get_team_manager,
    network_model_cls=TeamNetworkModel,
    nested_resources=[
        {
            "name": "invitation",
            "network_model_cls": InvitationNetworkModel,
            "create_mirror": True,
        }
    ],
)
```

### Testing Integration
```python
class TestResourceEndpoints(AbstractEPTest):
    base_endpoint = "resource"
    entity_name = "resource"
    required_fields = ["name", "description"]
    string_field_to_update = "name"
    
    create_fields = {
        "name": lambda: f"Test {faker.word()}",
        "description": "Test description"
    }
```

## Best Practices

1. **Consistent Naming**: Use same `resource_name` throughout
2. **Manager Logic**: Keep business logic in managers, not routes
3. **Authentication**: JWT for users, API keys for system operations
4. **Model Structure**: Follow NetworkModel requirements exactly
5. **Route Selection**: Only register needed routes
6. **Testing**: Use AbstractEPTest for comprehensive coverage
7. **Performance**: Implement pagination in managers
8. **Security**: Proper auth and input validation