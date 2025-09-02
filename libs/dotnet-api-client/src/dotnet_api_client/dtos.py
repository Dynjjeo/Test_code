from __future__ import annotations

from typing import Annotated
from datetime import datetime

from pydantic import Field, BaseModel

from dotnet_api_client.constants import FileStatus


class FileUpdateStatusRequestDto(BaseModel):
    file_id: Annotated[str, Field(serialization_alias="fileId")]
    status: FileStatus


class CVUpdateResponseDto(BaseModel):
    cv_id: Annotated[str, Field(serialization_alias="cvID")]
    name: str
    address: str
    email: str
    phone: str
    status: FileStatus
    additional_info: Annotated[str, Field(serialization_alias="additionalInfo")]
    profile_image_path: Annotated[str, Field(serialization_alias="profileImagePath")]


class JDUpdateResponseDto(BaseModel):
    product_id: str
    department_id: str
    position_id: str
    jd_id: str
    s3_save_path: str
    created_at: datetime
    updated_at: datetime | None = None
    jd_title: str
    hard_skills: list[str]
    soft_skills: list[str]
    education: list[str]
    experience: list[str]
    projects: list[str]
    languages: list[str]
    domain: list[str]
    status: FileStatus
