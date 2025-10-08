from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel, Field

from lib.Logging import logger
from logic.AbstractLogicManager import AbstractBLLManager

T = TypeVar("T")


class ExternalNavigationProperty:
    """
    Descriptor for external navigation properties.
    Automatically resolves relationships to external API models.
    """

    def __init__(
        self,
        external_model_class: Type["AbstractExternalModel"],
        local_field: str,
        external_field: str = "id",
        manager_class: Optional[Type["AbstractExternalManager"]] = None,
        is_list: bool = False,
        cache_key: Optional[str] = None,
    ):
        """
        Initialize external navigation property.

        Args:
            external_model_class: The external model class to navigate to
            local_field: The local field containing the external ID (e.g., 'external_payment_id')
            external_field: The field in the external model to match against (default: 'id')
            manager_class: Optional specific manager class to use
            is_list: Whether this navigation returns a list of items
            cache_key: Optional cache key for performance
        """
        self.external_model_class = external_model_class
        self.local_field = local_field
        self.external_field = external_field
        self.manager_class = manager_class
        self.is_list = is_list
        self.cache_key = cache_key
        self.attr_name = None  # Set by __set_name__

    def __set_name__(self, owner, name):
        """Called when the descriptor is assigned to a class attribute."""
        self.attr_name = name

    def __get__(self, instance, owner):
        """Resolve the navigation property when accessed."""
        if instance is None:
            return self

        # Check if already cached on the instance
        cache_attr = f"_cached_{self.attr_name}"
        if hasattr(instance, cache_attr):
            return getattr(instance, cache_attr)

        # Get the local field value (the external ID)
        local_value = getattr(instance, self.local_field, None)
        if not local_value:
            return [] if self.is_list else None

        try:
            # Get the manager for the external model
            manager_class = self.manager_class or self._get_default_manager_class()

            # Create manager instance - we need a requester_id context
            # For now, use a system context, but in practice this should come from the current request context
            from lib.Environment import env

            manager = manager_class(requester_id=env("SYSTEM_ID"))

            # Resolve the relationship
            if self.is_list:
                # For list relationships, search by the external field
                search_params = {self.external_field: local_value}
                result = manager.list(**search_params)
            else:
                # For single relationships, get by the external field
                if self.external_field == "id":
                    result = manager.get(id=local_value)
                else:
                    search_params = {self.external_field: local_value}
                    results = manager.list(**search_params)
                    result = results[0] if results else None

            # Cache the result on the instance
            setattr(instance, cache_attr, result)
            return result

        except Exception as e:
            logger.warning(
                f"Failed to resolve navigation property {self.attr_name}: {e}"
            )
            return [] if self.is_list else None

    def _get_default_manager_class(self) -> Type["AbstractExternalManager"]:
        """Get the default manager class for the external model."""
        # Look for a manager class with the same name pattern
        model_name = self.external_model_class.__name__
        if model_name.endswith("Model"):
            base_name = model_name[:-5]  # Remove "Model"
            manager_name = f"{base_name}Manager"

            # Try to find the manager class in the same module
            import sys

            for module in sys.modules.values():
                if hasattr(module, manager_name):
                    manager_class = getattr(module, manager_name)
                    if issubclass(manager_class, AbstractExternalManager):
                        return manager_class

        raise ValueError(
            f"Could not find manager class for {self.external_model_class.__name__}"
        )


def external_navigation_property(
    external_model_class: Type["AbstractExternalModel"],
    local_field: str,
    external_field: str = "id",
    manager_class: Optional[Type["AbstractExternalManager"]] = None,
    is_list: bool = False,
) -> Any:
    """
    Decorator/factory function for creating external navigation properties.

    Usage:
        class UserModel(BaseModel):
            external_payment_id: Optional[str] = None

            customer: Optional[StripeCustomerModel] = external_navigation_property(
                StripeCustomerModel,
                local_field="external_payment_id"
            )
    """
    return ExternalNavigationProperty(
        external_model_class=external_model_class,
        local_field=local_field,
        external_field=external_field,
        manager_class=manager_class,
        is_list=is_list,
    )


class AbstractExternalAPIClient(ABC):
    """
    Abstract base class for external API clients.
    Provides database-like interface for external APIs via Provider Rotation System.
    """

    def __init__(
        self, provider_rotation_manager, model_class: Type["AbstractExternalModel"]
    ):
        """
        Initialize the API client.

        Args:
            provider_rotation_manager: RotationManager instance for provider rotation
            model_class: The external model class this client manages
        """
        self.rotation_manager = provider_rotation_manager
        self.model_class = model_class

    def create(
        self,
        requester_id: str,
        db=None,  # Ignored for external APIs
        return_type: str = "dto",
        override_dto: Optional[Type] = None,
        **kwargs,
    ) -> Any:
        """
        Create an entity via external API using provider rotation.

        Args:
            requester_id: ID of requesting user
            db: Ignored for external APIs
            return_type: Type of return value ("dto" or "dict")
            override_dto: Optional DTO class override
            **kwargs: Creation parameters

        Returns:
            Created entity
        """
        try:
            # Convert internal format to external API format
            external_data = self.model_class.to_external_format(kwargs)

            # Call external API via provider rotation
            result = self.rotation_manager.rotate(
                self.model_class.create_via_provider, **external_data
            )

            if not result.get("success", False):
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to create {self.model_class.__name__}: {result.get('error', 'Unknown error')}",
                )

            # Convert external format back to internal format
            internal_data = self.model_class.from_external_format(
                result.get("data", {})
            )

            # Return as DTO or dict
            if return_type == "dto":
                dto_class = override_dto or self.model_class
                return dto_class(**internal_data)
            else:
                return internal_data

        except Exception as e:
            logger.error(f"Error creating {self.model_class.__name__}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def get(
        self,
        requester_id: str,
        db=None,  # Ignored for external APIs
        return_type: str = "dto",
        override_dto: Optional[Type] = None,
        options: Optional[List] = None,
        **kwargs,
    ) -> Any:
        """
        Get an entity by ID via external API.

        Args:
            requester_id: ID of requesting user
            db: Ignored for external APIs
            return_type: Type of return value
            override_dto: Optional DTO class override
            options: Ignored for external APIs (no joins)
            **kwargs: Query parameters (must include 'id')

        Returns:
            Retrieved entity
        """
        if "id" not in kwargs:
            raise HTTPException(status_code=400, detail="ID parameter required")

        try:
            # Call external API via provider rotation
            result = self.rotation_manager.rotate(
                self.model_class.get_via_provider, external_id=kwargs["id"]
            )

            if not result.get("success", False):
                if result.get("error") == "Not found":
                    raise HTTPException(
                        status_code=404, detail=f"{self.model_class.__name__} not found"
                    )
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to get {self.model_class.__name__}: {result.get('error', 'Unknown error')}",
                )

            # Convert external format to internal format
            internal_data = self.model_class.from_external_format(
                result.get("data", {})
            )

            # Return as DTO or dict
            if return_type == "dto":
                dto_class = override_dto or self.model_class
                return dto_class(**internal_data)
            else:
                return internal_data

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting {self.model_class.__name__}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def list(
        self,
        requester_id: str,
        db=None,  # Ignored for external APIs
        return_type: str = "dto",
        override_dto: Optional[Type] = None,
        options: Optional[List] = None,
        order_by: Optional[List] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        filters: Optional[List] = None,
        **kwargs,
    ) -> List[Any]:
        """
        List entities via external API.

        Args:
            requester_id: ID of requesting user
            db: Ignored for external APIs
            return_type: Type of return value
            override_dto: Optional DTO class override
            options: Ignored for external APIs
            order_by: Sorting parameters
            limit: Maximum number of results
            offset: Pagination offset
            filters: Ignored - use kwargs for filtering
            **kwargs: Query parameters for filtering

        Returns:
            List of entities
        """
        try:
            # Convert internal filters to external API format
            external_params = self.model_class.to_external_query_format(
                kwargs, limit=limit, offset=offset, order_by=order_by
            )

            # Call external API via provider rotation
            result = self.rotation_manager.rotate(
                self.model_class.list_via_provider, **external_params
            )

            if not result.get("success", False):
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to list {self.model_class.__name__}: {result.get('error', 'Unknown error')}",
                )

            # Convert external format to internal format
            items = []
            for item_data in result.get("data", []):
                internal_data = self.model_class.from_external_format(item_data)

                if return_type == "dto":
                    dto_class = override_dto or self.model_class
                    items.append(dto_class(**internal_data))
                else:
                    items.append(internal_data)

            return items

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error listing {self.model_class.__name__}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def update(
        self,
        requester_id: str,
        db=None,  # Ignored for external APIs
        return_type: str = "dto",
        override_dto: Optional[Type] = None,
        new_properties: Optional[Dict] = None,
        **kwargs,
    ) -> Any:
        """
        Update an entity via external API.

        Args:
            requester_id: ID of requesting user
            db: Ignored for external APIs
            return_type: Type of return value
            override_dto: Optional DTO class override
            new_properties: Properties to update
            **kwargs: Must include 'id'

        Returns:
            Updated entity
        """
        if "id" not in kwargs:
            raise HTTPException(status_code=400, detail="ID parameter required")

        try:
            # Convert internal format to external API format
            update_data = self.model_class.to_external_format(new_properties or {})

            # Call external API via provider rotation
            result = self.rotation_manager.rotate(
                self.model_class.update_via_provider,
                external_id=kwargs["id"],
                **update_data,
            )

            if not result.get("success", False):
                if result.get("error") == "Not found":
                    raise HTTPException(
                        status_code=404, detail=f"{self.model_class.__name__} not found"
                    )
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to update {self.model_class.__name__}: {result.get('error', 'Unknown error')}",
                )

            # Convert external format to internal format
            internal_data = self.model_class.from_external_format(
                result.get("data", {})
            )

            # Return as DTO or dict
            if return_type == "dto":
                dto_class = override_dto or self.model_class
                return dto_class(**internal_data)
            else:
                return internal_data

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating {self.model_class.__name__}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def delete(self, requester_id: str, db=None, **kwargs) -> None:
        """
        Delete an entity via external API.

        Args:
            requester_id: ID of requesting user
            db: Ignored for external APIs
            **kwargs: Must include 'id'
        """
        if "id" not in kwargs:
            raise HTTPException(status_code=400, detail="ID parameter required")

        try:
            # Call external API via provider rotation
            result = self.rotation_manager.rotate(
                self.model_class.delete_via_provider, external_id=kwargs["id"]
            )

            if not result.get("success", False):
                if result.get("error") == "Not found":
                    raise HTTPException(
                        status_code=404, detail=f"{self.model_class.__name__} not found"
                    )
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to delete {self.model_class.__name__}: {result.get('error', 'Unknown error')}",
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting {self.model_class.__name__}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def exists(self, requester_id: str, db=None, **kwargs) -> bool:
        """
        Check if an entity exists via external API.

        Args:
            requester_id: ID of requesting user
            db: Ignored for external APIs
            **kwargs: Query parameters

        Returns:
            True if entity exists, False otherwise
        """
        try:
            self.get(requester_id=requester_id, **kwargs)
            return True
        except HTTPException as e:
            if e.status_code == 404:
                return False
            raise


class DirectProviderAPIClient(AbstractExternalAPIClient):
    """
    Direct API client that works with provider classes for testing.

    This client bypasses the rotation system and calls provider methods directly,
    making it suitable for testing scenarios where no rotation manager is available.
    """

    def __init__(self, provider_class, model_class: Type["AbstractExternalModel"]):
        """Initialize direct provider API client."""
        self.provider_class = provider_class
        self.model_class = model_class
        logger.debug(
            f"Initialized DirectProviderAPIClient for {provider_class.__name__}"
        )

    def create(
        self,
        requester_id: str,
        db=None,  # Ignored for external APIs
        return_type: str = "dto",
        override_dto: Optional[Type] = None,
        **kwargs,
    ) -> Any:
        """Create via direct provider call."""
        try:
            # Call the model's create_via_provider method directly
            result = self.model_class.create_via_provider(self.provider_class, **kwargs)

            if result.get("success"):
                return result.get("data", result)
            else:
                logger.error(
                    f"Provider create failed: {result.get('error', 'Unknown error')}"
                )
                return None
        except Exception as e:
            logger.error(f"Direct provider create failed: {e}")
            return None

    def get(
        self,
        requester_id: str,
        db=None,  # Ignored for external APIs
        return_type: str = "dto",
        override_dto: Optional[Type] = None,
        options: Optional[List] = None,
        **kwargs,
    ) -> Any:
        """Get via direct provider call."""
        try:
            # Extract the ID from kwargs
            external_id = kwargs.get("id")
            if not external_id:
                logger.error("No ID provided for get operation")
                return None

            # Call the model's get_via_provider method directly
            result = self.model_class.get_via_provider(self.provider_class, external_id)

            if result.get("success"):
                return result.get("data", result)
            else:
                logger.error(
                    f"Provider get failed: {result.get('error', 'Unknown error')}"
                )
                return None
        except Exception as e:
            logger.error(f"Direct provider get failed: {e}")
            return None

    def list(
        self,
        requester_id: str,
        db=None,  # Ignored for external APIs
        return_type: str = "dto",
        override_dto: Optional[Type] = None,
        options: Optional[List] = None,
        order_by: Optional[List] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        filters: Optional[List] = None,
        **kwargs,
    ) -> List[Any]:
        """List via direct provider call."""
        try:
            # Call the model's list_via_provider method directly
            result = self.model_class.list_via_provider(self.provider_class, **kwargs)

            if result.get("success"):
                data = result.get("data", [])
                return data if isinstance(data, list) else [data]
            else:
                logger.error(
                    f"Provider list failed: {result.get('error', 'Unknown error')}"
                )
                return []
        except Exception as e:
            logger.error(f"Direct provider list failed: {e}")
            return []

    def update(
        self,
        requester_id: str,
        db=None,  # Ignored for external APIs
        return_type: str = "dto",
        override_dto: Optional[Type] = None,
        new_properties: Optional[Dict] = None,
        **kwargs,
    ) -> Any:
        """Update via direct provider call."""
        try:
            # Extract the ID from kwargs
            external_id = kwargs.get("id")
            if not external_id:
                logger.error("No ID provided for update operation")
                return None

            # Merge new_properties with kwargs for update data
            update_data = {**kwargs}
            if new_properties:
                update_data.update(new_properties)

            # Remove ID from update data
            update_data.pop("id", None)

            # Call the model's update_via_provider method directly
            result = self.model_class.update_via_provider(
                self.provider_class, external_id, **update_data
            )

            if result.get("success"):
                return result.get("data", result)
            else:
                logger.error(
                    f"Provider update failed: {result.get('error', 'Unknown error')}"
                )
                return None
        except Exception as e:
            logger.error(f"Direct provider update failed: {e}")
            return None

    def delete(self, requester_id: str, db=None, **kwargs) -> None:
        """Delete via direct provider call."""
        try:
            # Extract the ID from kwargs
            external_id = kwargs.get("id")
            if not external_id:
                logger.error("No ID provided for delete operation")
                return

            # Call the model's delete_via_provider method directly
            result = self.model_class.delete_via_provider(
                self.provider_class, external_id
            )

            if not result.get("success"):
                logger.error(
                    f"Provider delete failed: {result.get('error', 'Unknown error')}"
                )
        except Exception as e:
            logger.error(f"Direct provider delete failed: {e}")

    def exists(self, requester_id: str, db=None, **kwargs) -> bool:
        """Check existence via direct provider call."""
        try:
            # Try to get the entity to check if it exists
            result = self.get(requester_id, db=db, **kwargs)
            return result is not None
        except Exception as e:
            logger.error(f"Direct provider exists check failed: {e}")
            return False


class AbstractExternalModel(BaseModel, ABC):
    """
    Abstract base class for models representing external API resources.

    Provides similar interface to internal database models but operates via
    external APIs through the Provider Rotation System.
    """

    # External API resource identifier (e.g., "products", "customers")
    external_resource: str = ""

    # Field mappings between internal format and external API format
    # Format: {"internal_field": "external_field"}
    field_mappings: Dict[str, str] = {}

    # Provider method mappings for CRUD operations
    provider_methods: Dict[str, str] = {
        "create": "create_via_provider",
        "get": "get_via_provider",
        "list": "list_via_provider",
        "update": "update_via_provider",
        "delete": "delete_via_provider",
    }

    # External API client instance (set by manager)
    _api_client: Optional[AbstractExternalAPIClient] = None

    @property
    def API(self) -> AbstractExternalAPIClient:
        """Get the API client for this model."""
        if self._api_client is None:
            raise RuntimeError(
                f"API client not initialized for {self.__class__.__name__}"
            )
        return self._api_client

    @classmethod
    def set_api_client(cls, api_client: AbstractExternalAPIClient):
        """Set the API client for this model class."""
        cls._api_client = api_client

    @classmethod
    @abstractmethod
    def to_external_format(cls, internal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert internal data format to external API format.

        Args:
            internal_data: Data in internal format

        Returns:
            Data converted to external API format
        """
        pass

    @classmethod
    @abstractmethod
    def from_external_format(cls, external_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert external API format to internal data format.

        Args:
            external_data: Data from external API

        Returns:
            Data converted to internal format
        """
        pass

    @classmethod
    def to_external_query_format(
        cls,
        query_params: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[List] = None,
    ) -> Dict[str, Any]:
        """
        Convert internal query parameters to external API query format.

        Args:
            query_params: Internal query parameters
            limit: Maximum results
            offset: Pagination offset
            order_by: Sorting parameters

        Returns:
            Query parameters in external API format
        """
        # Default implementation - override in subclasses for API-specific formatting
        external_params = {}

        # Map fields
        for internal_field, value in query_params.items():
            external_field = cls.field_mappings.get(internal_field, internal_field)
            external_params[external_field] = value

        # Add pagination
        if limit is not None:
            external_params["limit"] = limit
        if offset is not None:
            external_params["offset"] = offset

        # Add ordering - format depends on API
        if order_by:
            # This is API-specific - override in subclasses
            external_params["order"] = order_by

        return external_params

    @staticmethod
    @abstractmethod
    def create_via_provider(provider_instance, **kwargs) -> Dict[str, Any]:
        """
        Create resource via provider instance.
        Called by Provider Rotation System.

        Args:
            provider_instance: ProviderInstanceModel with API credentials
            **kwargs: Creation parameters in external format

        Returns:
            Dict with success status and data/error
        """
        pass

    @staticmethod
    @abstractmethod
    def get_via_provider(provider_instance, external_id: str) -> Dict[str, Any]:
        """
        Get resource via provider instance.
        Called by Provider Rotation System.

        Args:
            provider_instance: ProviderInstanceModel with API credentials
            external_id: External resource ID

        Returns:
            Dict with success status and data/error
        """
        pass

    @staticmethod
    @abstractmethod
    def list_via_provider(provider_instance, **kwargs) -> Dict[str, Any]:
        """
        List resources via provider instance.
        Called by Provider Rotation System.

        Args:
            provider_instance: ProviderInstanceModel with API credentials
            **kwargs: Query parameters in external format

        Returns:
            Dict with success status and data/error
        """
        pass

    @staticmethod
    @abstractmethod
    def update_via_provider(
        provider_instance, external_id: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Update resource via provider instance.
        Called by Provider Rotation System.

        Args:
            provider_instance: ProviderInstanceModel with API credentials
            external_id: External resource ID
            **kwargs: Update parameters in external format

        Returns:
            Dict with success status and data/error
        """
        pass

    @staticmethod
    @abstractmethod
    def delete_via_provider(provider_instance, external_id: str) -> Dict[str, Any]:
        """
        Delete resource via provider instance.
        Called by Provider Rotation System.

        Args:
            provider_instance: ProviderInstanceModel with API credentials
            external_id: External resource ID

        Returns:
            Dict with success status and data/error
        """
        pass

    # Pydantic model classes for different operations
    class Create(BaseModel):
        """Base create model for external resources."""

        pass

    class Update(BaseModel):
        """Base update model for external resources."""

        pass

    class Search(BaseModel):
        """Base search model for external resources."""

        pass


def create_external_reference_model(
    external_model_class: Type[AbstractExternalModel],
    reference_field_name: str,
    local_field_name: str,
    manager_class: Optional[Type["AbstractExternalManager"]] = None,
) -> Type[BaseModel]:
    """
    Factory function to create external reference models that work with the standard pattern.

    Args:
        external_model_class: The external model to reference
        reference_field_name: The name of the reference field (e.g., "customer_id")
        local_field_name: The local field containing the external ID
        manager_class: Optional specific manager class

    Returns:
        A reference model class with Optional and Search variants
    """

    # Create the navigation property descriptor
    nav_property = ExternalNavigationProperty(
        external_model_class=external_model_class,
        local_field=local_field_name,
        manager_class=manager_class,
    )

    # Extract the navigation property name from the model class name
    model_name = external_model_class.__name__
    if model_name.endswith("Model"):
        nav_property_name = model_name[:-5].lower()  # Remove "Model" and lowercase
    else:
        nav_property_name = model_name.lower()

    # Create the ReferenceID class
    class ReferenceID(BaseModel):
        """ReferenceID for external model."""

        pass

    # Add the reference field dynamically
    setattr(
        ReferenceID,
        reference_field_name,
        Field(..., description=f"The ID of the related {nav_property_name}"),
    )

    class Optional(BaseModel):
        """Optional ReferenceID for external model."""

        pass

    # Add optional reference field
    setattr(
        Optional,
        reference_field_name,
        Field(None, description=f"The ID of the related {nav_property_name}"),
    )

    class Search(BaseModel):
        """Search ReferenceID for external model."""

        pass

    # Add search reference field
    setattr(
        Search,
        reference_field_name,
        Field(None, description=f"Search for {nav_property_name} ID"),
    )

    # Set the nested classes
    ReferenceID.Optional = Optional
    ReferenceID.Search = Search

    # Create the main reference model class
    class ExternalReferenceModel(ReferenceID):
        """Reference model for external resource."""

        pass

    # Add the navigation property
    setattr(ExternalReferenceModel, nav_property_name, nav_property)

    class OptionalReferenceModel(Optional):
        """Optional reference model for external resource."""

        pass

    # Add optional navigation property
    setattr(OptionalReferenceModel, nav_property_name, nav_property)

    # Set nested classes
    ExternalReferenceModel.Optional = OptionalReferenceModel

    return ExternalReferenceModel


class AbstractExternalManager(AbstractBLLManager):
    """
    Abstract base class for managers that work with external API models.

    Inherits from AbstractBLLManager to leverage hooks, validation, and other
    existing functionality while overriding the database operations to work
    with external APIs via the Provider Rotation System.
    """

    # External model class
    Model: Type[AbstractExternalModel] = None

    # Reference model class (for relationships)
    ReferenceModel: Type = None

    # Network model class (for API schemas)
    NetworkModel: Type = None

    def __init__(
        self,
        requester_id: str,
        rotation_manager=None,
        target_id: Optional[str] = None,
        target_team_id: Optional[str] = None,
        db=None,  # Ignored for external managers
        parent=None,
    ):
        """
        Initialize the external manager.

        Args:
            requester_id: ID of the user making the request
            rotation_manager: RotationManager instance for provider rotation
            target_id: ID of the target entity for operations
            target_team_id: ID of the target team
            db: Ignored for external managers
            parent: Parent manager for nested operations
        """
        # Initialize basic attributes without calling parent __init__
        # since external managers don't need database access
        self.requester_id = requester_id
        self.target_id = target_id
        self.target_team_id = target_team_id
        self._parent = parent
        self.rotation_manager = rotation_manager

        # External managers don't need database connections
        self.db = None
        self.requester = None  # External managers don't need user lookup

        # Set up API client for the model
        if self.Model and rotation_manager:
            self._api_client = AbstractExternalAPIClient(rotation_manager, self.Model)
        elif self.Model and hasattr(self, "provider_class"):
            # For testing or when no rotation manager is available,
            # create a direct API client that uses the provider class directly
            logger.debug(
                f"No rotation manager provided, creating direct API client for {self.provider_class.__name__}"
            )
            self._api_client = DirectProviderAPIClient(self.provider_class, self.Model)
        else:
            self._api_client = None

    @property
    def DB(self) -> AbstractExternalAPIClient:
        """
        Override DB property to return external API client instead of database model.
        This allows all existing AbstractBLLManager methods to work seamlessly
        with external APIs.
        """
        if self._api_client is None:
            raise RuntimeError(
                f"API client not initialized for {self.__class__.__name__}"
            )
        return self._api_client

    @property
    def db(self):
        """
        Provide db property for compatibility with AbstractBLLManager.
        External managers don't use database connections.
        """
        return None

    @db.setter
    def db(self, value):
        """
        Setter for db property that ignores assignments.
        External managers don't use database connections.
        """
        pass  # Ignore database assignments for external managers

    # All other methods (create, get, list, search, update, delete, batch_update,
    # batch_delete, hooks, validation, etc.) are inherited from AbstractBLLManager
    # and work automatically with the overridden DB property
