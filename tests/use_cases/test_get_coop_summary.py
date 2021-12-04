from datetime import datetime
from typing import Callable
from uuid import uuid4

from arbeitszeit.use_cases import (
    GetCoopSummary,
    GetCoopSummaryRequest,
    GetCoopSummaryResponse,
    GetCoopSummarySuccess,
)
from tests.data_generators import CompanyGenerator, CooperationGenerator, PlanGenerator

from .dependency_injection import injection_test
from .repositories import PlanCooperationRepository


@injection_test
def test_that_none_is_returned_when_cooperation_does_not_exist(
    get_coop_summary: GetCoopSummary,
    company_generator: CompanyGenerator,
):
    requester = company_generator.create_company()
    summary = get_coop_summary(GetCoopSummaryRequest(requester.id, uuid4()))
    assert summary is None


@injection_test
def test_that_requester_is_correctly_defined_as_equal_to_coordinator(
    get_coop_summary: GetCoopSummary,
    company_generator: CompanyGenerator,
    cooperation_generator: CooperationGenerator,
):
    requester = company_generator.create_company()
    coop = cooperation_generator.create_cooperation(coordinator=requester)
    summary = get_coop_summary(GetCoopSummaryRequest(requester.id, coop.id))
    assert_success(summary, lambda s: s.requester_is_coordinator == True)


@injection_test
def test_that_requester_is_correctly_defined_as_different_from_coordinator(
    get_coop_summary: GetCoopSummary,
    company_generator: CompanyGenerator,
    cooperation_generator: CooperationGenerator,
):
    requester = company_generator.create_company()
    coop = cooperation_generator.create_cooperation()
    summary = get_coop_summary(GetCoopSummaryRequest(requester.id, coop.id))
    assert_success(summary, lambda s: s.requester_is_coordinator == False)


@injection_test
def test_that_correct_amount_of_associated_plans_are_shown(
    get_coop_summary: GetCoopSummary,
    company_generator: CompanyGenerator,
    cooperation_generator: CooperationGenerator,
    plan_generator: PlanGenerator,
):
    requester = company_generator.create_company()
    plan1 = plan_generator.create_plan(activation_date=datetime.min)
    plan2 = plan_generator.create_plan(activation_date=datetime.min)
    coop = cooperation_generator.create_cooperation(plans=[plan1, plan2])
    summary = get_coop_summary(GetCoopSummaryRequest(requester.id, coop.id))
    assert_success(summary, lambda s: len(s.plans) == 2)


@injection_test
def test_that_correct_info_of_associated_plan_is_shown(
    get_coop_summary: GetCoopSummary,
    company_generator: CompanyGenerator,
    cooperation_generator: CooperationGenerator,
    plan_generator: PlanGenerator,
    plan_cooperation_repository: PlanCooperationRepository,
):
    requester = company_generator.create_company()
    plan = plan_generator.create_plan(activation_date=datetime.min)
    coop = cooperation_generator.create_cooperation(plans=[plan])
    summary = get_coop_summary(GetCoopSummaryRequest(requester.id, coop.id))
    assert_success(summary, lambda s: len(s.plans) == 1)
    assert summary is not None
    assert summary.plans[0].plan_id == plan.id
    assert summary.plans[0].plan_name == plan.prd_name
    assert summary.plans[0].plan_total_costs == plan.production_costs.total_cost()
    assert summary.plans[0].plan_amount == plan.prd_amount
    assert summary.plans[0].plan_individual_price == plan.individual_price_per_unit
    assert summary.plans[
        0
    ].plan_coop_price == plan_cooperation_repository.get_price_per_unit(plan.id)


def assert_success(
    response: GetCoopSummaryResponse, assertion: Callable[[GetCoopSummarySuccess], bool]
) -> None:
    assert isinstance(response, GetCoopSummarySuccess)
    assert assertion(response)
