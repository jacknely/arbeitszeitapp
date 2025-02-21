from uuid import uuid4

from tests.data_generators import CooperationGenerator, PlanGenerator

from .flask import ViewTestCase


class AuthenticatedCompanyTests(ViewTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.cooperation_generator = self.injector.get(CooperationGenerator)
        self.plan_generator = self.injector.get(PlanGenerator)
        self.company, _, self.email = self.login_company()
        self.company = self.confirm_company(company=self.company, email=self.email)

    def test_get_404_when_no_query_arguments_are_sent(
        self,
    ) -> None:
        url = "/company/end_cooperation/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_404_when_plan_does_not_exist(
        self,
    ) -> None:
        cooperation = self.cooperation_generator.create_cooperation()
        url = f"/company/end_cooperation?plan_id={uuid4()}&cooperation_id={str(cooperation.id)}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_404_when_coop_does_not_exist(
        self,
    ) -> None:
        plan = self.plan_generator.create_plan()
        url = (
            f"/company/end_cooperation?plan_id={str(plan.id)}&cooperation_id={uuid4()}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_404_when_coop_and_plan_do_exist_but_requester_is_neither_planner_nor_coordinator(
        self,
    ) -> None:
        plan = self.plan_generator.create_plan()
        cooperation = self.cooperation_generator.create_cooperation(plans=[plan])
        url = f"/company/end_cooperation?plan_id={str(plan.id)}&cooperation_id={str(cooperation.id)}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_302_when_coop_and_plan_do_exist_and_requester_is_planner(
        self,
    ) -> None:
        plan = self.plan_generator.create_plan(planner=self.company)
        cooperation = self.cooperation_generator.create_cooperation(plans=[plan])
        url = f"/company/end_cooperation?plan_id={str(plan.id)}&cooperation_id={str(cooperation.id)}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_get_302_when_coop_and_plan_do_exist_and_requester_is_coordinator(
        self,
    ) -> None:
        plan = self.plan_generator.create_plan()
        cooperation = self.cooperation_generator.create_cooperation(
            plans=[plan], coordinator=self.company
        )
        url = f"/company/end_cooperation?plan_id={str(plan.id)}&cooperation_id={str(cooperation.id)}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
