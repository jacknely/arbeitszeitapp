from uuid import uuid4

from arbeitszeit.use_cases import ListCoordinations, ListCoordinationsRequest
from tests.data_generators import CompanyGenerator, CooperationGenerator, PlanGenerator

from .dependency_injection import injection_test


@injection_test
def test_empty_list_is_returned_if_requesting_company_does_not_exist(
    use_case: ListCoordinations,
):
    response = use_case(ListCoordinationsRequest(company=uuid4()))
    assert len(response.coordinations) == 0


@injection_test
def test_empty_list_is_returned_when_plans_are_not_cooperating(
    use_case: ListCoordinations,
    plan_generator: PlanGenerator,
    company_generator: CompanyGenerator,
):
    plan_generator.create_plan()
    plan_generator.create_plan()
    company = company_generator.create_company()
    response = use_case(ListCoordinationsRequest(company.id))
    assert len(response.coordinations) == 0


@injection_test
def test_empty_list_is_returned_when_requester_is_not_coordinator_of_cooperation(
    use_case: ListCoordinations,
    plan_generator: PlanGenerator,
    company_generator: CompanyGenerator,
    cooperation_generator: CooperationGenerator,
):
    p1 = plan_generator.create_plan()
    p2 = plan_generator.create_plan()
    cooperation_generator.create_cooperation(plans=[p1, p2])
    company = company_generator.create_company()
    response = use_case(ListCoordinationsRequest(company.id))
    assert len(response.coordinations) == 0


@injection_test
def test_cooperation_is_listed_when_requester_is_coordinator_of_cooperation(
    use_case: ListCoordinations,
    plan_generator: PlanGenerator,
    company_generator: CompanyGenerator,
    cooperation_generator: CooperationGenerator,
):
    p1 = plan_generator.create_plan()
    p2 = plan_generator.create_plan()
    company = company_generator.create_company()
    cooperation = cooperation_generator.create_cooperation(
        plans=[p1, p2], coordinator=company
    )
    response = use_case(ListCoordinationsRequest(company.id))
    assert len(response.coordinations) == 1
    assert response.coordinations[0] == cooperation


@injection_test
def test_only_cooperations_are_listed_where_requester_is_coordinator(
    use_case: ListCoordinations,
    plan_generator: PlanGenerator,
    company_generator: CompanyGenerator,
    cooperation_generator: CooperationGenerator,
):
    p1 = plan_generator.create_plan()
    p2 = plan_generator.create_plan()
    company = company_generator.create_company()
    expected_cooperation = cooperation_generator.create_cooperation(
        plans=[p1, p2], coordinator=company
    )
    cooperation_generator.create_cooperation(
        plans=[p1, p2], coordinator=company_generator.create_company()
    )
    response = use_case(ListCoordinationsRequest(company.id))
    assert len(response.coordinations) == 1
    assert response.coordinations[0] == expected_cooperation
