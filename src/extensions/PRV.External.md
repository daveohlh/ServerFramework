# AbstractExternalModel System

## Overview

The AbstractExternalModel system provides a unified interface for working with external API resources using the same patterns as our internal database models. This allows external APIs to be managed through the Provider Rotation System while maintaining consistent interfaces for endpoints and GraphQL abstractions.

## Architecture

### Core Components

1. **AbstractExternalModel** - Base class for external API resource models
2. **AbstractExternalAPIClient** - Provides database-like interface for external APIs  
3. **AbstractExternalManager** - Manager class for external models (similar to AbstractBLLManager)

### Integration Points

- **Provider Rotation System** - All external API calls go through provider rotation for reliability
- **Endpoint/GraphQL Compatibility** - External models can be used with existing endpoint patterns
- **Consistent Interface** - Same CRUD operations as internal models (.create(), .get(), .list(), etc.)

## Key Classes

### AbstractExternalModel

Base class for representing external API resources. Similar to internal Pydantic models but with additional methods for API integration.

**Key Properties:**
- `external_resource` - API resource identifier (e.g., "products", "customers")
- `field_mappings` - Maps internal field names to external API field names
- `provider_methods` - Maps CRUD operations to provider method names

**Key Methods:**
- `to_external_format()` - Convert internal data to external API format
- `from_external_format()` - Convert external API data to internal format
- `to_external_query_format()` - Convert query parameters for external API
- `*_via_provider()` - Static methods called by Provider Rotation System

### AbstractExternalAPIClient

Provides database-like interface for external APIs. Acts as the "DB" property equivalent for external models.

**Key Methods:**
- `create()` - Create entity via external API
- `get()` - Get entity by ID via external API
- `list()` - List entities with filtering/pagination
- `update()` - Update entity via external API
- `delete()` - Delete entity via external API
- `exists()` - Check if entity exists

### AbstractExternalManager

Manager class for external models. **Inherits from AbstractBLLManager** to leverage all existing functionality (hooks, validation, search transformers, etc.) while overriding database operations to work with external APIs.

**Key Properties:**
- `Model` - The external model class
- `DB` - Returns the external API client (overrides the database property)
- All AbstractBLLManager functionality (hooks, validation, etc.)

## Implementation Example: Stripe Product

### 1. Define the External Model

```python
from extensions.AbstractExternalModel import AbstractExternalModel
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from decimal import Decimal

class StripeProductModel(AbstractExternalModel):
    """External model for Stripe Product API resource."""
    
    # Stripe API resource identifier
    external_resource = "products"
    
    # Field mappings between internal and Stripe API
    field_mappings = {
        "display_name": "name",
        "description": "description", 
        "is_active": "active",
        "external_id": "id"
    }
    
    # Model fields (internal format)
    external_id: str = Field(..., description="Stripe product ID")
    display_name: str = Field(..., description="Product name")
    description: Optional[str] = None
    is_active: bool = Field(True, description="Whether product is active")
    created_at: Optional[int] = None  # Stripe timestamp
    
    class Create(BaseModel):
        display_name: str
        description: Optional[str] = None
        is_active: bool = True
    
    class Update(BaseModel):
        display_name: Optional[str] = None
        description: Optional[str] = None
        is_active: Optional[bool] = None
    
    class Search(BaseModel):
        display_name: Optional[str] = None
        is_active: Optional[bool] = None
    
    @classmethod
    def to_external_format(cls, internal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert internal format to Stripe API format."""
        external_data = {}
        
        for internal_field, value in internal_data.items():
            # Map field names
            external_field = cls.field_mappings.get(internal_field, internal_field)
            external_data[external_field] = value
            
        return external_data
    
    @classmethod
    def from_external_format(cls, external_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Stripe API format to internal format."""
        internal_data = {}
        
        # Reverse field mapping
        reverse_mappings = {v: k for k, v in cls.field_mappings.items()}
        
        for external_field, value in external_data.items():
            internal_field = reverse_mappings.get(external_field, external_field)
            internal_data[internal_field] = value
            
        return internal_data
    
    @classmethod
    def to_external_query_format(
        cls, 
        query_params: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[List] = None
    ) -> Dict[str, Any]:
        """Convert query parameters to Stripe API format."""
        external_params = {}
        
        # Map query fields
        for internal_field, value in query_params.items():
            external_field = cls.field_mappings.get(internal_field, internal_field)
            external_params[external_field] = value
        
        # Stripe pagination
        if limit:
            external_params["limit"] = limit
        if offset:
            external_params["starting_after"] = offset  # Stripe uses cursor pagination
            
        return external_params
    
    @staticmethod
    def create_via_provider(provider_instance, **kwargs) -> Dict[str, Any]:
        """Create product via Stripe provider."""
        try:
            # Get Stripe client from provider
            stripe = provider_instance.get_stripe_client()
            
            # Create product
            product = stripe.Product.create(**kwargs)
            
            return {
                "success": True,
                "data": dict(product)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_via_provider(provider_instance, external_id: str) -> Dict[str, Any]:
        """Get product via Stripe provider."""
        try:
            stripe = provider_instance.get_stripe_client()
            product = stripe.Product.retrieve(external_id)
            
            return {
                "success": True,
                "data": dict(product)
            }
            
        except stripe.error.InvalidRequestError as e:
            if "No such product" in str(e):
                return {"success": False, "error": "Not found"}
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def list_via_provider(provider_instance, **kwargs) -> Dict[str, Any]:
        """List products via Stripe provider."""
        try:
            stripe = provider_instance.get_stripe_client()
            products = stripe.Product.list(**kwargs)
            
            return {
                "success": True,
                "data": [dict(product) for product in products.data]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def update_via_provider(provider_instance, external_id: str, **kwargs) -> Dict[str, Any]:
        """Update product via Stripe provider."""
        try:
            stripe = provider_instance.get_stripe_client()
            product = stripe.Product.modify(external_id, **kwargs)
            
            return {
                "success": True,
                "data": dict(product)
            }
            
        except stripe.error.InvalidRequestError as e:
            if "No such product" in str(e):
                return {"success": False, "error": "Not found"}
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def delete_via_provider(provider_instance, external_id: str) -> Dict[str, Any]:
        """Delete product via Stripe provider."""
        try:
            stripe = provider_instance.get_stripe_client()
            stripe.Product.delete(external_id)
            
            return {"success": True}
            
        except stripe.error.InvalidRequestError as e:
            if "No such product" in str(e):
                return {"success": False, "error": "Not found"}
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

### 2. Create External Manager

```python
from extensions.AbstractExternalModel import AbstractExternalManager
from extensions.payment.models.StripeProductModel import StripeProductModel

class StripeProductManager(AbstractExternalManager):
    """Manager for Stripe Product external API."""
    
    Model = StripeProductModel
    
    def __init__(self, requester_id: str, **kwargs):
        # Get rotation manager for payment extension
        from extensions.payment.EXT_Payment import EXT_Payment
        
        rotation_manager = EXT_Payment.root
        if not rotation_manager:
            raise RuntimeError("Payment extension rotation not available")
            
        super().__init__(
            requester_id=requester_id,
            rotation_manager=rotation_manager,
            **kwargs
        )
    
    # All AbstractBLLManager methods work automatically!
    # Hooks, validation, search transformers, etc. all work seamlessly
    
    # Optional: Override specific validation if needed
    def create_validation(self, entity):
        """Custom validation for Stripe products."""
        super().create_validation(entity)
        # Add Stripe-specific validation here
        
    def _register_search_transformers(self):
        """Register custom search transformers for Stripe products."""
        super()._register_search_transformers()
        # Add Stripe-specific search transformers
        self.register_search_transformer('price_range', self._transform_price_range)
```

### 3. Integration in BLL

```python
from extensions.payment.managers.StripeProductManager import StripeProductManager

class BLL_Payment(AbstractBLLManager):
    """Payment extension business logic."""
    
    @classmethod
    def get_stripe_product_manager(cls, requester_id: str, **kwargs) -> StripeProductManager:
        """Get Stripe product manager instance."""
        return StripeProductManager(requester_id=requester_id, **kwargs, db_manager=self.db_manager)
    
    @classmethod
    def create_stripe_product(cls, requester_id: str, **product_data):
        """Create a product in Stripe."""
        manager = cls.get_stripe_product_manager(requester_id)
        return manager.create(**product_data)
    
    @classmethod
    def list_stripe_products(cls, requester_id: str, **filters):
        """List products from Stripe."""
        manager = cls.get_stripe_product_manager(requester_id)
        return manager.list(**filters)
```

## Usage Patterns

### Basic CRUD Operations

```python
# Create product manager
product_manager = BLL_Payment.get_stripe_product_manager(requester_id="user_123")

# Create - works exactly like internal models
product = product_manager.create(
    display_name="Premium Plan",
    description="Premium subscription plan",
    is_active=True
)

# Get - same interface as internal models
product = product_manager.get(id="prod_stripe_id_123")

# List with filtering - same search capabilities
products = product_manager.list(is_active=True, limit=10)

# Search with complex filters - same as internal models
products = product_manager.search(
    display_name={"inc": "Premium"},
    is_active=True,
    limit=20
)

# Update - identical to internal models
updated_product = product_manager.update(
    id="prod_stripe_id_123",
    display_name="Premium Plan v2"
)

# Batch operations - work automatically!
updated_products = product_manager.batch_update([
    {"id": "prod_1", "data": {"display_name": "New Name 1"}},
    {"id": "prod_2", "data": {"display_name": "New Name 2"}}
])

# Delete - same as internal models
product_manager.delete(id="prod_stripe_id_123")

# Hooks work automatically - no changes needed!
@hook_bll(StripeProductManager.create, timing="after")
def log_product_creation(context):
    logger.info(f"Stripe product created: {context.result.display_name}")
```

### Endpoint Integration

External models can be used with existing endpoint patterns:

```python
from endpoints.AbstractEPRouter import AbstractEPRouter

class PaymentEPRouter(AbstractEPRouter):
    """Payment endpoints with external model support."""
    
    @app.get("/stripe/products/{product_id}")
    async def get_stripe_product(product_id: str, requester_id: str = Depends(get_requester)):
        manager = BLL_Payment.get_stripe_product_manager(requester_id)
        return manager.get(id=product_id)
    
    @app.get("/stripe/products")
    async def list_stripe_products(
        requester_id: str = Depends(get_requester),
        limit: Optional[int] = 20,
        is_active: Optional[bool] = None
    ):
        manager = BLL_Payment.get_stripe_product_manager(requester_id)
        return manager.list(limit=limit, is_active=is_active)
```

## Provider Integration

### Extending Existing Providers

Add external model support to existing providers:

```python
class StripeProvider(AbstractPaymentProvider):
    """Stripe provider with external model support."""
    
    def get_stripe_client(self):
        """Get configured Stripe client."""
        import stripe
        stripe.api_key = self.get_api_key()
        return stripe
    
    # External model methods are called via rotation system
    # Implementation is in the model's *_via_provider methods
```

## Navigation Properties

The AbstractExternalModel system supports navigation properties that work identically to internal database models. This allows seamless integration with GraphQL generation and existing endpoint patterns.

### Creating External Reference Models

Use the `create_external_reference_model` factory function to create reference models that follow the standard pattern:

```python
from extensions.AbstractExternalModel import AbstractExternalModel, create_external_reference_model

# 1. Define your external model
class Stripe_CustomerModel(AbstractExternalModel):
    """External model for Stripe Customer."""
    
    external_resource = "customers"
    
    # Fields
    id: str = Field(..., description="Stripe customer ID")
    email: str = Field(..., description="Customer email")
    name: Optional[str] = Field(None, description="Customer name")
    
    # ... implement required abstract methods ...

# 2. Create the reference model using the factory
Stripe_CustomerReferenceModel = create_external_reference_model(
    external_model_class=Stripe_CustomerModel,
    reference_field_name="external_payment_id",  # The field name containing the foreign key
    local_field_name="external_payment_id",     # The local field to resolve from
)
```

### Using External Reference Models

Once created, external reference models work exactly like internal ones:

```python
# In your BLL_Payment.py
from lib.Pydantic2SQLAlchemy import extension_model
from logic.BLL_Auth import UserModel

@extension_model(UserModel)
class Payment_UserModel(Stripe_CustomerReferenceModel.Optional):
    """
    Payment extension for User model with Stripe customer navigation.
    
    This automatically adds:
    - external_payment_id: Optional[str] field
    - stripe_customer: Optional[Stripe_CustomerModel] navigation property
    """
    pass
```

### Automatic Navigation

The navigation property resolves automatically:

```python
# Get a user with payment extension
user_manager = BLL_Payment.get_user_manager(requester_id="user_123")
user = user_manager.get(id="user_456")

# Access the Stripe customer directly via navigation property
if user.external_payment_id:
    customer = user.stripe_customer  # Automatically resolves from Stripe API
    logger.debug(f"Customer email: {customer.email}")
    logger.debug(f"Customer name: {customer.name}")
```

### GraphQL Integration

Navigation properties work seamlessly with GraphQL generation - no changes required:

```graphql
query GetUserWithCustomer {
  user(id: "user_456") {
    id
    email
    external_payment_id
    stripe_customer {
      id
      email  
      name
    }
  }
}
```

### Multiple Navigation Properties

You can define multiple external navigation properties:

```python
# Define multiple external models
Stripe_SubscriptionModel = AbstractExternalModel(...)  
Stripe_PaymentMethodModel = AbstractExternalModel(...)

# Create reference models
Stripe_CustomerReferenceModel = create_external_reference_model(
    Stripe_CustomerModel, "external_payment_id", "external_payment_id"
)

Stripe_SubscriptionReferenceModel = create_external_reference_model(
    Stripe_SubscriptionModel, "external_subscription_id", "external_subscription_id"  
)

# Use multiple references
@extension_model(UserModel)
class Payment_UserModel(
    Stripe_CustomerReferenceModel.Optional,
    Stripe_SubscriptionReferenceModel.Optional
):
    """User with multiple Stripe navigation properties."""
    pass
```

### Complex Navigation Examples

```python
# User with customer and subscriptions
user = user_manager.get(id="user_123")

# Direct customer access
customer = user.stripe_customer

# Get customer's subscriptions via another navigation
if customer:
    # This would require additional setup, but demonstrates the pattern
    subscriptions = customer.subscriptions  # List navigation property
    
    for subscription in subscriptions:
        logger.debug(f"Subscription: {subscription.id} - Status: {subscription.status}")
```

### Best Practices for Navigation Properties

1. **Lazy Loading** - Navigation properties are resolved on first access and cached
2. **Error Handling** - Failed navigation returns None (single) or empty list (collection)
3. **Performance** - Consider the impact of external API calls in navigation chains
4. **Caching** - Results are cached per instance to avoid duplicate API calls
5. **Context** - Navigation properties use system context by default (SYSTEM_ID)

## Benefits

1. **Full AbstractBLLManager Integration** - Inherits ALL functionality including hooks, validation, search transformers, batch operations, etc.
2. **Unified Interface** - External APIs use identical patterns to internal models
3. **Provider Rotation** - Automatic failover and load balancing for external APIs
4. **Endpoint Compatibility** - External models work seamlessly with existing endpoint abstractions
5. **GraphQL Support** - External models can be exposed via GraphQL without changes
6. **Hook System** - Full hook support for before/after operations, auditing, etc.
7. **Consistent Error Handling** - Same error patterns as internal operations
8. **Type Safety** - Full Pydantic validation and type hints
9. **Field Mapping** - Automatic conversion between internal and external formats
10. **Search Transformers** - Custom search logic works the same way
11. **Validation Framework** - Same validation patterns for create/update operations

## Best Practices

1. **Field Mappings** - Always define field mappings for different naming conventions
2. **Error Handling** - Provide meaningful error messages and proper HTTP status codes
3. **Pagination** - Handle different pagination styles (offset vs cursor-based)
4. **Rate Limiting** - Consider API rate limits in provider rotation
5. **Caching** - Implement caching for frequently accessed external data
6. **Validation** - Validate data both before sending to API and after receiving
7. **Testing** - Mock external API calls in tests using provider rotation patterns

## Testing

External models can be tested by mocking the provider rotation:

```python
def test_stripe_product_creation(mock_rotation):
    """Test Stripe product creation."""
    # Mock the rotation system
    mock_rotation.rotate.return_value = {
        "success": True,
        "data": {"id": "prod_123", "name": "Test Product", "active": True}
    }
    
    manager = StripeProductManager(requester_id="test_user", rotation_manager=mock_rotation, db_manager=self.db_manager)
    product = manager.create(display_name="Test Product")
    
    assert product.display_name == "Test Product"
    assert product.external_id == "prod_123"
```
