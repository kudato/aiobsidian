"""Structural checks that apply to every resource class at once.

A resource that forgets `__slots__` still works, so nothing but a test
like this notices: the base class declares slots, the subclass does not,
and Python silently hands every instance a `__dict__` back.
"""

import importlib
import pkgutil

import pytest

import aiobsidian.cli
import aiobsidian.rest
from aiobsidian.cli._base import BaseCLIResource
from aiobsidian.rest._base import BaseResource


def _resource_classes(package, base):
    """Collect the resource classes a package defines itself.

    Args:
        package: Package to walk.
        base: Base class every resource inherits from.

    Returns:
        Resource classes, excluding those merely imported into a module.
    """
    found = []
    for info in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{package.__name__}.{info.name}")
        found.extend(
            obj
            for obj in vars(module).values()
            if isinstance(obj, type)
            and issubclass(obj, base)
            and obj.__module__ == module.__name__
        )
    return found


RESOURCES = _resource_classes(aiobsidian.cli, BaseCLIResource) + _resource_classes(
    aiobsidian.rest, BaseResource
)


def test_every_resource_module_was_discovered():
    # Guards the two tests below: an import that quietly stops working
    # would empty the parametrization and turn them into no-ops.
    assert len(RESOURCES) > 30


@pytest.mark.parametrize("resource", RESOURCES, ids=lambda cls: cls.__name__)
def test_resource_declares_slots(resource):
    assert "__slots__" in vars(resource), (
        f"{resource.__name__} inherits __slots__ without declaring its own, "
        f"so its instances carry a __dict__"
    )


@pytest.mark.parametrize("resource", RESOURCES, ids=lambda cls: cls.__name__)
def test_resource_instance_has_no_dict(resource):
    instance = resource.__new__(resource)
    assert not hasattr(instance, "__dict__")
    with pytest.raises(AttributeError):
        instance.typo = 1
