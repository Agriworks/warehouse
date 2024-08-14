
from dataclasses import dataclass
from typing import Dict


@dataclass
class OrchestratorConfig:
    pipelines: Dict[str, str]
    # other configuration options
