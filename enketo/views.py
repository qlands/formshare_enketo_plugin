import formshare.plugins.utilities as u
from pyramid.httpexceptions import HTTPNotFound, HTTPFound
import json
import uuid
import os
import shutil
import mimetypes
from enketo.orm.processes import (
    add_enketo_details,
    get_enketo_details,
    get_thanks_content,
    update_thanks_content,
    add_language,
    get_languages,
    delete_language,
)
from formshare.processes.odk import get_odk_path
from formshare.processes.db.project import (
    get_project_id_from_name,
    get_project_details,
    get_form_data,
)
import requests
import logging
from urllib.parse import urljoin
from pyramid.response import FileResponse
from webhelpers2.html import literal

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

            form_data = get_form_data(self.request, project_id, form_id)
            if form_data is None:
                raise HTTPNotFound

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
                    "return_url": self.request.route_url(
                        "enketo_display_thanks_page",
                        userid=user_id,
                        projcode=project_code,
                        formid=form_id,
                    ),
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

            next_page = self.request.params.get("next") or self.request.route_url(
                "form_details", userid=user_id, projcode=project_code, formid=form_id
            )
            self.request.session.flash(
                self._("The data collection URLs were generated")
            )
            return HTTPFound(next_page)

        else:
            raise HTTPNotFound


class EditThanksPageView(u.FormSharePrivateView):
    def process_view(self):
        user_id = self.request.matchdict["userid"]
        project_code = self.request.matchdict["projcode"]
        form_id = self.request.matchdict["formid"]
        project_id = get_project_id_from_name(self.request, user_id, project_code)

        if project_id is not None:
            access_type = self.get_project_access_level()
            if access_type >= 4:
                raise HTTPNotFound
            project_details = get_project_details(self.request, project_id)
            project_details["access_type"] = access_type
        else:
            raise HTTPNotFound

        form_data = get_form_data(self.request, project_id, form_id)
        if form_data is None:
            raise HTTPNotFound

        enketo_details = get_enketo_details(self.request, project_id, form_id)
        if enketo_details is None:
            raise HTTPNotFound

        language_code = self.request.params.get("language", None)
        if self.request.method == "POST":
            post_details = self.get_post_dict()
            if "translate" in post_details.keys():
                current_content = get_thanks_content(
                    self.request, project_id, form_id, None
                )
                language_code = post_details.get("language_code", "")
                language_name = post_details.get("language_name", "")
                if language_code != "" and language_name != "":
                    added, message = add_language(
                        self.request,
                        project_id,
                        form_id,
                        language_code,
                        language_name,
                        current_content,
                    )
                    if added:
                        self.returnRawViewResult = True
                        return HTTPFound(
                            self.request.route_url(
                                "enketo_edit_thanks_page",
                                userid=user_id,
                                projcode=project_code,
                                formid=form_id,
                                _query={"language": language_code},
                            )
                        )
            if "delete_language" in post_details.keys():
                delete_language(self.request, project_id, form_id, language_code)
                self.returnRawViewResult = True
                return HTTPFound(
                    self.request.route_url(
                        "enketo_edit_thanks_page",
                        userid=user_id,
                        projcode=project_code,
                        formid=form_id,
                    )
                )
            update_thanks_content(
                self.request,
                project_id,
                form_id,
                post_details["page_content"],
                language_code,
            )
            self.returnRawViewResult = True
            return HTTPFound(self.request.url)

        languages = get_languages(self.request, project_id, form_id)

        page_content = get_thanks_content(
            self.request, project_id, form_id, language_code
        )
        if page_content is None and language_code is not None:
            raise HTTPNotFound
        if page_content is None:
            page_content = self._("Thank you for your response")
        return {
            "projectDetails": project_details,
            "formDetails": form_data,
            "page_content": page_content,
            "language": language_code,
            "languages": languages,
        }


class PageUploadImageView(u.FormSharePrivateView):
    def __init__(self, request):
        u.FormSharePrivateView.__init__(self, request)
        self.checkCrossPost = False
        self.checkCSRF = False
        self.returnRawViewResult = True

    def process_view(self):
        if self.request.method == "POST":
            user_id = self.request.matchdict["userid"]
            project_code = self.request.matchdict["projcode"]
            form_id = self.request.matchdict["formid"]
            project_id = get_project_id_from_name(self.request, user_id, project_code)

            if project_id is not None:
                access_type = self.get_project_access_level()
                if access_type >= 4:
                    raise HTTPNotFound
                project_details = get_project_details(self.request, project_id)
                project_details["access_type"] = access_type
            else:
                raise HTTPNotFound

            form_data = get_form_data(self.request, project_id, form_id)
            if form_data is None:
                raise HTTPNotFound

            uid = str(uuid.uuid4())
            input_file = self.request.POST["upload"].file
            input_file_name = self.request.POST["upload"].filename.lower()
            name, extension = os.path.splitext(input_file_name)

            repository_path = get_odk_path(self.request)
            paths = ["forms", form_data["form_directory"], "enketo_upload"]
            upload_path = os.path.join(repository_path, *paths)
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)

            paths = [
                "forms",
                form_data["form_directory"],
                "enketo_upload",
                uid + extension,
            ]
            target_file = os.path.join(repository_path, *paths)
            input_file.seek(0)
            with open(target_file, "wb") as permanent_file:
                shutil.copyfileobj(input_file, permanent_file)
            return {
                "uploaded": 1,
                "url": self.request.route_url(
                    "enketo_download_image",
                    userid=user_id,
                    projcode=project_code,
                    formid=form_id,
                    imageid=uid + extension,
                ),
            }
        else:
            raise HTTPNotFound


class PageGetImageView(u.FormSharePublicView):
    def process_view(self):
        user_id = self.request.matchdict["userid"]
        project_code = self.request.matchdict["projcode"]
        form_id = self.request.matchdict["formid"]
        project_id = get_project_id_from_name(self.request, user_id, project_code)

        if project_id is None:
            raise HTTPNotFound

        form_data = get_form_data(self.request, project_id, form_id)
        if form_data is None:
            raise HTTPNotFound

        image_id = self.request.matchdict["imageid"]
        repository_path = get_odk_path(self.request)
        paths = ["forms", form_data["form_directory"], "enketo_upload", image_id]

        file_path = os.path.join(repository_path, *paths)
        content_type, content_enc = mimetypes.guess_type(file_path)
        response = FileResponse(
            file_path, request=self.request, content_type=content_type
        )
        self.returnRawViewResult = True
        return response


class DisplayThanksPageView(u.FormSharePublicView):
    def process_view(self):
        user_id = self.request.matchdict["userid"]
        project_code = self.request.matchdict["projcode"]
        form_id = self.request.matchdict["formid"]
        project_id = get_project_id_from_name(self.request, user_id, project_code)

        if project_id is None:
            raise HTTPNotFound

        project_details = get_project_details(self.request, project_id)

        form_data = get_form_data(self.request, project_id, form_id)
        if form_data is None:
            raise HTTPNotFound

        language_code = self.request.params.get("language", None)
        page_content = get_thanks_content(
            self.request, project_id, form_id, language_code
        )
        if page_content is None and language_code is not None:
            raise HTTPNotFound
        if page_content is None:
            page_content = self._("Thank you for your response")
        languages = get_languages(self.request, project_id, form_id)
        return {
            "page_content": literal(page_content),
            "languages": languages,
            "language": language_code,
            "projectDetails": project_details,
            "formDetails": form_data,
        }
