from pydantic import BaseModel
from typing import Literal


class ToolRequirement(BaseModel):
    tool_name: str
    display_name: str
    description: str
    platform_available: bool = True


class StaffRole(BaseModel):
    role: str
    agent_type: str
    description: str
    is_suggested: bool = True


class DepartmentSuggestion(BaseModel):
    dept_type: str
    name: str
    description: str
    is_required: bool
    manager_title: str
    manager_description: str
    tools: list[ToolRequirement]
    suggested_staff: list[StaffRole]


class DepartmentSuggestRequest(BaseModel):
    business_id: str
    business_profile: dict


class DepartmentSuggestResponse(BaseModel):
    business_id: str
    departments: list[DepartmentSuggestion]


class ActivateDepartmentsRequest(BaseModel):
    business_id: str
    dept_types: list[str]


class ToolSetupItem(BaseModel):
    tool_name: str
    display_name: str
    dept_type: str
    dept_name: str
    key_source: Literal["platform", "user"] = "platform"
    user_key: str | None = None


class ToolSetupRequest(BaseModel):
    business_id: str
    tools: list[ToolSetupItem]


class HireStaffRequest(BaseModel):
    business_id: str
    department_id: str
    roles: list[str]


class LaunchConfigRequest(BaseModel):
    business_id: str
    autonomy: Literal["full_auto", "major_decisions", "step_by_step"]
    comm_channel: Literal["email", "slack", "discord", "sms"]
    comm_config: dict
