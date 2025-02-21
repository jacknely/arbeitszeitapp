from dataclasses import dataclass, replace
from unittest import TestCase
from uuid import UUID, uuid4

from arbeitszeit.use_cases import RequestCooperationRequest
from arbeitszeit_web.malformed_input_data import MalformedInputData
from arbeitszeit_web.request_cooperation import RequestCooperationController
from tests.session import FakeSession
from tests.translator import FakeTranslator


@dataclass
class FakeRequestCooperationForm:
    plan_id: str
    cooperation_id: str

    def get_plan_id_string(self) -> str:
        return self.plan_id

    def get_cooperation_id_string(self) -> str:
        return self.cooperation_id


fake_form = FakeRequestCooperationForm(
    plan_id=str(uuid4()), cooperation_id=str(uuid4())
)


class RequestCooperationControllerTests(TestCase):
    def setUp(self) -> None:
        self.session = FakeSession()
        self.translator = FakeTranslator()
        self.controller = RequestCooperationController(
            session=self.session, translator=self.translator
        )

    def test_when_user_is_not_authenticated_then_we_cannot_get_a_use_case_request(
        self,
    ) -> None:
        self.session.set_current_user_id(None)
        self.assertIsNone(self.controller.import_form_data(form=fake_form))

    def test_when_user_is_authenticated_then_the_user_is_identified_in_use_case_request(
        self,
    ) -> None:
        expected_user_id = uuid4()
        self.session.set_current_user_id(expected_user_id)
        use_case_request = self.controller.import_form_data(form=fake_form)
        assert use_case_request is not None
        assert isinstance(use_case_request, RequestCooperationRequest)
        self.assertEqual(use_case_request.requester_id, expected_user_id)

    def test_returns_malformed_data_instance_if_plan_id_cannot_be_converted_to_uuid(
        self,
    ):
        malformed_form = replace(fake_form, plan_id="malformed plan id")
        self.session.set_current_user_id(uuid4())
        use_case_request = self.controller.import_form_data(form=malformed_form)
        assert use_case_request is not None
        assert isinstance(use_case_request, MalformedInputData)
        self.assertEqual(use_case_request.field, "plan_id")
        self.assertEqual(
            use_case_request.message, self.translator.gettext("Invalid plan ID.")
        )

    def test_returns_malformed_data_instance_if_coop_id_cannot_be_converted_to_uuid(
        self,
    ):
        malformed_form = replace(fake_form, cooperation_id="malformed coop id")
        self.session.set_current_user_id(uuid4())
        use_case_request = self.controller.import_form_data(form=malformed_form)
        assert use_case_request is not None
        assert isinstance(use_case_request, MalformedInputData)
        self.assertEqual(use_case_request.field, "cooperation_id")
        self.assertEqual(
            use_case_request.message,
            self.translator.gettext("Invalid cooperation ID."),
        )

    def test_controller_can_convert_plan_and_cooperation_id_into_correct_uuid(self):
        self.session.set_current_user_id(uuid4())
        use_case_request = self.controller.import_form_data(form=fake_form)
        assert use_case_request is not None
        assert isinstance(use_case_request, RequestCooperationRequest)
        self.assertEqual(use_case_request.plan_id, UUID(fake_form.plan_id))
        self.assertEqual(
            use_case_request.cooperation_id, UUID(fake_form.cooperation_id)
        )
