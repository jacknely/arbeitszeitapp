from dataclasses import replace
from decimal import Decimal
from unittest import TestCase
from uuid import uuid4

from arbeitszeit.plan_summary import PlanSummary
from arbeitszeit_web.plan_summary_service import PlanSummaryServiceImpl
from tests.translator import FakeTranslator

from .dependency_injection import get_dependency_injector
from .url_index import CompanySummaryUrlIndex, CoopSummaryUrlIndexTestImpl

PLAN_SUMMARY = PlanSummary(
    plan_id=uuid4(),
    is_active=True,
    planner_id=uuid4(),
    planner_name="test planner name",
    product_name="test product name",
    description="test description",
    timeframe=7,
    active_days=5,
    production_unit="Piece",
    amount=100,
    means_cost=Decimal(1),
    resources_cost=Decimal(2),
    labour_cost=Decimal(3),
    is_public_service=False,
    price_per_unit=Decimal("0.061"),
    is_available=True,
    is_cooperating=True,
    cooperation=uuid4(),
)


class PlanSummaryServiceTests(TestCase):
    def setUp(self) -> None:
        self.injector = get_dependency_injector()
        self.coop_url_index = self.injector.get(CoopSummaryUrlIndexTestImpl)
        self.company_url_index = self.injector.get(CompanySummaryUrlIndex)
        self.translator = self.injector.get(FakeTranslator)
        self.service = self.injector.get(PlanSummaryServiceImpl)

    def test_plan_id_is_displayed_correctly_as_tuple_of_strings(self):
        plan_summary = self.service.get_plan_summary(PLAN_SUMMARY)
        self.assertTupleEqual(
            plan_summary.plan_id,
            (self.translator.gettext("Plan ID"), str(PLAN_SUMMARY.plan_id)),
        )

    def test_active_status_is_displayed_correctly_as_tuple_of_strings(self):
        plan_summary = self.service.get_plan_summary(PLAN_SUMMARY)
        self.assertTupleEqual(
            plan_summary.activity_string,
            (self.translator.gettext("Status"), self.translator.gettext("Active")),
        )

    def test_inactive_status_is_displayed_correctly_as_tuple_of_strings(self):
        response = replace(
            PLAN_SUMMARY,
            is_active=False,
        )
        plan_summary = self.service.get_plan_summary(response)
        self.assertTupleEqual(
            plan_summary.activity_string,
            (self.translator.gettext("Status"), self.translator.gettext("Inactive")),
        )

    def test_planner_is_displayed_correctly_as_tuple_of_strings(self):
        expected_planner_id = uuid4()
        response = replace(
            PLAN_SUMMARY,
            planner_id=expected_planner_id,
        )
        plan_summary = self.service.get_plan_summary(response)
        self.assertTupleEqual(
            plan_summary.planner,
            (
                self.translator.gettext("Planning company"),
                str(expected_planner_id),
                self.company_url_index.get_company_summary_url(expected_planner_id),
                PLAN_SUMMARY.planner_name,
            ),
        )

    def test_product_name_is_displayed_correctly_as_tuple_of_strings(self):
        plan_summary = self.service.get_plan_summary(PLAN_SUMMARY)
        self.assertTupleEqual(
            plan_summary.product_name,
            (
                self.translator.gettext("Name of product"),
                PLAN_SUMMARY.product_name,
            ),
        )

    def test_description_is_displayed_correctly_as_tuple_of_string_and_list_of_string(
        self,
    ):
        plan_summary = self.service.get_plan_summary(PLAN_SUMMARY)
        self.assertTupleEqual(
            plan_summary.description,
            (
                self.translator.gettext("Description of product"),
                [PLAN_SUMMARY.description],
            ),
        )

    def test_description_is_splitted_correctly_at_carriage_return_in_list_of_strings(
        self,
    ):
        response = replace(
            PLAN_SUMMARY,
            description="first paragraph\rsecond paragraph",
        )
        plan_summary = self.service.get_plan_summary(response)
        self.assertTupleEqual(
            plan_summary.description,
            (
                self.translator.gettext("Description of product"),
                ["first paragraph", "second paragraph"],
            ),
        )

    def test_timeframe_is_displayed_correctly_as_tuple_of_strings(self):
        plan_summary = self.service.get_plan_summary(PLAN_SUMMARY)
        self.assertTupleEqual(
            plan_summary.timeframe,
            (
                self.translator.gettext("Planning timeframe (days)"),
                str(PLAN_SUMMARY.timeframe),
            ),
        )

    def test_production_unit_is_displayed_correctly_as_tuple_of_strings(self):
        plan_summary = self.service.get_plan_summary(PLAN_SUMMARY)
        self.assertTupleEqual(
            plan_summary.production_unit,
            (
                self.translator.gettext("Smallest delivery unit"),
                PLAN_SUMMARY.production_unit,
            ),
        )

    def test_amount_is_displayed_correctly_as_tuple_of_strings(self):
        plan_summary = self.service.get_plan_summary(PLAN_SUMMARY)
        self.assertTupleEqual(
            plan_summary.amount,
            (self.translator.gettext("Amount"), str(PLAN_SUMMARY.amount)),
        )

    def test_means_cost_is_displayed_correctly_as_tuple_of_strings(self):
        plan_summary = self.service.get_plan_summary(PLAN_SUMMARY)
        self.assertTupleEqual(
            plan_summary.means_cost,
            (
                self.translator.gettext("Costs for fixed means of production"),
                str(PLAN_SUMMARY.means_cost),
            ),
        )

    def test_resources_cost_is_displayed_correctly_as_tuple_of_strings(self):
        plan_summary = self.service.get_plan_summary(PLAN_SUMMARY)
        self.assertTupleEqual(
            plan_summary.resources_cost,
            (
                self.translator.gettext("Costs for liquid means of production"),
                str(PLAN_SUMMARY.resources_cost),
            ),
        )

    def test_labour_cost_is_displayed_correctly_as_tuple_of_strings(self):
        plan_summary = self.service.get_plan_summary(PLAN_SUMMARY)
        self.assertTupleEqual(
            plan_summary.labour_cost,
            (
                self.translator.gettext("Costs for work"),
                str(PLAN_SUMMARY.labour_cost),
            ),
        )

    def test_type_of_plan_is_displayed_correctly_as_tuple_of_strings_when_productive_plan(
        self,
    ):
        response = replace(
            PLAN_SUMMARY,
            is_public_service=False,
        )
        plan_summary = self.service.get_plan_summary(response)
        self.assertTupleEqual(
            plan_summary.type_of_plan,
            (
                self.translator.gettext("Type"),
                self.translator.gettext("Productive"),
            ),
        )

    def test_type_of_plan_is_displayed_correctly_as_tuple_of_strings_when_public_plan(
        self,
    ):
        response = replace(
            PLAN_SUMMARY,
            is_public_service=True,
        )
        plan_summary = self.service.get_plan_summary(response)
        self.assertTupleEqual(
            plan_summary.type_of_plan,
            (
                self.translator.gettext("Type"),
                self.translator.gettext("Public"),
            ),
        )

    def test_price_per_unit_is_displayed_correctly_as_tuple_of_strings_and_bool(self):
        plan_summary = self.service.get_plan_summary(PLAN_SUMMARY)
        coop_id = PLAN_SUMMARY.cooperation
        assert coop_id
        self.assertTupleEqual(
            plan_summary.price_per_unit,
            (
                self.translator.gettext("Price (per unit)"),
                "0.06",
                True,
                self.coop_url_index.get_coop_summary_url(coop_id),
            ),
        )

    def test_availability_is_displayed_correctly_as_tuple_of_strings(self):
        plan_summary = self.service.get_plan_summary(PLAN_SUMMARY)
        self.assertTupleEqual(
            plan_summary.availability_string,
            (
                self.translator.gettext("Product currently available"),
                self.translator.gettext("Yes"),
            ),
        )

    def test_active_days_is_displayed_correctly_as_string(self):
        plan_summary = self.service.get_plan_summary(PLAN_SUMMARY)
        self.assertEqual(
            plan_summary.active_days,
            str(PLAN_SUMMARY.active_days),
        )
