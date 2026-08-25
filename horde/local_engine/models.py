from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

TargetType = Literal[
    "hostname",
    "domain",
    "ipv4",
    "ipv6",
    "ip",
    "cidr",
    "url",
]


class ExecutionDefinition(BaseModel):
    executable: str
    args: List[str]
    timeout_seconds: int = Field(default=300, ge=1, le=86400)
    ai_agent_command: Optional[str] = None
    manual_runbook: Optional[Dict[str, Any]] = None


class ModuleDefinition(BaseModel):
    module_id: str
    name: str
    category: str = "Uncategorized"
    risk_level: Literal["Low", "Medium", "High", "Critical"]
    target_type: TargetType
    description: str = ""
    potential_consequences: List[str] = Field(default_factory=list)
    system_impact: str = ""
    execution: ExecutionDefinition


class ExecutionRequest(BaseModel):
    module_id: str
    target: str
    force_manual: bool = False
    user_acknowledged: bool = False
