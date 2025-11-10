from django.test import TestCase

from ..models import MachineModel, MachineInstance


class MachineInstanceSlugTests(TestCase):
    """Tests for slug auto-generation and uniqueness."""

    def setUp(self):
        self.model = MachineModel.objects.create(
            name='The Addams Family',
            manufacturer='Williams',
            year=1992,
            era=MachineModel.ERA_SS,
        )

    def test_slug_auto_generation_from_model_name(self):
        """Slug should be auto-generated from model name when no name_override."""
        machine = MachineInstance.objects.create(
            model=self.model,
            location=MachineInstance.LOCATION_FLOOR,
        )
        self.assertEqual(machine.slug, 'the-addams-family')

    def test_slug_auto_generation_from_name_override(self):
        """Slug should be auto-generated from name_override when provided."""
        machine = MachineInstance.objects.create(
            model=self.model,
            name_override='TAF Special Edition',
            location=MachineInstance.LOCATION_FLOOR,
        )
        self.assertEqual(machine.slug, 'taf-special-edition')

    def test_slug_uniqueness_automatic_suffix(self):
        """Second instance with same name should get -2 suffix."""
        machine1 = MachineInstance.objects.create(
            model=self.model,
            location=MachineInstance.LOCATION_FLOOR,
        )
        machine2 = MachineInstance.objects.create(
            model=self.model,
            location=MachineInstance.LOCATION_WORKSHOP,
        )

        self.assertEqual(machine1.slug, 'the-addams-family')
        self.assertEqual(machine2.slug, 'the-addams-family-2')

    def test_slug_uniqueness_third_instance(self):
        """Third instance should get -3 suffix."""
        machine1 = MachineInstance.objects.create(model=self.model)
        machine2 = MachineInstance.objects.create(model=self.model)
        machine3 = MachineInstance.objects.create(model=self.model)

        self.assertEqual(machine1.slug, 'the-addams-family')
        self.assertEqual(machine2.slug, 'the-addams-family-2')
        self.assertEqual(machine3.slug, 'the-addams-family-3')

    def test_slug_manual_override(self):
        """Manually setting slug should be preserved."""
        machine = MachineInstance.objects.create(
            model=self.model,
            slug='custom-slug',
            location=MachineInstance.LOCATION_FLOOR,
        )
        self.assertEqual(machine.slug, 'custom-slug')

    def test_slug_update_on_save(self):
        """Changing name_override should not change existing slug."""
        machine = MachineInstance.objects.create(
            model=self.model,
            name_override='Original Name',
        )
        original_slug = machine.slug

        machine.name_override = 'New Name'
        machine.save()

        # Slug should remain unchanged
        self.assertEqual(machine.slug, original_slug)


class MachineInstanceQuerysetTests(TestCase):
    """Tests for MachineInstance custom querysets."""

    def setUp(self):
        self.model = MachineModel.objects.create(
            name='Test Machine',
            manufacturer='Test Corp',
            year=2000,
            era=MachineModel.ERA_SS,
        )

        # Create machines in different locations
        self.floor_machines = [
            MachineInstance.objects.create(
                model=self.model,
                name_override=f'Floor Machine {i}',
                location=MachineInstance.LOCATION_FLOOR,
            ) for i in range(3)
        ]

        self.workshop_machines = [
            MachineInstance.objects.create(
                model=self.model,
                name_override=f'Workshop Machine {i}',
                location=MachineInstance.LOCATION_WORKSHOP,
            ) for i in range(2)
        ]

        self.storage_machines = [
            MachineInstance.objects.create(
                model=self.model,
                name_override=f'Storage Machine {i}',
                location=MachineInstance.LOCATION_STORAGE,
            ) for i in range(1)
        ]

    def test_on_floor_queryset(self):
        """on_floor() should return only machines on the floor."""
        floor_machines = MachineInstance.objects.on_floor()
        self.assertEqual(floor_machines.count(), 3)
        for machine in floor_machines:
            self.assertEqual(machine.location, MachineInstance.LOCATION_FLOOR)

    def test_in_workshop_queryset(self):
        """in_workshop() should return only machines in workshop."""
        workshop_machines = MachineInstance.objects.in_workshop()
        self.assertEqual(workshop_machines.count(), 2)
        for machine in workshop_machines:
            self.assertEqual(machine.location, MachineInstance.LOCATION_WORKSHOP)

    def test_in_storage_queryset(self):
        """in_storage() should return only machines in storage."""
        storage_machines = MachineInstance.objects.in_storage()
        self.assertEqual(storage_machines.count(), 1)
        for machine in storage_machines:
            self.assertEqual(machine.location, MachineInstance.LOCATION_STORAGE)

    def test_by_name_with_name_override(self):
        """by_name() should find machines by their name_override."""
        results = MachineInstance.objects.by_name('Floor Machine 0')
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().name_override, 'Floor Machine 0')

    def test_by_name_with_model_name(self):
        """by_name() should find machines by their model name."""
        # Create a machine without name_override
        machine = MachineInstance.objects.create(
            model=self.model,
            location=MachineInstance.LOCATION_FLOOR,
        )
        results = MachineInstance.objects.by_name('Test Machine')
        self.assertIn(machine, results)

    def test_by_name_no_results(self):
        """by_name() should return empty queryset for non-existent name."""
        results = MachineInstance.objects.by_name('Nonexistent Machine')
        self.assertEqual(results.count(), 0)


class MachineInstanceNamePropertyTests(TestCase):
    """Tests for MachineInstance name property behavior."""

    def setUp(self):
        self.model = MachineModel.objects.create(
            name='Star Trek',
            manufacturer='Bally',
            year=1979,
            era=MachineModel.ERA_SS,
        )

    def test_name_property_uses_model_name_by_default(self):
        """name property should return model name when no override."""
        machine = MachineInstance.objects.create(
            model=self.model,
            location=MachineInstance.LOCATION_FLOOR,
        )
        self.assertEqual(machine.name, 'Star Trek')

    def test_name_property_uses_override_when_set(self):
        """name property should return name_override when set."""
        machine = MachineInstance.objects.create(
            model=self.model,
            name_override='Star Trek Limited Edition',
            location=MachineInstance.LOCATION_FLOOR,
        )
        self.assertEqual(machine.name, 'Star Trek Limited Edition')

    def test_name_property_falls_back_after_override_cleared(self):
        """name property should fall back to model name if override is cleared."""
        machine = MachineInstance.objects.create(
            model=self.model,
            name_override='Custom Name',
        )
        self.assertEqual(machine.name, 'Custom Name')

        machine.name_override = ''
        machine.save()
        self.assertEqual(machine.name, 'Star Trek')

    def test_str_uses_name_property(self):
        """__str__() should use the name property."""
        machine = MachineInstance.objects.create(
            model=self.model,
            name_override='Custom Name',
        )
        self.assertEqual(str(machine), 'Custom Name')

    def test_name_propagates_from_model_changes(self):
        """Changing model name should propagate to instances without override."""
        machine = MachineInstance.objects.create(model=self.model)
        self.assertEqual(machine.name, 'Star Trek')

        self.model.name = 'Star Trek: The Next Generation'
        self.model.save()
        machine.refresh_from_db()

        self.assertEqual(machine.name, 'Star Trek: The Next Generation')
