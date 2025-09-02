from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import UTC, datetime

import httpx

from dotnet_api_client.dtos import CVUpdateResponseDto, JDUpdateResponseDto
from dotnet_api_client.constants import DotNetApiRoutes


if TYPE_CHECKING:
    from dotnet_api_client.constants import FileStatus


class DotNetApiClient:
    def __init__(self, api_url: str) -> None:
        self._client = httpx.Client(
            base_url=api_url,
            verify=False,  # noqa: S501
        )

    def update_file_status(self, file_id: str, status: FileStatus) -> None:
        response = self._client.post(
            url=DotNetApiRoutes.FILES_UPDATE_STATUS,
            params={
                "fileId": file_id,
                "status": status,
            },
        )

        response.raise_for_status()

    def update_cv_result(
        self,
        file_id: str,
        status: FileStatus,
        result: CVUpdateResponseDto | None,
    ) -> None:
        if result is None:
            result = CVUpdateResponseDto(
                cv_id=file_id,
                status=status,
                name="",
                address="",
                email="",
                phone="",
                additional_info="",
                profile_image_path="",
            )

        response = self._client.put(
            url=DotNetApiRoutes.CVS_UPDATE_RESULTS,
            json=[result.model_dump(by_alias=True, mode="json")],
        )

        response.raise_for_status()

    def update_jd_result(
        self,
        file_id: str,
        status: FileStatus,
        result: JDUpdateResponseDto | None,
    ) -> None:
        if result is None:
            result = JDUpdateResponseDto(
                jd_id=file_id,
                status=status,
                product_id="",
                department_id="",
                position_id="",
                s3_save_path="",
                created_at=datetime.now(UTC),
                updated_at=None,
                jd_title="",
                hard_skills=[],
                soft_skills=[],
                education=[],
                experience=[],
                projects=[],
                languages=[],
                domain=[],
            )

        response = self._client.post(
            url=DotNetApiRoutes.JDS_UPDATE_RESULTS,
            json={**result.model_dump(mode="json")},
        )

        response.raise_for_status()
