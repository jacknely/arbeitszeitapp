from decimal import Decimal

from arbeitszeit.entities import ProductionCosts
from arbeitszeit.use_cases import GetPlanSummary
from tests.data_generators import PlanGenerator

from .dependency_injection import injection_test


@injection_test
def test_that_correct_production_costs_are_shown(
    plan_generator: PlanGenerator,
    get_plan_summary: GetPlanSummary,
):
    plan = plan_generator.create_plan(
        costs=ProductionCosts(
            means_cost=Decimal(1),
            labour_cost=Decimal(2),
            resource_cost=Decimal(3),
        )
    )
    summary = get_plan_summary(plan.id)
    assert summary.means_cost == Decimal(1)
    assert summary.labour_cost == Decimal(2)
    assert summary.resources_cost == Decimal(3)


@injection_test
def test_that_correct_product_name_is_shown(
    plan_generator: PlanGenerator,
    get_plan_summary: GetPlanSummary,
):
    plan = plan_generator.create_plan(product_name="test product")
    summary = get_plan_summary(plan.id)
    assert summary.product_name == "test product"


@injection_test
def test_that_correct_product_description_is_shown(
    plan_generator: PlanGenerator,
    get_plan_summary: GetPlanSummary,
):
    plan = plan_generator.create_plan(description="test description")
    summary = get_plan_summary(plan.id)
    assert summary.description == "test description"


@injection_test
def test_that_correct_product_unit_is_shown(
    plan_generator: PlanGenerator,
    get_plan_summary: GetPlanSummary,
):
    plan = plan_generator.create_plan(production_unit="test unit")
    summary = get_plan_summary(plan.id)
    assert summary.production_unit == "test unit"


@injection_test
def test_that_correct_amount_is_shown(
    plan_generator: PlanGenerator,
    get_plan_summary: GetPlanSummary,
):
    plan = plan_generator.create_plan(amount=123)
    summary = get_plan_summary(plan.id)
    assert summary.amount == 123
