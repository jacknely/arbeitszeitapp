import datetime
from decimal import Decimal

from arbeitszeit.entities import AccountTypes, ProductionCosts
from arbeitszeit.use_cases import UpdatePlansAndPayout
from tests.data_generators import CooperationGenerator, PlanGenerator
from tests.datetime_service import FakeDatetimeService

from .dependency_injection import injection_test
from .repositories import AccountRepository, TransactionRepository


def count_transactions_of_type_a(transaction_repository: TransactionRepository) -> int:
    wages_transactions = 0
    for trans in transaction_repository.transactions:
        if trans.receiving_account.account_type == AccountTypes.a:
            wages_transactions += 1
    return wages_transactions


@injection_test
def test_that_a_plan_that_is_not_active_can_not_expire(
    plan_generator: PlanGenerator,
    payout: UpdatePlansAndPayout,
):
    plan = plan_generator.create_plan(activation_date=None)
    payout()
    assert not plan.expired


@injection_test
def test_that_expiration_time_is_set_if_plan_is_active(
    plan_generator: PlanGenerator,
    datetime_service: FakeDatetimeService,
    payout: UpdatePlansAndPayout,
):
    plan = plan_generator.create_plan(
        timeframe=2, activation_date=datetime_service.now()
    )
    assert not plan.expiration_date
    assert not plan.expiration_relative
    payout()
    assert plan.expiration_relative
    assert plan.expiration_date


@injection_test
def test_that_active_days_is_set_if_plan_is_active(
    plan_generator: PlanGenerator,
    datetime_service: FakeDatetimeService,
    payout: UpdatePlansAndPayout,
):
    plan = plan_generator.create_plan(
        timeframe=2, activation_date=datetime_service.now()
    )
    assert not plan.active_days
    payout()
    assert plan.active_days is not None


@injection_test
def test_that_active_days_is_not_set_if_plan_is_not_active(
    plan_generator: PlanGenerator,
    payout: UpdatePlansAndPayout,
):
    plan = plan_generator.create_plan(timeframe=2, activation_date=None)
    assert not plan.active_days
    payout()
    assert plan.active_days is None


@injection_test
def test_that_active_days_is_set_correctly(
    plan_generator: PlanGenerator,
    datetime_service: FakeDatetimeService,
    payout: UpdatePlansAndPayout,
):
    datetime_service.freeze_time(datetime.datetime(2021, 10, 2, 2))
    plan = plan_generator.create_plan(
        timeframe=5, activation_date=datetime_service.now()
    )
    datetime_service.freeze_time(datetime.datetime(2021, 10, 4, 3))
    payout()
    assert plan.active_days == 2


@injection_test
def test_that_active_days_is_set_correctly_if_current_time_exceeds_timeframe(
    plan_generator: PlanGenerator,
    datetime_service: FakeDatetimeService,
    payout: UpdatePlansAndPayout,
):
    datetime_service.freeze_time(datetime.datetime(2021, 10, 2, 2))
    plan = plan_generator.create_plan(
        timeframe=5, activation_date=datetime_service.now()
    )
    datetime_service.freeze_time(datetime.datetime(2021, 10, 10, 3))
    payout()
    assert plan.active_days == 5


@injection_test
def test_that_plan_is_set_expired_and_deactivated_if_expired(
    plan_generator: PlanGenerator,
    datetime_service: FakeDatetimeService,
    payout: UpdatePlansAndPayout,
):
    plan = plan_generator.create_plan(
        timeframe=5, activation_date=datetime_service.now_minus_ten_days()
    )
    payout()
    assert plan.expired
    assert not plan.is_active


@injection_test
def test_that_plan_is_not_set_expired_and_not_deactivated_if_not_yet_expired(
    plan_generator: PlanGenerator,
    datetime_service: FakeDatetimeService,
    payout: UpdatePlansAndPayout,
):
    plan = plan_generator.create_plan(
        timeframe=5, activation_date=datetime_service.now_minus_one_day()
    )
    payout()
    assert not plan.expired
    assert plan.is_active


@injection_test
def test_that_expiration_date_is_correctly_calculated_if_plan_expires_now(
    plan_generator: PlanGenerator,
    datetime_service: FakeDatetimeService,
    payout: UpdatePlansAndPayout,
):
    datetime_service.freeze_time(datetime.datetime.now())
    plan = plan_generator.create_plan(
        timeframe=1, activation_date=datetime_service.now_minus_one_day()
    )
    payout()
    expected_expiration_time = datetime_service.now()
    assert plan.expiration_date == expected_expiration_time


@injection_test
def test_that_expiration_date_is_correctly_calculated_if_plan_expires_in_the_future(
    plan_generator: PlanGenerator,
    datetime_service: FakeDatetimeService,
    payout: UpdatePlansAndPayout,
):
    datetime_service.freeze_time(datetime.datetime.now())
    plan = plan_generator.create_plan(
        timeframe=2, activation_date=datetime_service.now_minus_one_day()
    )
    payout()
    expected_expiration_time = datetime_service.now_plus_one_day()
    assert plan.expiration_date == expected_expiration_time


@injection_test
def test_that_expiration_relative_is_correctly_calculated_when_plan_expires_in_less_than_one_day(
    plan_generator: PlanGenerator,
    datetime_service: FakeDatetimeService,
    payout: UpdatePlansAndPayout,
):
    datetime_service.freeze_time(datetime.datetime(2021, 10, 2, 2))
    plan = plan_generator.create_plan(
        timeframe=1, activation_date=datetime_service.now()
    )
    datetime_service.freeze_time(datetime.datetime(2021, 10, 2, 5))
    payout()
    assert plan.expiration_relative == 0


@injection_test
def test_that_expiration_relative_is_correctly_calculated_when_plan_expires_in_exactly_one_day(
    plan_generator: PlanGenerator,
    datetime_service: FakeDatetimeService,
    payout: UpdatePlansAndPayout,
):
    datetime_service.freeze_time(datetime.datetime.now())
    plan = plan_generator.create_plan(
        timeframe=2, activation_date=datetime_service.now_minus_one_day()
    )
    payout()
    assert plan.expiration_relative == 1


@injection_test
def test_that_plan_with_requested_cooperation_has_no_requested_cooperation_after_expiration(
    plan_generator: PlanGenerator,
    datetime_service: FakeDatetimeService,
    payout: UpdatePlansAndPayout,
    cooperation_generator: CooperationGenerator,
):
    requested_coop = cooperation_generator.create_cooperation()
    plan = plan_generator.create_plan(
        timeframe=5,
        activation_date=datetime_service.now_minus_ten_days(),
        requested_cooperation=requested_coop,
    )
    assert plan.requested_cooperation
    payout()
    assert plan.expired
    assert not plan.is_active
    assert not plan.requested_cooperation


@injection_test
def test_that_cooperating_plan_is_not_cooperating_after_expiration(
    plan_generator: PlanGenerator,
    datetime_service: FakeDatetimeService,
    payout: UpdatePlansAndPayout,
    cooperation_generator: CooperationGenerator,
):
    cooperation = cooperation_generator.create_cooperation()
    plan = plan_generator.create_plan(
        timeframe=5,
        activation_date=datetime_service.now_minus_ten_days(),
        cooperation=cooperation,
    )
    assert plan.cooperation
    payout()
    assert plan.expired
    assert not plan.is_active
    assert not plan.cooperation


@injection_test
def test_that_wages_are_paid_out(
    payout: UpdatePlansAndPayout,
    plan_generator: PlanGenerator,
    datetime_service: FakeDatetimeService,
    transaction_repository: TransactionRepository,
):
    plan_generator.create_plan(
        approved=True, activation_date=datetime_service.now_minus_one_day()
    )
    payout()
    assert count_transactions_of_type_a(transaction_repository)


@injection_test
def test_that_past_3_due_wages_get_paid_out_when_plan_expires(
    plan_generator: PlanGenerator,
    payout: UpdatePlansAndPayout,
    datetime_service: FakeDatetimeService,
    transaction_repository: TransactionRepository,
):
    plan_generator.create_plan(
        activation_date=datetime_service.now_minus_ten_days(),
        timeframe=3,
    )
    payout()
    assert count_transactions_of_type_a(transaction_repository) == 3


@injection_test
def test_that_one_past_due_wage_does_get_paid_out_only_once(
    plan_generator: PlanGenerator,
    payout: UpdatePlansAndPayout,
    datetime_service: FakeDatetimeService,
    transaction_repository: TransactionRepository,
):
    plan_generator.create_plan(
        activation_date=datetime_service.now_minus_ten_days(),
        timeframe=1,
    )
    payout()
    payout()
    assert count_transactions_of_type_a(transaction_repository) == 1


@injection_test
def test_account_balances_correctly_adjusted_for_work_account(
    plan_generator: PlanGenerator,
    payout: UpdatePlansAndPayout,
    account_repository: AccountRepository,
    datetime_service: FakeDatetimeService,
):
    datetime_service.freeze_time(datetime.datetime(2021, 10, 2, 10))
    plan = plan_generator.create_plan(
        approved=True,
        is_public_service=False,
        activation_date=datetime_service.now(),
        timeframe=5,
    )
    datetime_service.freeze_time(datetime.datetime(2021, 10, 3, 9))
    expected_payout_factor = 1
    expected_payout = expected_payout_factor * plan.production_costs.labour_cost / 5
    payout()

    assert (
        account_repository.get_account_balance(plan.planner.work_account)
        == expected_payout
    )


@injection_test
def test_sum_of_payouts_is_equals_to_costs_for_labour(
    plan_generator: PlanGenerator,
    payout: UpdatePlansAndPayout,
    account_repository: AccountRepository,
    datetime_service: FakeDatetimeService,
):
    datetime_service.freeze_time(datetime.datetime(2021, 10, 2, 10))
    plan = plan_generator.create_plan(
        approved=True,
        is_public_service=False,
        activation_date=datetime_service.now(),
        timeframe=5,
    )
    datetime_service.freeze_time(datetime.datetime(2021, 10, 12, 11))
    payout()

    assert (
        account_repository.get_account_balance(plan.planner.work_account)
        == plan.production_costs.labour_cost
    )


@injection_test
def test_account_balances_correctly_adjusted_for_work_accounts_with_two_active_plans(
    plan_generator: PlanGenerator,
    payout: UpdatePlansAndPayout,
    datetime_service: FakeDatetimeService,
    account_repository: AccountRepository,
):
    datetime_service.freeze_time(datetime.datetime(2021, 10, 2, 10))
    plan1 = plan_generator.create_plan(
        approved=True,
        is_public_service=False,
        timeframe=5,
        activation_date=datetime_service.now(),
        costs=ProductionCosts(Decimal(1), Decimal(1), Decimal(1)),
    )

    plan2 = plan_generator.create_plan(
        approved=True,
        is_public_service=False,
        timeframe=2,
        activation_date=datetime_service.now(),
        costs=ProductionCosts(Decimal(3), Decimal(3), Decimal(3)),
    )

    datetime_service.freeze_time(datetime.datetime(2021, 10, 3, 9))
    expected_payout_factor = 1
    expected_payout1 = expected_payout_factor * plan1.production_costs.labour_cost / 5
    expected_payout2 = expected_payout_factor * plan2.production_costs.labour_cost / 2
    payout()

    assert (
        account_repository.get_account_balance(plan1.planner.work_account)
        == expected_payout1
    )
    assert (
        account_repository.get_account_balance(plan2.planner.work_account)
        == expected_payout2
    )


@injection_test
def test_account_balances_correctly_adjusted_for_work_accounts_with_public_and_productive_plans_of_different_timeframes(
    plan_generator: PlanGenerator,
    payout: UpdatePlansAndPayout,
    account_repository: AccountRepository,
    datetime_service: FakeDatetimeService,
):
    datetime_service.freeze_time(datetime.datetime(2021, 10, 2, 10))
    plan1 = plan_generator.create_plan(
        activation_date=datetime_service.now(),
        is_public_service=False,
        timeframe=2,
        costs=ProductionCosts(Decimal(1), Decimal(1), Decimal(1)),
    )

    plan2 = plan_generator.create_plan(
        activation_date=datetime_service.now(),
        is_public_service=True,
        timeframe=5,
        costs=ProductionCosts(Decimal(3), Decimal(3), Decimal(3)),
    )
    datetime_service.freeze_time(datetime.datetime(2021, 10, 3, 9))
    # (A − ( P o + R o )) / (A + A o) =
    # (1/2 - (3/5 + 3/5)) / (1/2 + 3/5) =
    # -0.7 / 1.1 = -0.636363636
    expected_payout_factor = Decimal(-0.636363636)
    expected_payout1 = round(
        (expected_payout_factor * plan1.production_costs.labour_cost / plan1.timeframe),
        2,
    )
    expected_payout2 = round(
        (expected_payout_factor * plan2.production_costs.labour_cost / plan2.timeframe),
        2,
    )
    payout()

    assert (
        account_repository.get_account_balance(plan1.planner.work_account)
        == expected_payout1
    )
    assert (
        account_repository.get_account_balance(plan2.planner.work_account)
        == expected_payout2
    )


@injection_test
def test_account_balances_correctly_adjusted_with_public_plan_not_yet_activated(
    plan_generator: PlanGenerator,
    payout: UpdatePlansAndPayout,
    account_repository: AccountRepository,
    datetime_service: FakeDatetimeService,
):
    datetime_service.freeze_time(datetime.datetime(2021, 10, 2, 10))
    plan1 = plan_generator.create_plan(
        activation_date=datetime_service.now(),
        is_public_service=False,
        timeframe=2,
        costs=ProductionCosts(Decimal(1), Decimal(1), Decimal(1)),
    )

    plan2 = plan_generator.create_plan(
        approved=True,
        activation_date=None,
        is_public_service=True,
        timeframe=5,
        costs=ProductionCosts(Decimal(3), Decimal(3), Decimal(3)),
    )

    datetime_service.freeze_time(datetime.datetime(2021, 10, 3, 9))
    expected_payout_factor = Decimal(1)
    expected_payout1 = round(
        (expected_payout_factor * plan1.production_costs.labour_cost / plan1.timeframe),
        2,
    )
    expected_payout2 = 0
    payout()

    assert (
        account_repository.get_account_balance(plan1.planner.work_account)
        == expected_payout1
    )
    assert (
        account_repository.get_account_balance(plan2.planner.work_account)
        == expected_payout2
    )


@injection_test
def test_that_wages_are_paid_out_twice_after_25_hours_when_plan_has_timeframe_of_3(
    payout: UpdatePlansAndPayout,
    plan_generator: PlanGenerator,
    transaction_repository: TransactionRepository,
    datetime_service: FakeDatetimeService,
):
    datetime_service.freeze_time(datetime.datetime(2021, 1, 1, 10))
    plan_generator.create_plan(activation_date=datetime_service.now(), timeframe=3)
    datetime_service.freeze_time(datetime.datetime(2021, 1, 2, 11))
    payout()

    wages_transactions = count_transactions_of_type_a(transaction_repository)
    assert wages_transactions == 2


@injection_test
def test_that_wages_are_paid_out_twice_after_two_days(
    payout: UpdatePlansAndPayout,
    plan_generator: PlanGenerator,
    transaction_repository: TransactionRepository,
    datetime_service: FakeDatetimeService,
):
    datetime_service.freeze_time(datetime.datetime(2021, 1, 1, 1))
    plan_generator.create_plan(activation_date=datetime_service.now(), timeframe=3)
    payout()
    datetime_service.freeze_time(datetime.datetime(2021, 1, 2, 1))
    payout()
    wages_transactions = count_transactions_of_type_a(transaction_repository)
    assert wages_transactions == 2


@injection_test
def test_that_a_company_receives_wage_if_activation_is_before_midnight_and_no_payout_until_next_morning_and_timeframe_of_1(
    payout: UpdatePlansAndPayout,
    plan_generator: PlanGenerator,
    datetime_service: FakeDatetimeService,
    transaction_repository: TransactionRepository,
):
    datetime_service.freeze_time(datetime.datetime(2021, 1, 1, 23, 45))
    plan_generator.create_plan(activation_date=datetime_service.now(), timeframe=1)
    datetime_service.freeze_time(datetime.datetime(2021, 1, 2, 0, 1))
    payout()
    wages_transactions = count_transactions_of_type_a(transaction_repository)
    assert wages_transactions == 1
