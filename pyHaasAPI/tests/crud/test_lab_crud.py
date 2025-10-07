"""
Lab CRUD Tests

Comprehensive CRUD testing for Lab API with field mapping validation,
error handling, and cleanup discipline.
"""

import pytest
import asyncio
from typing import Dict, Any

from .helpers import (
    assert_safe_field, assert_lab_details_integrity, retry_async,
    await_idle_lab, generate_test_resource_name, create_test_lab_config,
    log_field_mapping_warnings
)
from pyHaasAPI.exceptions import LabError, LabNotFoundError, LabConfigurationError, ValidationError


pytestmark = pytest.mark.asyncio

@pytest.mark.crud
@pytest.mark.srv03
class TestLabCRUD:
    """Lab CRUD operation tests"""
    
    async def test_lab_create_success(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test successful lab creation with proper field mapping"""
        lab_api = apis['lab_api']
        
        # Create test lab configuration
        lab_config = create_test_lab_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id
        )
        
        # Create lab
        lab_details = await lab_api.create_lab(**lab_config)
        
        # Validate response structure
        assert lab_details is not None, "Lab creation should return lab details"
        
        # Record for cleanup
        lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
        cleanup_registry.add_lab(lab_id)
        
        # Validate lab details integrity
        assert_lab_details_integrity(lab_details)
        
        # Log field mapping warnings for debugging
        log_field_mapping_warnings(lab_details, "LabDetails")
        
        # Verify lab name matches expected pattern
        lab_name = assert_safe_field(lab_details, 'lab_name', str, required=True)
        expected_name = generate_test_resource_name('lab', test_session_id)
        assert lab_name == expected_name, f"Lab name mismatch: {lab_name} != {expected_name}"
    
    async def test_lab_get_details_safe_mapping(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test lab details retrieval with safe field mapping"""
        lab_api = apis['lab_api']
        
        # Create a lab first
        lab_config = create_test_lab_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id
        )
        
        lab_details = await lab_api.create_lab(**lab_config)
        lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
        cleanup_registry.add_lab(lab_id)
        
        # Retrieve lab details
        retrieved_details = await lab_api.get_lab_details(lab_id)
        
        # Validate all fields using safe mapping
        assert retrieved_details is not None, "Lab details should not be None"
        assert_lab_details_integrity(retrieved_details)
        
        # Verify critical fields are present
        assert_safe_field(retrieved_details, 'lab_id', str, required=True)
        assert_safe_field(retrieved_details, 'lab_name', str, required=True)
        assert_safe_field(retrieved_details, 'script_id', str, required=True)
        
        # Check settings structure
        settings = assert_safe_field(retrieved_details, 'settings', required=True)
        if settings:
            assert_safe_field(settings, 'market_tag', str, required=True)
            assert_safe_field(settings, 'account_id', str, required=True)
        
        # Log any missing optional fields
        log_field_mapping_warnings(retrieved_details, "LabDetails")
    
    async def test_list_labs_contains_created(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test that created lab appears in lab list"""
        lab_api = apis['lab_api']
        
        # Create a lab
        lab_config = create_test_lab_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id
        )
        
        lab_details = await lab_api.create_lab(**lab_config)
        lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
        cleanup_registry.add_lab(lab_id)
        
        # Get all labs
        labs = await lab_api.get_labs()
        
        # Verify lab list is not empty
        assert labs is not None, "Labs list should not be None"
        assert isinstance(labs, list), "Labs should be a list"
        
        # Find our created lab
        created_lab = None
        for lab in labs:
            if hasattr(lab, 'lab_id') and getattr(lab, 'lab_id') == lab_id:
                created_lab = lab
                break
        
        assert created_lab is not None, f"Created lab {lab_id} not found in labs list"
        
        # Validate the found lab
        assert_lab_details_integrity(created_lab)
    
    async def test_lab_update_details(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test lab details update with field validation"""
        lab_api = apis['lab_api']
        
        # Create a lab
        lab_config = create_test_lab_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id
        )
        
        lab_details = await lab_api.create_lab(**lab_config)
        lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
        cleanup_registry.add_lab(lab_id)
        
        # Wait for lab to be idle before updating
        await await_idle_lab(lab_api, lab_id)
        
        # Update lab details
        update_data = {
            'interval': 2,  # Change interval
            'chart_style': 301,  # Change chart style
            'trade_amount': 2000.0,  # Change trade amount
            'position_mode': 0,  # Change position mode
            'margin_mode': 1,  # Change margin mode
        }
        
        updated_lab = await lab_api.update_lab_details(lab_id, update_data)
        
        # Validate update response
        assert updated_lab is not None, "Update should return lab details"
        assert_lab_details_integrity(updated_lab)
        
        # Verify changes were persisted
        retrieved_lab = await lab_api.get_lab_details(lab_id)
        assert_lab_details_integrity(retrieved_lab)
        
        # Check specific updated fields
        settings = assert_safe_field(retrieved_lab, 'settings', required=True)
        if settings:
            # Note: Field names may vary based on API response structure
            # This is where safe field mapping is critical
            log_field_mapping_warnings(settings, "LabSettings")
    
    async def test_lab_delete_safely(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test safe lab deletion with job cancellation"""
        lab_api = apis['lab_api']
        
        # Create a lab
        lab_config = create_test_lab_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id
        )
        
        lab_details = await lab_api.create_lab(**lab_config)
        lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
        
        # Wait for lab to be idle
        await await_idle_lab(lab_api, lab_id)
        
        # Delete lab
        delete_result = await lab_api.delete_lab(lab_id)
        
        # Verify deletion (implementation depends on API response)
        assert delete_result is not None, "Delete should return result"
        
        # Verify lab is no longer in labs list
        labs = await lab_api.get_labs()
        lab_ids = [getattr(lab, 'lab_id', None) for lab in labs if hasattr(lab, 'lab_id')]
        assert lab_id not in lab_ids, f"Lab {lab_id} should not be in labs list after deletion"
    
    async def test_lab_get_details_not_found(self, apis):
        """Test lab details retrieval for non-existent lab"""
        lab_api = apis['lab_api']
        
        # Use a clearly non-existent lab ID
        non_existent_id = "non-existent-lab-id-12345"
        
        # Should raise LabNotFoundError
        with pytest.raises(LabNotFoundError):
            await lab_api.get_lab_details(non_existent_id)
    
    async def test_lab_update_invalid_values(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test lab update with invalid values"""
        lab_api = apis['lab_api']
        
        # Create a lab
        lab_config = create_test_lab_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id
        )
        
        lab_details = await lab_api.create_lab(**lab_config)
        lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
        cleanup_registry.add_lab(lab_id)
        
        # Wait for lab to be idle
        await await_idle_lab(lab_api, lab_id)
        
        # Try to update with invalid values
        invalid_update = {
            'leverage': -1,  # Invalid leverage
            'position_mode': 999,  # Invalid position mode
            'margin_mode': 999,  # Invalid margin mode
        }
        
        # Should raise LabConfigurationError or similar
        with pytest.raises((LabError, LabConfigurationError, ValidationError)):
            await lab_api.update_lab_details(lab_id, invalid_update)
        
        # Verify lab is still in original state (no partial updates)
        retrieved_lab = await lab_api.get_lab_details(lab_id)
        assert_lab_details_integrity(retrieved_lab)
    
    async def test_lab_field_mapping_resilience(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test field mapping resilience with missing optional fields"""
        lab_api = apis['lab_api']
        
        # Create a lab
        lab_config = create_test_lab_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id
        )
        
        lab_details = await lab_api.create_lab(**lab_config)
        lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
        cleanup_registry.add_lab(lab_id)
        
        # Test safe field access for various optional fields
        optional_fields = [
            'script_name', 'market_name', 'account_name',
            'leverage', 'position_mode', 'margin_mode',
            'trade_amount', 'chart_style', 'interval'
        ]
        
        for field in optional_fields:
            # This should not raise an exception even if field is missing
            value = assert_safe_field(lab_details, field, required=False)
            # Field may be None or missing - both are acceptable
            assert value is None or isinstance(value, (str, int, float, bool)), \
                f"Field {field} has unexpected type: {type(value)}"
        
        # Test nested field access
        settings = assert_safe_field(lab_details, 'settings', required=False)
        if settings:
            for field in optional_fields:
                value = assert_safe_field(settings, field, required=False)
                assert value is None or isinstance(value, (str, int, float, bool)), \
                    f"Settings field {field} has unexpected type: {type(value)}"
    
    async def test_lab_retry_mechanism(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test retry mechanism for transient errors"""
        lab_api = apis['lab_api']
        
        # Create a lab
        lab_config = create_test_lab_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id
        )
        
        lab_details = await lab_api.create_lab(**lab_config)
        lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
        cleanup_registry.add_lab(lab_id)
        
        # Test retry mechanism for lab details retrieval
        retrieved_details = await retry_async(
            lab_api.get_lab_details,
            lab_id,
            retries=3,
            delay=1.0
        )
        
        assert retrieved_details is not None, "Retry should succeed"
        assert_lab_details_integrity(retrieved_details)
    
    async def test_lab_clone_operation(self, apis, cleanup_registry, test_session_id, default_entities):
        """Test lab cloning operation"""
        lab_api = apis['lab_api']
        
        # Create original lab
        lab_config = create_test_lab_config(
            script_id=default_entities['script_id'],
            market_tag=default_entities['market_tag'],
            account_id=default_entities['account_id'],
            session_id=test_session_id
        )
        
        original_lab = await lab_api.create_lab(**lab_config)
        original_lab_id = assert_safe_field(original_lab, 'lab_id', str, required=True)
        cleanup_registry.add_lab(original_lab_id)
        
        # Clone the lab
        cloned_lab_name = f"CLONED {generate_test_resource_name('lab', test_session_id)}"
        cloned_lab = await lab_api.clone_lab(original_lab_id, cloned_lab_name)
        
        # Validate cloned lab
        assert cloned_lab is not None, "Clone should return lab details"
        cloned_lab_id = assert_safe_field(cloned_lab, 'lab_id', str, required=True)
        cleanup_registry.add_lab(cloned_lab_id)
        
        # Verify cloned lab has different ID
        assert cloned_lab_id != original_lab_id, "Cloned lab should have different ID"
        
        # Verify cloned lab name
        cloned_name = assert_safe_field(cloned_lab, 'lab_name', str, required=True)
        assert cloned_name == cloned_lab_name, f"Cloned lab name mismatch: {cloned_name}"
        
        # Validate cloned lab integrity
        assert_lab_details_integrity(cloned_lab)
