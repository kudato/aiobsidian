"""The public surface of each subpackage matches what it defines.

Adding a resource or a model is two steps — write the class, export it —
and the second one is easy to forget. These tests fail when a subpackage
defines something public that its `__all__` does not name.
"""

import importlib
import pkgutil

import pytest
from pydantic import BaseModel

import aiobsidian
import aiobsidian.cli
import aiobsidian.models
import aiobsidian.rest
from aiobsidian.cli._base import BaseCLIResource
from aiobsidian.rest._base import BaseResource


def _defined_names(package, base):
    """Collect the public classes a package defines across its modules.

    Args:
        package: Package to walk. Modules whose name starts with an
            underscore are private and are skipped.
        base: Base class the collected classes inherit from.

    Returns:
        Set of class names.
    """
    names = set()
    for info in pkgutil.iter_modules(package.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{package.__name__}.{info.name}")
        names |= {
            obj.__name__
            for obj in vars(module).values()
            if isinstance(obj, type)
            and issubclass(obj, base)
            and obj.__module__ == module.__name__
        }
    return names


PACKAGES = [
    (aiobsidian.cli, BaseCLIResource),
    (aiobsidian.rest, BaseResource),
    (aiobsidian.models, BaseModel),
]
IDS = [package.__name__ for package, _ in PACKAGES]


@pytest.mark.parametrize(("package", "base"), PACKAGES, ids=IDS)
def test_all_matches_what_the_package_defines(package, base):
    assert set(package.__all__) == _defined_names(package, base)


@pytest.mark.parametrize(("package", "base"), PACKAGES, ids=IDS)
def test_all_is_sorted_and_free_of_duplicates(package, base):
    assert package.__all__ == sorted(set(package.__all__))


@pytest.mark.parametrize(("package", "base"), PACKAGES, ids=IDS)
def test_every_exported_name_resolves(package, base):
    for name in package.__all__:
        assert getattr(package, name).__name__ == name


def test_root_reexports_every_model():
    for name in aiobsidian.models.__all__:
        assert getattr(aiobsidian, name) is getattr(aiobsidian.models, name)
