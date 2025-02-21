from decimal import Decimal
from unittest import TestCase
from uuid import uuid4

from arbeitszeit.use_cases.get_member_profile_info import (
    GetMemberProfileInfoResponse,
    Workplace,
)
from arbeitszeit_web.get_member_profile_info import GetMemberProfileInfoPresenter
from tests.translator import FakeTranslator

from .dependency_injection import get_dependency_injector

RESPONSE_WITHOUT_WORKPLACES = GetMemberProfileInfoResponse(
    workplaces=[],
    account_balance=Decimal(0),
    name="worker",
    email="worker@cp.org",
    id=uuid4(),
)


RESPONSE_WITH_ONE_WORKPLACE = GetMemberProfileInfoResponse(
    workplaces=[
        Workplace(workplace_name="workplace_name", workplace_email="workplace@cp.org"),
    ],
    account_balance=Decimal(1.3333333),
    name="worker",
    email="worker@cp.org",
    id=uuid4(),
)


class GetMemberProfileInfoPresenterTests(TestCase):
    def setUp(self) -> None:
        self.injector = get_dependency_injector()
        self.translator = self.injector.get(FakeTranslator)
        self.presenter = self.injector.get(GetMemberProfileInfoPresenter)

    def test_that_welcome_line_is_correctly_translated(self) -> None:
        view_model = self.presenter.present(RESPONSE_WITHOUT_WORKPLACES)
        self.assertEqual(
            view_model.welcome_message,
            self.translator.gettext("Welcome, %s!") % RESPONSE_WITHOUT_WORKPLACES.name,
        )

    def test_that_workplaces_are_not_shown_when_worker_is_not_employed(self):
        presentation = self.presenter.present(RESPONSE_WITHOUT_WORKPLACES)
        self.assertFalse(presentation.show_workplaces)
        self.assertFalse(presentation.workplaces)

    def test_that_work_registration_info_is_shown_when_worker_is_not_employed(self):
        presentation = self.presenter.present(RESPONSE_WITHOUT_WORKPLACES)
        self.assertTrue(presentation.show_workplace_registration_info)

    def test_that_workplaces_are_shown_when_worker_is_employed(self):
        presentation = self.presenter.present(RESPONSE_WITH_ONE_WORKPLACE)
        self.assertTrue(presentation.show_workplaces)
        self.assertTrue(presentation.workplaces)

    def test_that_work_registration_info_is_not_shown_when_worker_is_employed(self):
        presentation = self.presenter.present(RESPONSE_WITH_ONE_WORKPLACE)
        self.assertFalse(presentation.show_workplace_registration_info)

    def test_that_account_balance_shows_only_two_digits_after_comma(self):
        presentation = self.presenter.present(RESPONSE_WITH_ONE_WORKPLACE)
        self.assertEqual(
            presentation.account_balance,
            self.translator.gettext("%.2f hours")
            % RESPONSE_WITH_ONE_WORKPLACE.account_balance,
        )
