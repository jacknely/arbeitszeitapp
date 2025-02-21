from typing import Callable, Optional
from unittest import TestCase
from uuid import uuid4

from arbeitszeit.use_cases.register_accountant import RegisterAccountantUseCase
from arbeitszeit_web.presenters.register_accountant_presenter import (
    RegisterAccountantPresenter,
)
from tests.presenters.notifier import NotifierTestImpl
from tests.session import FakeSession
from tests.translator import FakeTranslator

from .dependency_injection import get_dependency_injector
from .url_index import AccountantDashboardUrlIndexImpl


class PresenterTests(TestCase):
    def setUp(self) -> None:
        self.injector = get_dependency_injector()
        self.presenter = self.injector.get(RegisterAccountantPresenter)
        self.notifier = self.injector.get(NotifierTestImpl)
        self.session = self.injector.get(FakeSession)
        self.translator = self.injector.get(FakeTranslator)
        self.dashboard_url_index = self.injector.get(AccountantDashboardUrlIndexImpl)

    def test_that_registration_rejection_results_in_error_message_shown(self) -> None:
        response = self.create_rejected_response()
        self.presenter.present_registration_result(response)
        self.assertTrue(self.notifier.warnings)

    def test_that_no_error_message_is_shown_when_registration_was_accepted(
        self,
    ) -> None:
        response = self.create_accepted_response()
        self.presenter.present_registration_result(response)
        self.assertFalse(self.notifier.warnings)

    def test_that_successful_registration_authenticates_user(self) -> None:
        response = self.create_accepted_response()
        self.presenter.present_registration_result(response)
        self.assertTrue(self.session.is_logged_in())

    def test_that_successful_registration_authenticates_user_with_correct_email(
        self,
    ) -> None:
        for email in self.example_email_addresses:
            with self.subTest():
                response = self.create_accepted_response(email=email)
                self.presenter.present_registration_result(response)
                self.assertLoggedIn(lambda l: l.email == email)

    def test_that_user_is_not_logged_in_when_failing_to_register(self) -> None:
        response = self.create_rejected_response()
        self.presenter.present_registration_result(response)
        self.assertFalse(self.session.is_logged_in())

    def test_that_user_is_logged_in_as_role_of_accountant(self) -> None:
        response = self.create_accepted_response()
        self.presenter.present_registration_result(response)
        self.assertLoggedIn(
            lambda l: l.user_role == FakeSession.UserRole.accountant,
        )

    def test_for_correct_error_message_when_failing_to_log_in(self) -> None:
        for email_address in self.example_email_addresses:
            with self.subTest():
                response = self.create_rejected_response(email=email_address)
                self.presenter.present_registration_result(response)
                self.assertEqual(
                    self.notifier.warnings[-1],
                    self.translator.gettext(
                        "Could not register %(email_address)s as an accountant"
                    )
                    % dict(email_address=email_address),
                )

    def test_redirect_to_accountant_dashboard_on_registration_success(self) -> None:
        response = self.create_accepted_response()
        view_model = self.presenter.present_registration_result(response)
        self.assertEqual(
            view_model.redirect_url,
            self.dashboard_url_index.get_accountant_dashboard_url(),
        )

    def test_do_not_redirect_when_registration_fails(self) -> None:
        response = self.create_rejected_response()
        view_model = self.presenter.present_registration_result(response)
        self.assertIsNone(view_model.redirect_url)

    def assertLoggedIn(
        self, condition: Optional[Callable[[FakeSession.LoginAttempt], bool]] = None
    ) -> None:
        self.assertTrue(self.session.is_logged_in())
        if condition:
            login_attempt = self.session.get_most_recent_login()
            assert login_attempt
            self.assertTrue(condition(login_attempt))

    def create_rejected_response(
        self, email: Optional[str] = None
    ) -> RegisterAccountantUseCase.Response:
        if email is None:
            email = "test@test.test"
        return RegisterAccountantUseCase.Response(
            is_accepted=False,
            user_id=None,
            email_address=email,
        )

    def create_accepted_response(
        self, email: Optional[str] = None
    ) -> RegisterAccountantUseCase.Response:
        if email is None:
            email = "a@b.c"
        return RegisterAccountantUseCase.Response(
            is_accepted=True,
            user_id=uuid4(),
            email_address=email,
        )

    example_email_addresses = [
        "test@test.test",
        "test2@test.test",
    ]
