"""Resource classes of the CLI transport.

Reached in normal use through `ObsidianCLI`; exported here so they can be
named in a type hint without importing a private module.
"""

from .aliases import CLIAliasesResource
from .bases import CLIBasesResource
from .bookmarks import CLIBookmarksResource
from .commands import CLICommandsResource
from .daily import CLIDailyResource
from .dev import CLIDevResource
from .history import CLIHistoryResource
from .hotkeys import CLIHotkeysResource
from .links import CLILinksResource
from .outline import CLIOutlineResource
from .plugins import CLIPluginsResource
from .properties import CLIPropertiesResource
from .publish import CLIPublishResource
from .random_note import CLIRandomResource
from .search import CLISearchResource
from .snippets import CLISnippetsResource
from .sync import CLISyncResource
from .system import CLISystemResource
from .tabs import CLITabsResource
from .tags import CLITagsResource
from .tasks import CLITasksResource
from .templates import CLITemplatesResource
from .themes import CLIThemesResource
from .vault import CLIVaultResource
from .web import CLIWebResource
from .workspaces import CLIWorkspacesResource

__all__ = [
    "CLIAliasesResource",
    "CLIBasesResource",
    "CLIBookmarksResource",
    "CLICommandsResource",
    "CLIDailyResource",
    "CLIDevResource",
    "CLIHistoryResource",
    "CLIHotkeysResource",
    "CLILinksResource",
    "CLIOutlineResource",
    "CLIPluginsResource",
    "CLIPropertiesResource",
    "CLIPublishResource",
    "CLIRandomResource",
    "CLISearchResource",
    "CLISnippetsResource",
    "CLISyncResource",
    "CLISystemResource",
    "CLITabsResource",
    "CLITagsResource",
    "CLITasksResource",
    "CLITemplatesResource",
    "CLIThemesResource",
    "CLIVaultResource",
    "CLIWebResource",
    "CLIWorkspacesResource",
]
