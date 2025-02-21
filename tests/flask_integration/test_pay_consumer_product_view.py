from datetime import datetime
from uuid import uuid4

from tests.data_generators import PlanGenerator

from .flask import ViewTestCase


class AuthenticatedMemberTests(ViewTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.plan_generator = self.injector.get(PlanGenerator)
        self.member, _, self.email = self.login_member()
        self.member = self.confirm_member(member=self.member, email=self.email)

    def test_get_returns_200_status(self) -> None:
        response = self.client.get("/member/pay_consumer_product")
        self.assertEqual(response.status_code, 200)

    def test_posting_without_data_results_in_400(self) -> None:
        response = self.client.post("/member/pay_consumer_product")
        self.assertEqual(response.status_code, 400)

    def test_posting_with_invalid_form_data_results_in_400(self) -> None:
        response = self.client.post(
            "/member/pay_consumer_product",
            data=dict(
                plan_id=uuid4(),
                amount="abc",
            ),
        )
        self.assertEqual(response.status_code, 400)

    def test_posting_with_valid_form_data_results_in_200(self) -> None:
        plan = self.plan_generator.create_plan(activation_date=datetime.min)
        response = self.client.post(
            "/member/pay_consumer_product",
            data=dict(
                plan_id=plan.id,
                amount=2,
            ),
        )
        self.assertEqual(response.status_code, 200)

    def test_posting_with_nonexisting_plan_id_results_in_404(self) -> None:
        response = self.client.post(
            "/member/pay_consumer_product",
            data=dict(
                plan_id=uuid4(),
                amount=2,
            ),
        )
        self.assertEqual(response.status_code, 404)


class AuthenticatedCompanyTests(ViewTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.login_company()

    def test_company_gets_redirected_when_trying_to_access_consumer_product_view(self):
        response = self.client.get("/member/pay_consumer_product")
        self.assertEqual(response.status_code, 302)
