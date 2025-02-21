from dataclasses import dataclass
from typing import cast
from uuid import UUID

from flask import Response, redirect

from arbeitszeit.use_cases import (
    AnswerCompanyWorkInvite,
    ShowCompanyWorkInviteDetailsUseCase,
)
from arbeitszeit_flask.database import commit_changes
from arbeitszeit_flask.template import TemplateIndex, TemplateRenderer
from arbeitszeit_web.answer_company_work_invite import (
    AnswerCompanyWorkInviteController,
    AnswerCompanyWorkInviteForm,
    AnswerCompanyWorkInvitePresenter,
    AnswerCompanyWorkInviteRequest,
)
from arbeitszeit_web.controllers.show_company_work_invite_details_controller import (
    ShowCompanyWorkInviteDetailsController,
)
from arbeitszeit_web.presenters.show_company_work_invite_details_presenter import (
    ShowCompanyWorkInviteDetailsPresenter,
)

from .http_404_view import Http404View


@dataclass
class CompanyWorkInviteView:
    details_use_case: ShowCompanyWorkInviteDetailsUseCase
    details_presenter: ShowCompanyWorkInviteDetailsPresenter
    details_controller: ShowCompanyWorkInviteDetailsController
    answer_controller: AnswerCompanyWorkInviteController
    answer_presenter: AnswerCompanyWorkInvitePresenter
    answer_use_case: AnswerCompanyWorkInvite
    http_404_view: Http404View
    template_renderer: TemplateRenderer
    template_index: TemplateIndex

    def respond_to_get(self, invite_id: UUID) -> Response:
        use_case_request = self.details_controller.create_use_case_request(invite_id)
        if use_case_request is None:
            return self.http_404_view.get_response()
        use_case_response = self.details_use_case.show_company_work_invite_details(
            use_case_request
        )
        view_model = self.details_presenter.render_response(use_case_response)
        if view_model is None:
            return self.http_404_view.get_response()
        template = self.template_index.get_template_by_name(
            "show_company_work_invite_details"
        )
        return Response(
            self.template_renderer.render_template(
                template, dict(view_model=view_model)
            ),
            status=200,
        )

    @commit_changes
    def respond_to_post(
        self, form: AnswerCompanyWorkInviteForm, invite_id: UUID
    ) -> Response:
        use_case_request = self.answer_controller.import_form_data(
            form=form, invite_id=invite_id
        )
        assert isinstance(use_case_request, AnswerCompanyWorkInviteRequest)
        use_case_response = self.answer_use_case(use_case_request)
        view_model = self.answer_presenter.present(use_case_response)
        return cast(Response, redirect(view_model.redirect_url))
