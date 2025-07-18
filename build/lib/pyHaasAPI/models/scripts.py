from typing import List, Optional, Any, Dict, Union
from pydantic import BaseModel, Field


class ScriptParameter(BaseModel):
    """Parameter definition for script components"""
    name: str = Field(..., description="Parameter name")
    type: int = Field(..., description="Parameter type")
    is_required: bool = Field(..., alias="IsRequired")
    is_hidden: bool = Field(..., alias="IsHidden")
    is_field: bool = Field(..., alias="IsField")
    allow_null: bool = Field(..., alias="AllowNull")
    description: str = Field(..., description="Parameter description")
    suggestion: Optional[List[int]] = Field(None, description="Suggested command types")
    is_input: bool = Field(..., alias="IsInput")


class ScriptConnection(BaseModel):
    """Connection between script components"""
    guid: str = Field(..., alias="Guid")
    points: List[Any] = Field(default_factory=list, description="Connection points")


class ScriptInput(BaseModel):
    """Input for a script component"""
    guid: str = Field(..., alias="Guid")
    connections: List[ScriptConnection] = Field(default_factory=list)
    parameter: ScriptParameter
    storage: str = Field(..., description="Stored value")


class ScriptOutput(BaseModel):
    """Output for a script component"""
    guid: str = Field(..., alias="Guid")
    connections: List[ScriptConnection] = Field(default_factory=list)
    parameter: ScriptParameter
    storage: str = Field(..., description="Stored value")


class ScriptSubOutput(BaseModel):
    """Sub-output for a script component"""
    guid: str = Field(..., alias="Guid")
    connections: List[ScriptConnection] = Field(default_factory=list)
    parameter: ScriptParameter
    storage: str = Field(..., description="Stored value")


class ScriptCommand(BaseModel):
    """Command definition for script components"""
    command_name: str = Field(..., alias="CommandName")
    command: int = Field(..., description="Command ID")
    command_type: int = Field(..., alias="CommandType")
    category: int = Field(..., description="Command category")
    description: str = Field(..., description="Command description")
    return_description: Optional[str] = Field(None, alias="ReturnDescription")
    parameters: List[ScriptParameter] = Field(default_factory=list)
    output_index: List[Any] = Field(default_factory=list, alias="OutputIndex")
    is_constant: bool = Field(..., alias="IsConstant")
    is_primary: bool = Field(..., alias="IsPrimary")
    requires_call: bool = Field(..., alias="RequiresCall")
    resizable: bool = Field(..., description="Whether component is resizable")
    output_hidden: bool = Field(..., alias="OutputHidden")
    output_type: int = Field(..., alias="OutputType")
    output_suggestions: List[int] = Field(default_factory=list, alias="OutputSuggestions")
    change_types: List[int] = Field(default_factory=list, alias="ChangeTypes")


class ScriptComponent(BaseModel):
    """Individual script component/block"""
    x: int = Field(..., alias="X", description="X coordinate")
    y: int = Field(..., alias="Y", description="Y coordinate")
    w: int = Field(..., alias="W", description="Width")
    h: int = Field(..., alias="H", description="Height")
    guid: str = Field(..., alias="Guid", description="Component GUID")
    type: int = Field(..., alias="Type", description="Component type")
    command_name: str = Field(..., alias="CommandName")
    inputs: List[ScriptInput] = Field(default_factory=list)
    output: ScriptOutput
    sub_outputs: List[ScriptSubOutput] = Field(default_factory=list, alias="SubOutputs")
    connector: ScriptInput = Field(..., description="Execute connector")
    command: ScriptCommand
    is_reversed: bool = Field(..., alias="IsReversed")
    is_mirrored: bool = Field(..., alias="IsMirrored")
    show_unused_parameters: bool = Field(..., alias="ShowUnusedParameters")
    needs_connector: bool = Field(..., alias="NeedsConnector")
    resizable: bool = Field(..., description="Whether component is resizable")
    disabled: bool = Field(..., description="Whether component is disabled")


class ScriptCompileResult(BaseModel):
    """Script compilation result"""
    is_valid: bool = Field(..., alias="IV")
    compilation: Optional[Union[str, dict]] = Field(None, alias="C")
    compile_result: List[str] = Field(default_factory=list, alias="CR")
    compile_log: List[str] = Field(default_factory=list, alias="CL")
    lce: List[Any] = Field(default_factory=list, alias="LCE")
    vce: List[Any] = Field(default_factory=list, alias="VCE")
    inputs: List[Dict[str, Any]] = Field(default_factory=list, alias="I")
    optimization: int = Field(..., alias="O")
    hide_tooltips: bool = Field(..., alias="HT")
    hide_outputs: bool = Field(..., alias="HO")
    show_suggestions: bool = Field(..., alias="SS")
    show_messages: bool = Field(..., alias="MS")
    show_logs: bool = Field(..., alias="LS")
    show_tooltips: bool = Field(..., alias="MT")
    show_descriptions: bool = Field(..., alias="OD")
    show_minimap: bool = Field(..., alias="MM")
    show_sidebar: bool = Field(..., alias="RSB")
    show_auto_update: bool = Field(..., alias="TAU")


class ScriptRecord(BaseModel):
    """Complete script record from GET_SCRIPT_RECORD"""
    script_components: str = Field(..., alias="SC", description="JSON string of script components")
    compile_result: ScriptCompileResult = Field(..., alias="CR")
    user_id: str = Field(..., alias="UID")
    script_id: str = Field(..., alias="SID")
    script_name: str = Field(..., alias="SN")
    script_description: str = Field(..., alias="SD")
    script_type: int = Field(..., alias="ST")
    script_status: int = Field(..., alias="SS")
    category_name: str = Field(..., alias="CN")
    is_compiled: bool = Field(..., alias="IC")
    is_valid: bool = Field(..., alias="IV")
    created_user: int = Field(..., alias="CU")
    updated_user: int = Field(..., alias="UU")
    folder_id: int = Field(..., alias="FID")


class GetScriptRecordRequest(BaseModel):
    """Request model for GET_SCRIPT_RECORD"""
    script_id: str = Field(..., alias="scriptid", description="Script ID to retrieve")
    interface_key: str = Field(..., alias="interfacekey")
    user_id: str = Field(..., alias="userid")


class GetScriptRecordResponse(BaseModel):
    """Response model for GET_SCRIPT_RECORD"""
    success: bool = Field(..., alias="Success")
    error: str = Field(..., alias="Error")
    data: ScriptRecord = Field(..., alias="Data") 