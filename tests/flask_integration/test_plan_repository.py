from datetime import datetime
from decimal import Decimal
from typing import Union
from uuid import uuid4

from arbeitszeit.entities import ProductionCosts
from project.database.repositories import PlanRepository

from ..data_generators import CompanyGenerator, PlanGenerator
from .dependency_injection import injection_test

Number = Union[int, Decimal]


def production_costs(a: Number, r: Number, p: Number) -> ProductionCosts:
    return ProductionCosts(
        Decimal(a),
        Decimal(r),
        Decimal(p),
    )


@injection_test
def test_active_plans_are_counted_correctly(
    plan_repository: PlanRepository,
    plan_generator: PlanGenerator,
):
    assert plan_repository.count_active_plans() == 0
    plan_generator.create_plan(activation_date=datetime.min)
    plan_generator.create_plan(activation_date=datetime.min)
    assert plan_repository.count_active_plans() == 2


@injection_test
def test_active_public_plans_are_counted_correctly(
    plan_repository: PlanRepository,
    plan_generator: PlanGenerator,
):
    assert plan_repository.count_active_public_plans() == 0
    plan_generator.create_plan(activation_date=datetime.min, is_public_service=True)
    plan_generator.create_plan(activation_date=datetime.min, is_public_service=True)
    plan_generator.create_plan(activation_date=datetime.min, is_public_service=False)
    assert plan_repository.count_active_public_plans() == 2


@injection_test
def test_avg_timeframe_of_active_plans_is_calculated_correctly(
    plan_repository: PlanRepository,
    plan_generator: PlanGenerator,
):
    assert plan_repository.avg_timeframe_of_active_plans() == 0
    plan_generator.create_plan(activation_date=datetime.min, timeframe=5)
    plan_generator.create_plan(activation_date=datetime.min, timeframe=3)
    plan_generator.create_plan(activation_date=None, timeframe=20)
    assert plan_repository.avg_timeframe_of_active_plans() == 4


@injection_test
def test_sum_of_active_planned_work_calculated_correctly(
    plan_repository: PlanRepository,
    plan_generator: PlanGenerator,
):
    assert plan_repository.sum_of_active_planned_work() == 0
    plan_generator.create_plan(
        activation_date=datetime.min,
        costs=production_costs(2, 0, 0),
    )
    plan_generator.create_plan(
        activation_date=datetime.min,
        costs=production_costs(3, 0, 0),
    )
    assert plan_repository.sum_of_active_planned_work() == 5


@injection_test
def test_sum_of_active_planned_resources_calculated_correctly(
    plan_repository: PlanRepository,
    plan_generator: PlanGenerator,
):
    assert plan_repository.sum_of_active_planned_resources() == 0
    plan_generator.create_plan(
        activation_date=datetime.min,
        costs=production_costs(0, 2, 0),
    )
    plan_generator.create_plan(
        activation_date=datetime.min,
        costs=production_costs(0, 3, 0),
    )
    assert plan_repository.sum_of_active_planned_resources() == 5


@injection_test
def test_sum_of_active_planned_means_calculated_correctly(
    plan_repository: PlanRepository,
    plan_generator: PlanGenerator,
):
    assert plan_repository.sum_of_active_planned_means() == 0
    plan_generator.create_plan(
        activation_date=datetime.min,
        costs=production_costs(0, 0, 2),
    )
    plan_generator.create_plan(
        activation_date=datetime.min,
        costs=production_costs(0, 0, 3),
    )
    assert plan_repository.sum_of_active_planned_means() == 5


@injection_test
def test_plans_that_were_set_to_expired_dont_show_up_in_active_plans(
    repository: PlanRepository,
    generator: PlanGenerator,
) -> None:
    plan = generator.create_plan()
    repository.activate_plan(plan, datetime.now())
    assert plan in list(repository.all_active_plans())
    repository.set_plan_as_expired(plan)
    assert plan not in list(repository.all_active_plans())


@injection_test
def test_get_plan_by_id_with_unkown_id_results_in_none(
    repository: PlanRepository,
) -> None:
    assert repository.get_plan_by_id(uuid4()) is None


@injection_test
def test_that_existing_plan_can_be_retrieved_by_id(
    repository: PlanRepository,
    generator: PlanGenerator,
) -> None:
    expected_plan = generator.create_plan()
    assert expected_plan == repository.get_plan_by_id(expected_plan.id)


@injection_test
def test_that_all_plans_for_a_company_are_returned(
    repository: PlanRepository,
    plan_generator: PlanGenerator,
    company_generator: CompanyGenerator,
) -> None:
    company = company_generator.create_company()
    plan_generator.create_plan(planner=company, activation_date=None)
    plan_generator.create_plan(planner=company, is_public_service=True)
    plan_generator.create_plan(planner=company, is_available=False)
    returned_plans = list(repository.get_all_plans_for_company(company_id=company.id))
    assert len(returned_plans) == 3


@injection_test
def test_that_all_active_plan_for_a_company_are_returned(
    repository: PlanRepository,
    plan_generator: PlanGenerator,
    company_generator: CompanyGenerator,
) -> None:
    company = company_generator.create_company()
    plan_generator.create_plan(planner=company, activation_date=datetime.min)
    plan_generator.create_plan(planner=company, activation_date=datetime.min)
    plan_generator.create_plan(planner=company)
    returned_plans = list(
        repository.get_all_active_plans_for_company(company_id=company.id)
    )
    assert len(returned_plans) == 2


@injection_test
def test_that_plan_gets_hidden(
    repository: PlanRepository,
    plan_generator: PlanGenerator,
) -> None:
    plan = plan_generator.create_plan()
    repository.hide_plan(plan.id)
    plan_from_repo = repository.get_plan_by_id(plan.id)
    assert plan_from_repo
    assert plan_from_repo.hidden_by_user


@injection_test
def test_that_query_active_plans_by_exact_product_name_returns_plan(
    repository: PlanRepository,
    plan_generator: PlanGenerator,
) -> None:
    expected_plan = plan_generator.create_plan(
        activation_date=datetime.min, product_name="Delivery of goods"
    )
    returned_plan = list(
        repository.query_active_plans_by_product_name("Delivery of goods")
    )
    assert returned_plan
    assert returned_plan[0] == expected_plan


@injection_test
def test_that_query_active_plans_by_substring_of_product_name_returns_plan(
    repository: PlanRepository,
    plan_generator: PlanGenerator,
) -> None:
    expected_plan = plan_generator.create_plan(
        activation_date=datetime.min, product_name="Delivery of goods"
    )
    returned_plan = list(repository.query_active_plans_by_product_name("very of go"))
    assert returned_plan
    assert returned_plan[0] == expected_plan


@injection_test
def test_that_query_active_plans_by_substring_of_plan_id_returns_plan(
    repository: PlanRepository,
    plan_generator: PlanGenerator,
) -> None:
    expected_plan = plan_generator.create_plan(activation_date=datetime.min)
    expected_plan_id = expected_plan.id
    query = str(expected_plan_id)[3:8]
    returned_plan = list(repository.query_active_plans_by_plan_id(query))
    assert returned_plan
    assert returned_plan[0] == expected_plan


@injection_test
def test_that_active_days_are_set(
    repository: PlanRepository,
    plan_generator: PlanGenerator,
) -> None:
    plan = plan_generator.create_plan(activation_date=datetime.min)
    assert plan.active_days is None
    repository.set_active_days(plan, 3)
    plan_from_repo = repository.get_plan_by_id(plan.id)
    assert plan_from_repo
    assert plan_from_repo.active_days == 3


@injection_test
def test_that_payout_count_is_increased_by_one(
    repository: PlanRepository,
    plan_generator: PlanGenerator,
) -> None:
    plan = plan_generator.create_plan(activation_date=datetime.min)
    assert plan.payout_count == 0
    repository.increase_payout_count_by_one(plan)
    plan_from_repo = repository.get_plan_by_id(plan.id)
    assert plan_from_repo
    assert plan_from_repo.payout_count == 1


@injection_test
def test_that_availability_is_toggled_to_false(
    repository: PlanRepository,
    plan_generator: PlanGenerator,
) -> None:
    plan = plan_generator.create_plan()
    assert plan.is_available == True
    repository.toggle_product_availability(plan)
    plan_from_repo = repository.get_plan_by_id(plan.id)
    assert plan_from_repo
    assert plan_from_repo.is_available == False


@injection_test
def test_that_availability_is_toggled_to_true(
    repository: PlanRepository,
    plan_generator: PlanGenerator,
) -> None:
    plan = plan_generator.create_plan(is_available=False)
    assert plan.is_available == False
    repository.toggle_product_availability(plan)
    plan_from_repo = repository.get_plan_by_id(plan.id)
    assert plan_from_repo
    assert plan_from_repo.is_available == True
