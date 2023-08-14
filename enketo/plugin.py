import formshare.plugins as plugins
import formshare.plugins.utilities as u
from .views import (
    GenerateEnketoURLView,
    EditThanksPageView,
    DisplayThanksPageView,
    PageUploadImageView,
    PageGetImageView,
)
import sys
import os
from formshare.processes.db.project import get_project_code_from_id
import requests
import json
from enketo.orm.processes import add_enketo_details, get_enketo_details
import logging
from urllib.parse import urljoin

log = logging.getLogger("formshare")


class Enketo(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.IConfig)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.ISchema)
    plugins.implements(plugins.IForm)
    plugins.implements(plugins.IDatabase)
    plugins.implements(plugins.IPrivateView)

    # Implement IRoutes functions
    def before_mapping(self, config):
        # We don't add any routes before the host application
        return []

    def after_mapping(self, config):
        # We add here a new route /json that returns a JSON
        custom_map = [
            u.add_route(
                "enketo_generate_urls",
                "/user/{userid}/project/{projcode}/form/{formid}/plugins/enketo/generate",
                GenerateEnketoURLView,
                None,
            ),
            u.add_route(
                "enketo_edit_thanks_page",
                "/user/{userid}/project/{projcode}/form/{formid}/plugins/enketo/edit_thanks",
                EditThanksPageView,
                "templates/enketo/edit_thanks.jinja2",
            ),
            u.add_route(
                "enketo_display_thanks_page",
                "/user/{userid}/project/{projcode}/form/{formid}/plugins/enketo/thank_you",
                DisplayThanksPageView,
                "templates/enketo/display_thanks.jinja2",
            ),
            u.add_route(
                "enketo_upload_image",
                "/user/{userid}/project/{projcode}/form/{formid}/plugins/enketo/upload_image",
                PageUploadImageView,
                "json",
            ),
            u.add_route(
                "enketo_download_image",
                "/user/{userid}/project/{projcode}/form/{formid}/plugins/enketo/image/{imageid}",
                PageGetImageView,
                None,
            ),
        ]

        return custom_map

    # Implement IConfig functions. This will allow us to extend the interface
    def update_config(self, config):
        # We add here the templates of the plugin to the config
        u.add_templates_directory(config, "templates")
        u.add_static_view(config, "enketo_static", "static")

    # Implement ITranslation functions
    def get_translation_directory(self):
        module = sys.modules["enketo"]
        return os.path.join(os.path.dirname(module.__file__), "locale")

    def get_translation_domain(self):
        return "enketo"

    # IDatabase
    def update_orm(self, config):
        config.include("enketo.orm")

    def update_extendable_tables(self, tables_allowed):
        return tables_allowed

    def update_extendable_modules(self, modules_allowed):
        return modules_allowed

    # IPrivateView
    def before_processing(self, route_name, request, class_data):
        pass

    def after_processing(self, route_name, request, class_data, context):
        if route_name == "form_details":
            project_id = context["formDetails"]["project_id"]
            form_id = context["formDetails"]["form_id"]
            context["enketo_metadata"] = get_enketo_details(
                request, project_id, form_id
            )
        return context

    # Implements ISchema. This will include a field called Enketo_url as part of a form DB schema
    def update_schema(self, config):
        return [u.add_field_to_form_schema("enketo_url", "Enketo URL")]

    # Implements IForm. This will allow us get and delete an Enketo URL when an ODK form is created,
    # updated or deleted

    def after_odk_form_checks(
        self,
        request,
        user,
        project,
        form,
        form_data,
        form_directory,
        survey_file,
        create_file,
        insert_file,
        itemsets_csv,
    ):
        return True, ""

    def before_adding_form(
        self, request, form_type, user_id, project_id, form_id, form_data
    ):
        return True, "", form_data

    def after_adding_form(
        self, request, form_type, user_id, project_id, form_id, form_data
    ):
        if form_type == "ODK":
            project_code = get_project_code_from_id(request, user_id, project_id)
            form_url = request.route_url(
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
                    request.registry.settings.get("enketo.url"), an_url["url"]
                )
                try:
                    # Online Survey
                    r = requests.post(
                        enketo_survey_url,
                        data=survey_data,
                        auth=(request.registry.settings.get("enketo.apikey"), ""),
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

            add_enketo_details(request, enketo_metadata)

    def before_updating_form(
        self, request, form_type, user_id, project_id, form_id, form_data
    ):
        return True, "", form_data

    def after_updating_form(
        self, request, form_type, user_id, project_id, form_id, form_data
    ):
        pass

    def before_deleting_form(self, request, form_type, user_id, project_id, form_id):
        return True, ""

    def after_deleting_form(
        self, request, form_type, user_id, project_id, form_id, form_data
    ):
        if form_type == "ODK":
            project_code = get_project_code_from_id(request, user_id, project_id)
            form_url = request.route_url(
                "project_details", userid=user_id, projcode=project_code
            )

            survey_data = {"server_url": form_url, "form_id": form_id}
            survey_data = json.loads(json.dumps(survey_data))
            enketo_survey_url = urljoin(
                request.registry.settings.get("enketo.url"), "api/v2/survey"
            )
            try:
                r = requests.delete(
                    enketo_survey_url,
                    data=survey_data,
                    auth=(request.registry.settings.get("enketo.apikey"), ""),
                )
                if r.status_code != 204:
                    log.error(
                        "ENKETO PLUGIN. Unable to deactivate survey with URL {}. Status code: {}".format(
                            form_url, r.status_code
                        )
                    )
            except Exception as e:
                log.error(
                    "ENKETO PLUGIN. Unable to delete survey with URL {}. Error: {}".format(
                        form_url, str(e)
                    )
                )
