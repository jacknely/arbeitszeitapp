from unittest import TestCase
from uuid import uuid4

from arbeitszeit.use_cases.delete_offer import DeleteOfferResponse
from arbeitszeit_web.delete_offer import DeleteOfferPresenter

SUCCESSFUL_DELETE_RESPONSE = DeleteOfferResponse(
    offer_id=uuid4(),
    is_success=True,
)
FAILED_DELETE_RESPONSE = DeleteOfferResponse(
    offer_id=uuid4(),
    is_success=False,
)


class DeleteOfferPresenterTests(TestCase):
    def setUp(self):
        self.presenter = DeleteOfferPresenter()

    def test_that_a_notification_is_shown_when_deletion_was_successful(self):
        presentation = self.presenter.present(SUCCESSFUL_DELETE_RESPONSE)
        self.assertTrue(presentation.notifications)

    def test_that_a_notification_is_shown_when_deletion_was_a_failure(self):
        presentation = self.presenter.present(FAILED_DELETE_RESPONSE)
        self.assertTrue(presentation.notifications)

    def test_that_correct_notification_is_shown_when_deletion_was_successful(self):
        presentation = self.presenter.present(SUCCESSFUL_DELETE_RESPONSE)
        self.assertTrue(
            presentation.notifications[0]
            == f"Löschen des Angebots {SUCCESSFUL_DELETE_RESPONSE.offer_id} erfolgreich."
        )

    def test_that_correct_notification_is_shown_when_deletion_was_a_failure(self):
        presentation = self.presenter.present(FAILED_DELETE_RESPONSE)
        self.assertTrue(
            presentation.notifications[0]
            == f"Löschen des Angebots {FAILED_DELETE_RESPONSE.offer_id} nicht erfolgreich."
        )
