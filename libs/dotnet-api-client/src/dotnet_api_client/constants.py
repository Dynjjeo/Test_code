from __future__ import annotations

from enum import IntEnum, StrEnum


class DotNetApiRoutes(StrEnum):
    FILES_UPDATE_STATUS = "/api/Resources/updatestatus"
    CVS_UPDATE_RESULTS = "/api/Candidate/receiveCVResults"
    JDS_UPDATE_RESULTS = "/api/JobDescription/receiveJDResults"


class FileStatus(IntEnum):
    NEW = 0
    IN_PROGRESS = 1
    SUCCESSFUL = 2
    FAILED = 3
