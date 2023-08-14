import formshare.plugins.utilities as u
from pyramid.httpexceptions import HTTPNotFound
import json
from enketo.orm.processes import add_enketo_details
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
        if self.request.method == "POST":
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

            enketo_urls = [
                {"url": "api/v2/survey", "result": None, "result_key": "url"},
                {
                    "url": "api/v2/survey/offline",
                    "result": None,
                    "result_key": "offline_url",
                },
                {
                    "url": "api/v2/survey/single",
                    "result": None,
                    "result_key": "single_url",
                },
                {
                    "url": "api/v2/survey/single/once",
                    "result": None,
                    "result_key": "single_once_url",
                },
                {
                    "url": "api/v2/survey/preview",
                    "result": None,
                    "result_key": "preview_url",
                },
            ]

            for an_url in enketo_urls:
                survey_data = {
                    "server_url": form_url,
                    "form_id": form_id,
                    "return_url": "",
                }
                survey_data = json.loads(json.dumps(survey_data))
                enketo_survey_url = urljoin(
                    self.request.registry.settings.get("enketo.url"), an_url["url"]
                )
                try:
                    # Online Survey
                    r = requests.post(
                        enketo_survey_url,
                        data=survey_data,
                        auth=(self.request.registry.settings.get("enketo.apikey"), ""),
                    )
                    if r.status_code == 200 or r.status_code == 201:
                        an_url["result"] = json.loads(r.text)[an_url["result_key"]]
                    else:
                        log.error(
                            "ENKETO PLUGIN. Unable to activate off-line survey with URL {}. Status code: {}".format(
                                an_url["url"], r.status_code
                            )
                        )
                except Exception as e:
                    log.error(
                        "ENKETO PLUGIN Exception. Unable to activate survey with URL {}. Error: {}".format(
                            an_url["url"], str(e)
                        )
                    )
            enketo_metadata = {"project_id": project_id, "form_id": form_id}
            if enketo_urls[0]["result"] is not None:
                enketo_metadata["url_multi"] = enketo_urls[0]["result"]
            if enketo_urls[1]["result"] is not None:
                enketo_metadata["url_off_multi"] = enketo_urls[1]["result"]
            if enketo_urls[2]["result"] is not None:
                enketo_metadata["url_single"] = enketo_urls[2]["result"]
            if enketo_urls[3]["result"] is not None:
                enketo_metadata["url_once"] = enketo_urls[3]["result"]
            if enketo_urls[4]["result"] is not None:
                enketo_metadata["url_testing"] = enketo_urls[4]["result"]

            add_enketo_details(self.request, enketo_metadata)

        else:
            raise HTTPNotFound
