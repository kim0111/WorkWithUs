from src.projects.models import Project, ProjectFile


async def get_project_with_applications(project_id: int) -> Project | None:
    return await Project.filter(id=project_id).prefetch_related("applications").first()


async def get_file_by_id(file_id: int) -> ProjectFile | None:
    return await ProjectFile.filter(id=file_id).first()


async def create_file(project_id: int, uploader_id: int, filename: str,
                      object_name: str, file_size: int, content_type: str | None,
                      file_type: str) -> ProjectFile:
    return await ProjectFile.create(
        project_id=project_id, uploader_id=uploader_id,
        filename=filename, object_name=object_name,
        file_size=file_size, content_type=content_type,
        file_type=file_type,
    )


async def list_files(project_id: int, file_type: str | None = None) -> list[ProjectFile]:
    filters: dict = {"project_id": project_id}
    if file_type:
        filters["file_type"] = file_type
    return await ProjectFile.filter(**filters).order_by("-created_at")


async def delete_file(pf: ProjectFile) -> None:
    await pf.delete()
