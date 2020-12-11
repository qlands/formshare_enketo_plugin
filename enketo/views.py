import formshare.plugins.utilities as u
from pyramid.httpexceptions import HTTPNotFound
import json
from formshare.models import Odkform, map_to_schema
from formshare.processes.db.project import get_project_id_from_name
import requests
import logging
from urllib.parse import urljoin

log = logging.getLogger("formshare")


class GenerateEnketoURLView(u.FormSharePrivateView):
    def __init__(self, request):
        u.FormSharePrivateView.__init__(self, request)
        self.checkCrossPost = False

    def process_view(self):
        if self.request.method == "GET":
            self.returnRawViewResult = True
            if self.get_project_access_level() >= 4:
                raise HTTPNotFound

            user_id = self.request.matchdict.get("userid", None)
            project_code = self.request.matchdict.get("projcode", None)
            form_id = self.request.matchdict.get("formid", None)
            project_id = get_project_id_from_name(self.request, user_id, project_code)

            form_url = self.request.route_url(
                "project_details", userid=user_id, projcode=project_code
            )

            survey_data = {"server_url": form_url, "form_id": form_id}
            survey_data = json.loads(json.dumps(survey_data))
            enketo_survey_url = urljoin(
                self.request.registry.settings.get("enketo.url"), "api/v2/survey"
            )
            try:
                r = requests.post(
                    enketo_survey_url,
                    data=survey_data,
                    auth=(self.request.registry.settings.get("enketo.apikey"), ""),
                )
                if r.status_code == 200 or r.status_code == 201:
                    enketo_survey_url = urljoin(
                        self.request.registry.settings.get("enketo.url"),
                        "api/v2/survey/offline",
                    )
                    r = requests.post(
                        enketo_survey_url,
                        data=survey_data,
                        auth=(self.request.registry.settings.get("enketo.apikey"), ""),
                    )
                    if r.status_code == 200 or r.status_code == 201:
                        enketo_url = json.loads(r.text)["offline_url"]
                        mapped_data = map_to_schema(Odkform, {"enketo_url": enketo_url})
                        self.request.dbsession.query(Odkform).filter(
                            Odkform.project_id == project_id
                        ).filter(Odkform.form_id == form_id).update(mapped_data)
                        return {"status": 200, "enketo_url": enketo_url, "message": ""}
                    else:
                        log.error(
                            "ENKETO PLUGIN. Unable to activate offline survey with URL {}. Status code: {}".format(
                                form_url, r.status_code
                            )
                        )
                        return {
                            "status": r.status_code,
                            "enketo_url": "",
                            "message": self._("Error configuring Enketo offline"),
                        }
                else:
                    log.error(
                        "ENKETO PLUGIN. Unable to activate survey with URL {}. Status code: {}".format(
                            form_url, r.status_code
                        )
                    )
                    return {
                        "status": r.status_code,
                        "enketo_url": "",
                        "message": self._("Error configuring Enketo "),
                    }
            except Exception as e:
                log.error(
                    "ENKETO PLUGIN Exception. Unable to activate survey with URL {}. Error: {}".format(
                        form_url, str(e)
                    )
                )
                return {
                    "status": 500,
                    "enketo_url": "",
                    "message": self._("Error accessing Enketo server"),
                }
        else:
            raise HTTPNotFound
