from src.applications.models import Application, ApplicationStatus, ApplicationInitiator


async def get_by_id(app_id: int) -> Application | None:
    return await Application.filter(id=app_id).first()


async def exists(project_id: int, applicant_id: int) -> bool:
    return await Application.filter(project_id=project_id, applicant_id=applicant_id).exists()


async def count_active(project_id: int) -> int:
    active_statuses = (
        ApplicationStatus.accepted, ApplicationStatus.in_progress,
        ApplicationStatus.submitted, ApplicationStatus.approved, ApplicationStatus.completed,
    )
    return await Application.filter(project_id=project_id, status__in=active_statuses).count()


async def create_application(project_id: int, applicant_id: int,
                             cover_letter: str | None) -> Application:
    return await Application.create(
        project_id=project_id, applicant_id=applicant_id, cover_letter=cover_letter,
    )


async def save(application: Application) -> None:
    await application.save()


async def get_by_project(project_id: int, offset: int, limit: int) -> list[Application]:
    return await Application.filter(project_id=project_id).offset(offset).limit(limit)


async def get_by_applicant(applicant_id: int) -> list[Application]:
    return await Application.filter(applicant_id=applicant_id).order_by("-created_at")


async def create_invite(project_id: int, student_id: int,
                        message: str | None) -> Application:
    return await Application.create(
        project_id=project_id,
        applicant_id=student_id,
        cover_letter=message,
        status=ApplicationStatus.invited,
        initiator=ApplicationInitiator.company,
    )
