import formshare.plugins.utilities as u
from pyramid.httpexceptions import HTTPNotFound, HTTPFound
import json
from formshare.models import Odkform, map_to_schema
from formshare.processes.db.project import get_project_id_from_name
import requests
import logging
from urllib.parse import urljoin

log = logging.getLogger("formshare")


class EnketoStoreSettingsView(u.FormSharePrivateView):
    def __init__(self, request):
        u.FormSharePrivateView.__init__(self, request)
        self.checkCrossPost = False

    def process_view(self):
        if self.request.method == "POST":
            if self.user.super == 1:
                settings_data = self.get_post_dict()
                settings = u.FormShareSettings(self.request)
                if not settings.get("enketo"):
                    settings.store(
                        "enketo",
                        {"url": settings_data["url"], "key": settings_data["key"]},
                    )
                else:
                    settings.update(
                        "enketo",
                        {"url": settings_data["url"], "key": settings_data["key"]},
                    )
                self.returnRawViewResult = True
                return HTTPFound(
                    location=self.request.route_url("dashboard", userid=self.user.login)
                )
            else:
                raise HTTPNotFound
        else:
            raise HTTPNotFound


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
            settings = u.FormShareSettings(self.request)
            enketo_settings = settings.get("enketo")
            if enketo_settings:
                survey_data = {"server_url": form_url, "form_id": form_id}
                survey_data = json.loads(json.dumps(survey_data))
                enketo_survey_url = urljoin(enketo_settings["url"], "api/v2/survey")

                try:
                    r = requests.post(
                        enketo_survey_url,
                        data=survey_data,
                        auth=(enketo_settings["key"], ""),
                    )
                    if r.status_code == 200 or r.status_code == 201:
                        enketo_url = json.loads(r.text)["url"]
                        mapped_data = map_to_schema(Odkform, {"enketo_url": enketo_url})
                        self.request.dbsession.query(Odkform).filter(
                            Odkform.project_id == project_id
                        ).filter(Odkform.form_id == form_id).update(mapped_data)
                        return {"status": 200, "enketo_url": enketo_url, "message": ""}
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
                        "ENKETO PLUGIN. Unable to activate survey with URL {}. Error: {}".format(
                            form_url, str(e)
                        )
                    )
                    return {
                        "status": 500,
                        "enketo_url": "",
                        "message": self._("Error accessing Enketo server"),
                    }
            return {
                "status": 400,
                "enketo_url": "",
                "message": self._("Enketo hasn't been configured yet"),
            }
        else:
            raise HTTPNotFound
