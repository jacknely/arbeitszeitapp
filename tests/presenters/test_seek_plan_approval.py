from typing import Optional
from unittest import TestCase
from uuid import uuid4

from arbeitszeit.use_cases.seek_approval import SeekApproval
from arbeitszeit_web.presenters.seek_plan_approval import SeekPlanApprovalPresenter
from tests.presenters.notifier import NotifierTestImpl

from .dependency_injection import get_dependency_injector


class PresenterTests(TestCase):
    def setUp(self) -> None:
        self.injector = get_dependency_injector()
        self.presenter = self.injector.get(SeekPlanApprovalPresenter)
        self.notifier = self.injector.get(NotifierTestImpl)

    def test_show_info_notification_when_plan_was_approved(self) -> None:
        response = self.create_response(is_approved=True)
        self.presenter.present_response(response)
        self.assertTrue(self.notifier.infos)

    def test_dont_show_info_notification_if_plan_was_not_approved(self) -> None:
        response = self.create_response(is_approved=False)
        self.presenter.present_response(response)
        self.assertFalse(self.notifier.infos)

    def test_dont_show_warning_when_plan_was_approved(self) -> None:
        response = self.create_response(is_approved=True)
        self.presenter.present_response(response)
        self.assertFalse(self.notifier.warnings)

    def test_show_warning_when_plan_was_not_approved(self) -> None:
        response = self.create_response(is_approved=False)
        self.presenter.present_response(response)
        self.assertTrue(self.notifier.warnings)

    def create_response(
        self, *, is_approved: Optional[bool] = None
    ) -> SeekApproval.Response:
        if is_approved is None:
            is_approved = True
        return SeekApproval.Response(
            is_approved=is_approved,
            reason="",
            new_plan_id=uuid4(),
        )
