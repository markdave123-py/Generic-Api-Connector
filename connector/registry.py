from importlib import import_module
from typing import Dict, Type
from connector.base import BaseConnector

_PLUGINS: Dict[str, str] = {
    # logical-name → dotted-path where class lives
    "sim": "connectors.sim.SimConnector",
    # add new connectors here, or load from entry-points later
}


def get_connector(name: str) -> Type[BaseConnector]:
    """
    Dynamically import & return the connector class without
    hard-coding provider imports in application code.
    """
    dotted = _PLUGINS[name]
    mod_path, cls_name = dotted.rsplit(".", 1)
    cls = getattr(import_module(mod_path), cls_name)
    if not issubclass(cls, BaseConnector):
        raise TypeError(f"{cls_name} is not a BaseConnector")
    return cls
