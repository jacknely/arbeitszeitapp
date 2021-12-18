from dataclasses import dataclass
from uuid import UUID

from flask import Response

from arbeitszeit.use_cases import ListPlans, RequestCooperation
from arbeitszeit_web.list_plans import ListPlansPresenter
from arbeitszeit_web.request_cooperation import (
    RequestCooperationController,
    RequestCooperationPresenter,
)
from arbeitszeit_web.template import TemplateRenderer
from project.forms import RequestCooperationForm

from .http_404_view import Http404View


@dataclass
class RequestCooperationView:
    current_user_id: UUID
    form: RequestCooperationForm
    list_plans: ListPlans
    list_plans_presenter: ListPlansPresenter
    request_cooperation: RequestCooperation
    controller: RequestCooperationController
    presenter: RequestCooperationPresenter
    not_found_view: Http404View
    template_name: str
    template_renderer: TemplateRenderer

    def respond_to_get(self) -> Response:
        list_plans_view_model = self._get_list_plans_view_model()
        return Response(
            self.template_renderer.render_template(
                self.template_name,
                context=dict(list_plans_view_model=list_plans_view_model),
            )
        )

    def respond_to_post(self) -> Response:
        list_plans_view_model = self._get_list_plans_view_model()
        use_case_request = self.controller.import_form_data(self.form)
        if use_case_request is None:
            return self.not_found_view.get_response()
        if isinstance(use_case_request, self.controller.MalformedInputData):
            return self._handle_malformed_data(use_case_request)
        use_case_response = self.request_cooperation(use_case_request)
        view_model = self.presenter.present(use_case_response)
        return Response(
            self.template_renderer.render_template(
                self.template_name,
                context=dict(
                    view_model=view_model, list_plans_view_model=list_plans_view_model
                ),
            )
        )

    def _handle_malformed_data(
        self, result: RequestCooperationController.MalformedInputData
    ) -> Response:
        field = getattr(self.form, result.field)
        field.errors += (result.message,)
        return Response(
            self.template_renderer.render_template(
                self.template_name, context=dict(form=self.form)
            ),
            status=400,
        )

    def _get_list_plans_view_model(self):
        plans_list_response = self.list_plans(self.current_user_id)
        list_plans_view_model = self.list_plans_presenter.present(plans_list_response)
        return list_plans_view_model
