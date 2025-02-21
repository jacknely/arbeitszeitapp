from typing import Optional
from unittest import TestCase
from uuid import UUID, uuid4

from arbeitszeit.use_cases import ShowCompanyWorkInviteDetailsResponse
from arbeitszeit_web.presenters.show_company_work_invite_details_presenter import (
    ShowCompanyWorkInviteDetailsPresenter,
)
from tests.translator import FakeTranslator

from .dependency_injection import get_dependency_injector
from .url_index import AnswerCompanyWorkInviteUrlIndexImpl


class PresenterTests(TestCase):
    def setUp(self) -> None:
        self.injector = get_dependency_injector()
        self.invite_url_index = self.injector.get(AnswerCompanyWorkInviteUrlIndexImpl)
        self.translator = self.injector.get(FakeTranslator)
        self.presenter = self.injector.get(ShowCompanyWorkInviteDetailsPresenter)

    def test_use_case_response_without_details_doesnt_render_to_view_model(
        self,
    ) -> None:
        view_model = self.presenter.render_response(self.make_error_response())
        self.assertIsNone(view_model)

    def test_successful_response_renders_to_view_model(self) -> None:
        view_model = self.presenter.render_response(self.make_response())
        self.assertIsNotNone(view_model)

    def test_successful_response_renders_accept_url_to_view_model(self) -> None:
        invite_id = uuid4()
        expected_url = self.invite_url_index.get_answer_company_work_invite_url(
            invite_id
        )
        view_model = self.presenter.render_response(
            self.make_response(invite_id=invite_id)
        )
        assert view_model
        self.assertEqual(view_model.answer_invite_url, expected_url)

    def test_that_company_name_shows_up_view_model(self) -> None:
        view_model = self.presenter.render_response(
            self.make_response(company_name="test company")
        )
        assert view_model
        self.assertEqual(
            view_model.explanation_text,
            self.translator.gettext(
                'The company "%(company)s" invites you to join them. Do you want to accept this invitation?'
            )
            % dict(company="test company"),
        )

    def make_response(
        self,
        invite_id: Optional[UUID] = None,
        company_name: str = "test company name",
    ) -> ShowCompanyWorkInviteDetailsResponse:
        if invite_id is None:
            invite_id = uuid4()
        return ShowCompanyWorkInviteDetailsResponse(
            details=ShowCompanyWorkInviteDetailsResponse.Details(
                company_name=company_name,
                invite_id=invite_id,
            )
        )

    def make_error_response(self) -> ShowCompanyWorkInviteDetailsResponse:
        return ShowCompanyWorkInviteDetailsResponse(details=None)
