from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException
from src.core.activity import log_activity
from src.applications import repository
from src.applications.models import Application, ApplicationStatus
from src.projects.models import Project
from src.users.models import User, RoleEnum, StudentProfile
from src.teams import repository as teams_repo
from src.teams.models import TeamRole


VALID_TRANSITIONS = {
    ApplicationStatus.pending: [ApplicationStatus.accepted, ApplicationStatus.rejected],
    ApplicationStatus.accepted: [ApplicationStatus.in_progress],
    ApplicationStatus.in_progress: [ApplicationStatus.submitted],
    ApplicationStatus.submitted: [ApplicationStatus.approved, ApplicationStatus.revision_requested],
    ApplicationStatus.revision_requested: [ApplicationStatus.submitted],
    ApplicationStatus.approved: [ApplicationStatus.completed],
}


def _append_history(app: Application, status: str, actor: User,
                    note: Optional[str] = None) -> list[dict]:
    entry = {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor_id": actor.id,
        "actor_name": actor.full_name or actor.username,
        "note": note,
    }
    history = list(app.status_history or [])
    history.append(entry)
    return history


async def apply(user: User, project_id: int, cover_letter: str | None) -> tuple[Application, Project]:
    if user.role != RoleEnum.student:
        raise HTTPException(status_code=403, detail="Only students can apply")

    project = await Project.filter(id=project_id).prefetch_related("applications").first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.status.value != "open":
        raise HTTPException(status_code=400, detail="Project is not open")
    if await repository.exists(project_id, user.id):
        raise HTTPException(status_code=400, detail="Already applied")

    active_count = await repository.count_active(project_id)
    if active_count >= project.max_participants:
        raise HTTPException(status_code=400, detail="Project has reached maximum number of participants")

    application = await repository.create_application(project_id, user.id, cover_letter)
    application.status_history = _append_history(application, "pending", user, None)
    await repository.save(application)

    await log_activity(user.id, "apply", f"Applied to project '{project.title}'",
                       "application", application.id)

    return application, project


async def update_status(app_id: int, new_status: ApplicationStatus, note: str | None,
                        user: User) -> tuple[Application, Project]:
    application = await repository.get_by_id(app_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    project = await Project.filter(id=application.project_id).first()

    is_owner = project.owner_id == user.id
    is_applicant = application.applicant_id == user.id
    is_admin = user.role == RoleEnum.admin

    owner_statuses = {ApplicationStatus.accepted, ApplicationStatus.rejected,
                      ApplicationStatus.approved, ApplicationStatus.revision_requested,
                      ApplicationStatus.completed}
    applicant_statuses = {ApplicationStatus.in_progress, ApplicationStatus.submitted}

    if new_status in owner_statuses and not (is_owner or is_admin):
        raise HTTPException(status_code=403, detail="Only project owner can perform this action")
    if new_status in applicant_statuses and not is_applicant:
        raise HTTPException(status_code=403, detail="Only applicant can perform this action")

    allowed = VALID_TRANSITIONS.get(application.status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {application.status.value} to {new_status.value}. "
                   f"Allowed: {[s.value for s in allowed]}",
        )

    application.status = new_status
    if new_status == ApplicationStatus.submitted and note:
        application.submission_note = note
    if new_status == ApplicationStatus.revision_requested and note:
        application.revision_note = note
    application.status_history = _append_history(application, new_status.value, user, note)
    await repository.save(application)

    if new_status == ApplicationStatus.accepted:
        existing = await teams_repo.get_by_project_and_user(project.id, application.applicant_id)
        if not existing:
            has_lead = await teams_repo.has_lead(project.id)
            await teams_repo.add_member(
                project.id, application.applicant_id,
                TeamRole.other, is_lead=not has_lead,
            )

    if new_status == ApplicationStatus.completed:
        profile = await StudentProfile.filter(user_id=application.applicant_id).first()
        if profile:
            profile.completed_projects_count = (profile.completed_projects_count or 0) + 1
            await profile.save(update_fields=["completed_projects_count"])

    await log_activity(user.id, "update_application_status",
                       f"Changed status to {new_status.value}", "application", app_id)

    return application, project


async def get_project_applications(project_id: int, page: int, size: int,
                                   user: User) -> list[Application]:
    project = await Project.filter(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != user.id and user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    return await repository.get_by_project(project_id, (page - 1) * size, size)


async def get_my_applications(user: User) -> list[Application]:
    return await repository.get_by_applicant(user.id)
