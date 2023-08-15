from enketo.orm import EnketoFormMetadata, EnketoReturnContent
from formshare.models.schema import map_to_schema, map_from_schema
from sqlalchemy.exc import IntegrityError
import logging

log = logging.getLogger("formshare")


def get_enketo_details(request, project_id, form_id):
    res = (
        request.dbsession.query(EnketoFormMetadata)
        .filter(EnketoFormMetadata.project_id == project_id)
        .filter(EnketoFormMetadata.form_id == form_id)
        .first()
    )
    if res is None:
        return res
    else:
        return map_from_schema(res)


def add_enketo_details(request, enketo_details):
    _ = request.translate
    res = (
        request.dbsession.query(EnketoFormMetadata)
        .filter(EnketoFormMetadata.project_id == enketo_details["project_id"])
        .filter(EnketoFormMetadata.form_id == enketo_details["form_id"])
        .first()
    )
    if res is None:
        mapped_data = map_to_schema(EnketoFormMetadata, enketo_details)
        new_enketo_data = EnketoFormMetadata(**mapped_data)
        try:
            request.dbsession.add(new_enketo_data)
            request.dbsession.flush()
        except IntegrityError:
            request.dbsession.rollback()
            log.error(
                "Duplicated project {} {}".format(
                    mapped_data["project_id"], mapped_data["form_id"]
                )
            )
            return False, _("The form already exists")
        except Exception as e:
            request.dbsession.rollback()
            log.error(
                "Error {} while inserting project {} {}".format(
                    str(e), mapped_data["project_id"], mapped_data["form_id"]
                )
            )
            return False, str(e)
    else:
        mapped_data = map_to_schema(EnketoFormMetadata, enketo_details)
        request.dbsession.query(EnketoFormMetadata).filter(
            EnketoFormMetadata.project_id == enketo_details["project_id"]
        ).filter(EnketoFormMetadata.form_id == enketo_details["form_id"]).update(
            mapped_data
        )


def get_thanks_content(request, project_id, form_id, language_code=None):
    if language_code is None:
        res = (
            request.dbsession.query(EnketoFormMetadata)
            .filter(EnketoFormMetadata.project_id == project_id)
            .filter(EnketoFormMetadata.form_id == form_id)
            .first()
        )
    else:
        res = (
            request.dbsession.query(EnketoReturnContent)
            .filter(EnketoReturnContent.project_id == project_id)
            .filter(EnketoReturnContent.form_id == form_id)
            .filter(EnketoReturnContent.language_code == language_code)
            .first()
        )
    if res is not None:
        return map_from_schema(res)["return_url_content"]
    return None


def update_thanks_content(request, project_id, form_id, content, language_code=None):
    if language_code is None:
        request.dbsession.query(EnketoFormMetadata).filter(
            EnketoFormMetadata.project_id == project_id
        ).filter(EnketoFormMetadata.form_id == form_id).update(
            {"return_url_content": content}
        )
    else:
        request.dbsession.query(EnketoReturnContent).filter(
            EnketoReturnContent.project_id == project_id
        ).filter(EnketoReturnContent.form_id == form_id).filter(
            EnketoReturnContent.language_code == language_code
        ).update(
            {"return_url_content": content}
        )


def get_languages(request, project_id, form_id):
    res = (
        request.dbsession.query(EnketoReturnContent)
        .filter(EnketoReturnContent.project_id == project_id)
        .filter(EnketoReturnContent.form_id == form_id)
        .all()
    )
    return map_from_schema(res)


def delete_language(request, project_id, form_id, language_code):
    request.dbsession.query(EnketoReturnContent).filter(
        EnketoReturnContent.project_id == project_id
    ).filter(EnketoReturnContent.form_id == form_id).filter(
        EnketoReturnContent.language_code == language_code
    ).delete()


def add_language(request, project_id, form_id, language_code, language_name, content):
    _ = request.translate
    res = (
        request.dbsession.query(EnketoReturnContent)
        .filter(EnketoReturnContent.project_id == project_id)
        .filter(EnketoReturnContent.form_id == form_id)
        .filter(EnketoReturnContent.language_code == language_code)
        .first()
    )
    if res is None:
        language_details = {
            "project_id": project_id,
            "form_id": form_id,
            "language_code": language_code,
            "language_name": language_name,
            "return_url_content": content,
        }
        mapped_data = map_to_schema(EnketoReturnContent, language_details)
        new_language = EnketoReturnContent(**mapped_data)
        try:
            request.dbsession.add(new_language)
            request.dbsession.flush()
            return True, ""
        except IntegrityError:
            request.dbsession.rollback()
            log.error(
                "Duplicated language {} {} {}".format(
                    project_id, form_id, language_code
                )
            )
            return False, _("The form already exists")
        except Exception as e:
            request.dbsession.rollback()
            log.error(
                "Error {} while inserting language {} {} {}".format(
                    str(e), project_id, form_id, language_code
                )
            )
            return False, str(e)
