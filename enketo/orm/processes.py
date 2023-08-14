from enketo.orm import EnketoFormMetadata
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
