"""
Tests for Seed Templates Script
Author: Sowad Al-Mughni

Tests for the seed_templates.py script to verify:
- All 7 templates are created on fresh database
- Idempotency (running twice doesn't duplicate)
- Template updates when re-run
- JSON config parsing
"""

import pytest
import json
from src.models.referral import AssetPageTemplate
from src.models.user import db


class TestSeedTemplates:
    """Test suite for seed_templates.py"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self, app):
        """Clear templates before each test"""
        with app.app_context():
            # Remove all existing templates
            AssetPageTemplate.query.delete()
            db.session.commit()
    
    def test_seed_creates_all_templates(self, app):
        """Test that seed_templates creates all 7 expected templates"""
        from src.seed_templates import seed_templates
        
        with app.app_context():
            # Run the seed function
            templates = seed_templates()
            
            # Verify 7 templates were defined
            assert len(templates) == 7
            
            # Verify all templates exist in database
            db_templates = AssetPageTemplate.query.all()
            assert len(db_templates) == 7
    
    def test_expected_template_names(self, app):
        """Test that all expected template names are created"""
        from src.seed_templates import seed_templates
        
        expected_names = [
            'real-estate',
            'private-equity',
            'debt-instrument',
            'art-collectibles',
            'revenue-share',
            'default',
            'minimal'
        ]
        
        with app.app_context():
            seed_templates()
            
            for name in expected_names:
                template = AssetPageTemplate.query.filter_by(name=name).first()
                assert template is not None, f"Template '{name}' not found"
    
    def test_seed_idempotency(self, app):
        """Test that running seed twice doesn't create duplicates"""
        from src.seed_templates import seed_templates
        
        with app.app_context():
            # Run seed first time
            seed_templates()
            first_count = AssetPageTemplate.query.count()
            
            # Run seed second time
            seed_templates()
            second_count = AssetPageTemplate.query.count()
            
            # Should have same count
            assert first_count == second_count == 7
    
    def test_seed_updates_existing_template(self, app):
        """Test that seed updates existing templates instead of failing"""
        from src.seed_templates import seed_templates
        
        with app.app_context():
            # Create a template with old data
            old_template = AssetPageTemplate(
                name='real-estate',
                display_name='OLD NAME',
                description='Old description',
                asset_type='real-estate',
                config='{}',
                primary_color='#000000',
                secondary_color='#ffffff',
                is_premium=True  # Will be overwritten to False
            )
            db.session.add(old_template)
            db.session.commit()
            
            old_id = old_template.id
            
            # Run seed
            seed_templates()
            
            # Get the updated template
            updated = AssetPageTemplate.query.filter_by(name='real-estate').first()
            
            # Should keep same ID but update data
            assert updated.id == old_id
            assert updated.display_name == 'Real Estate Fund'
            assert 'property showcase' in updated.description.lower()
            assert updated.is_premium is False
    
    def test_template_config_is_valid_json(self, app):
        """Test that all template configs are valid JSON strings"""
        from src.seed_templates import seed_templates
        
        with app.app_context():
            seed_templates()
            
            templates = AssetPageTemplate.query.all()
            
            for template in templates:
                # Config should be parseable JSON
                try:
                    config = json.loads(template.config)
                    assert isinstance(config, dict)
                    assert 'sections' in config
                except json.JSONDecodeError:
                    pytest.fail(f"Template '{template.name}' has invalid JSON config")
    
    def test_real_estate_template_properties(self, app):
        """Test specific properties of real-estate template"""
        from src.seed_templates import seed_templates
        
        with app.app_context():
            seed_templates()
            
            template = AssetPageTemplate.query.filter_by(name='real-estate').first()
            
            assert template is not None
            assert template.display_name == 'Real Estate Fund'
            assert template.asset_type == 'real-estate'
            assert template.is_premium is False
            assert template.show_badges is True
            assert template.show_compliance is True
            
            # Check config
            config = json.loads(template.config)
            assert 'property_gallery' in config['sections']
            assert config.get('show_map') is True
    
    def test_art_collectibles_is_premium(self, app):
        """Test that art-collectibles template is marked as premium"""
        from src.seed_templates import seed_templates
        
        with app.app_context():
            seed_templates()
            
            template = AssetPageTemplate.query.filter_by(name='art-collectibles').first()
            
            assert template is not None
            assert template.is_premium is True
    
    def test_default_and_minimal_have_no_asset_type(self, app):
        """Test that default and minimal templates work for any asset type"""
        from src.seed_templates import seed_templates
        
        with app.app_context():
            seed_templates()
            
            default_template = AssetPageTemplate.query.filter_by(name='default').first()
            minimal_template = AssetPageTemplate.query.filter_by(name='minimal').first()
            
            # These should have None/null asset_type (work for any)
            assert default_template.asset_type is None
            assert minimal_template.asset_type is None
    
    def test_template_colors_are_valid_hex(self, app):
        """Test that all color values are valid hex colors"""
        from src.seed_templates import seed_templates
        import re
        
        hex_pattern = re.compile(r'^#[0-9a-fA-F]{6}$')
        
        with app.app_context():
            seed_templates()
            
            templates = AssetPageTemplate.query.all()
            
            for template in templates:
                assert hex_pattern.match(template.primary_color), \
                    f"Invalid primary_color for '{template.name}': {template.primary_color}"
                assert hex_pattern.match(template.secondary_color), \
                    f"Invalid secondary_color for '{template.name}': {template.secondary_color}"
    
    def test_template_background_types_are_valid(self, app):
        """Test that background types are one of expected values"""
        from src.seed_templates import seed_templates
        
        valid_types = {'solid', 'gradient', 'image'}
        
        with app.app_context():
            seed_templates()
            
            templates = AssetPageTemplate.query.all()
            
            for template in templates:
                assert template.background_type in valid_types, \
                    f"Invalid background_type for '{template.name}': {template.background_type}"


class TestTemplateModel:
    """Test AssetPageTemplate model"""
    
    def test_template_to_dict(self, app):
        """Test template serialization"""
        with app.app_context():
            template = AssetPageTemplate(
                name='test-template',
                display_name='Test Template',
                description='Test description',
                asset_type='test',
                config='{"sections": ["hero"]}',
                primary_color='#000000',
                secondary_color='#ffffff',
                background_type='solid',
                is_premium=False
            )
            db.session.add(template)
            db.session.commit()
            
            # Check that to_dict works if it exists
            if hasattr(template, 'to_dict'):
                data = template.to_dict()
                assert data['name'] == 'test-template'
                assert data['display_name'] == 'Test Template'
