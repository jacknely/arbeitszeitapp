from unittest import TestCase
from uuid import uuid4

from hypothesis import given

from arbeitszeit.use_cases import ReadMessageSuccess
from arbeitszeit.user_action import UserAction, UserActionType
from arbeitszeit_web.read_message import ReadMessagePresenter
from tests.strategies import user_actions

from .dependency_injection import get_dependency_injector
from .user_action_resolver import UserActionResolver


class ReadMessagePresenterTests(TestCase):
    def setUp(self) -> None:
        self.injector = get_dependency_injector()
        self.action_link_resolver = self.injector.get(UserActionResolver)
        self.presenter = self.injector.get(ReadMessagePresenter)
        self.use_case_response = ReadMessageSuccess(
            message_title="test title",
            message_content="message content",
            sender_remarks=None,
            user_action=None,
        )

    def test_correct_message_title_from_use_case_is_propagated_to_view_model(
        self,
    ) -> None:
        self.use_case_response.message_title = "test title"
        view_model = self.presenter.present(self.use_case_response)
        self.assertEqual(view_model.title, "test title")

    def test_correct_message_content_is_shown_in_view_model(self) -> None:
        self.use_case_response.message_content = "test content"
        view_model = self.presenter.present(self.use_case_response)
        self.assertEqual(view_model.content, "test content")

    def test_dont_show_action_link_when_no_user_action_is_provided(self) -> None:
        self.use_case_response.user_action = None
        view_model = self.presenter.present(self.use_case_response)
        self.assertFalse(view_model.show_action_link)

    @given(user_action=user_actions())
    def test_show_action_link_when_user_action_is_provided(
        self, user_action: UserAction
    ) -> None:
        self.use_case_response.user_action = user_action
        view_model = self.presenter.present(self.use_case_response)
        self.assertTrue(view_model.show_action_link)

    def test_that_for_worker_invite_action_the_proper_action_link_is_rendered(
        self,
    ) -> None:
        action = UserAction(
            type=UserActionType.answer_invite,
            reference=uuid4(),
        )
        self.use_case_response.user_action = action
        view_model = self.presenter.present(self.use_case_response)
        self.assertEqual(
            view_model.action_link_reference,
            self.action_link_resolver.resolve_user_action_reference(action),
        )

    def test_that_for_anser_cooperation_request_the_proper_action_link_is_rendered(
        self,
    ) -> None:
        action = UserAction(
            type=UserActionType.answer_cooperation_request,
            reference=uuid4(),
        )
        self.use_case_response.user_action = action
        view_model = self.presenter.present(self.use_case_response)
        self.assertEqual(
            view_model.action_link_reference,
            self.action_link_resolver.resolve_user_action_reference(action),
        )

    def test_that_action_link_label_for_invite_action_is_rendered_properly(
        self,
    ) -> None:
        action = UserAction(
            type=UserActionType.answer_invite,
            reference=uuid4(),
        )
        self.use_case_response.user_action = action
        view_model = self.presenter.present(self.use_case_response)
        self.assertEqual(
            view_model.action_link_label,
            self.action_link_resolver.resolve_user_action_name(action),
        )

    def test_that_action_link_label_for_answer_cooperation_request_is_rendered_properly(
        self,
    ) -> None:
        action = UserAction(
            type=UserActionType.answer_cooperation_request,
            reference=uuid4(),
        )
        self.use_case_response.user_action = action
        view_model = self.presenter.present(self.use_case_response)
        self.assertEqual(
            view_model.action_link_label,
            self.action_link_resolver.resolve_user_action_name(action),
        )
