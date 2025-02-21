import datetime
from decimal import Decimal
from unittest import TestCase

from arbeitszeit.entities import AccountTypes, Company, ProductionCosts
from arbeitszeit.use_cases import UpdatePlansAndPayout
from arbeitszeit.use_cases.show_my_accounts import ShowMyAccounts, ShowMyAccountsRequest
from tests.data_generators import CompanyGenerator, CooperationGenerator, PlanGenerator
from tests.datetime_service import FakeDatetimeService

from .dependency_injection import get_dependency_injector
from .repositories import AccountRepository, TransactionRepository


class UseCaseTests(TestCase):
    def setUp(self) -> None:
        self.injector = get_dependency_injector()
        self.plan_generator = self.injector.get(PlanGenerator)
        self.payout = self.injector.get(UpdatePlansAndPayout)
        self.datetime_service = self.injector.get(FakeDatetimeService)
        self.cooperation_generator = self.injector.get(CooperationGenerator)
        self.account_repository = self.injector.get(AccountRepository)
        self.transaction_repository = self.injector.get(TransactionRepository)
        self.show_my_accounts = self.injector.get(ShowMyAccounts)
        self.company_generator = self.injector.get(CompanyGenerator)

    def test_that_a_plan_that_is_not_active_can_not_expire(self) -> None:
        plan = self.plan_generator.create_plan(activation_date=None)
        self.payout()
        self.assertFalse(plan.expired)

    def test_that_expiration_time_is_set_if_plan_is_active(self) -> None:
        plan = self.plan_generator.create_plan(
            timeframe=2, activation_date=self.datetime_service.now()
        )
        self.assertIsNone(plan.expiration_date)
        self.assertIsNone(plan.expiration_relative)
        self.payout()
        self.assertIsNotNone(plan.expiration_relative)
        self.assertIsNotNone(plan.expiration_date)

    def test_that_active_days_is_set_if_plan_is_active(self) -> None:
        plan = self.plan_generator.create_plan(
            timeframe=2, activation_date=self.datetime_service.now()
        )
        self.assertIsNone(plan.active_days)
        self.payout()
        self.assertIsNotNone(plan.active_days)

    def test_that_active_days_is_not_set_if_plan_is_not_active(self) -> None:
        plan = self.plan_generator.create_plan(timeframe=2, activation_date=None)
        assert not plan.active_days
        self.payout()
        assert plan.active_days is None

    def test_that_active_days_is_set_correctly(self) -> None:
        self.datetime_service.freeze_time(datetime.datetime(2021, 10, 2, 2))
        plan = self.plan_generator.create_plan(
            timeframe=5, activation_date=self.datetime_service.now()
        )
        self.datetime_service.freeze_time(datetime.datetime(2021, 10, 4, 3))
        self.payout()
        assert plan.active_days == 2

    def test_that_active_days_is_set_correctly_if_current_time_exceeds_timeframe(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime.datetime(2021, 10, 2, 2))
        plan = self.plan_generator.create_plan(
            timeframe=5, activation_date=self.datetime_service.now()
        )
        self.datetime_service.freeze_time(datetime.datetime(2021, 10, 10, 3))
        self.payout()
        assert plan.active_days == 5

    def test_that_plan_is_set_expired_and_deactivated_if_expired(self) -> None:
        plan = self.plan_generator.create_plan(
            timeframe=5, activation_date=self.datetime_service.now_minus_ten_days()
        )
        self.payout()
        assert plan.expired
        assert not plan.is_active

    def test_that_plan_is_not_set_expired_and_not_deactivated_if_not_yet_expired(
        self,
    ) -> None:
        plan = self.plan_generator.create_plan(
            timeframe=5, activation_date=self.datetime_service.now_minus_one_day()
        )
        self.payout()
        assert not plan.expired
        assert plan.is_active

    def test_that_expiration_date_is_correctly_calculated_if_plan_expires_now(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime.datetime.now())
        plan = self.plan_generator.create_plan(
            timeframe=1, activation_date=self.datetime_service.now_minus_one_day()
        )
        self.payout()
        expected_expiration_time = self.datetime_service.now()
        assert plan.expiration_date == expected_expiration_time

    def test_that_expiration_date_is_correctly_calculated_if_plan_expires_in_the_future(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime.datetime.now())
        plan = self.plan_generator.create_plan(
            timeframe=2, activation_date=self.datetime_service.now_minus_one_day()
        )
        self.payout()
        expected_expiration_time = self.datetime_service.now_plus_one_day()
        assert plan.expiration_date == expected_expiration_time

    def test_that_expiration_relative_is_correctly_calculated_when_plan_expires_in_less_than_one_day(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime.datetime(2021, 10, 2, 2))
        plan = self.plan_generator.create_plan(
            timeframe=1, activation_date=self.datetime_service.now()
        )
        self.datetime_service.freeze_time(datetime.datetime(2021, 10, 2, 5))
        self.payout()
        assert plan.expiration_relative == 0

    def test_that_expiration_relative_is_correctly_calculated_when_plan_expires_in_exactly_one_day(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime.datetime.now())
        plan = self.plan_generator.create_plan(
            timeframe=2, activation_date=self.datetime_service.now_minus_one_day()
        )
        self.payout()
        assert plan.expiration_relative == 1

    def test_that_plan_with_requested_cooperation_has_no_requested_cooperation_after_expiration(
        self,
    ) -> None:
        requested_coop = self.cooperation_generator.create_cooperation()
        plan = self.plan_generator.create_plan(
            timeframe=5,
            activation_date=self.datetime_service.now_minus_ten_days(),
            requested_cooperation=requested_coop,
        )
        assert plan.requested_cooperation
        self.payout()
        assert plan.expired
        assert not plan.is_active
        assert not plan.requested_cooperation

    def test_that_cooperating_plan_is_not_cooperating_after_expiration(self) -> None:
        cooperation = self.cooperation_generator.create_cooperation()
        plan = self.plan_generator.create_plan(
            timeframe=5,
            activation_date=self.datetime_service.now_minus_ten_days(),
            cooperation=cooperation,
        )
        assert plan.cooperation
        self.payout()
        assert plan.expired
        assert not plan.is_active
        assert not plan.cooperation

    def test_that_wages_are_paid_out(self) -> None:
        self.plan_generator.create_plan(
            approved=True, activation_date=self.datetime_service.now_minus_one_day()
        )
        self.payout()
        self.assertTrue(self.count_transactions_of_type_a())

    def test_that_past_3_due_wages_get_paid_out_when_plan_expires(self) -> None:
        self.plan_generator.create_plan(
            activation_date=self.datetime_service.now_minus_ten_days(),
            timeframe=3,
        )
        self.payout()
        assert self.count_transactions_of_type_a() == 3

    def test_that_one_past_due_wage_does_get_paid_out_only_once(self) -> None:
        self.plan_generator.create_plan(
            activation_date=self.datetime_service.now_minus_ten_days(),
            timeframe=1,
        )
        self.payout()
        self.payout()
        assert self.count_transactions_of_type_a() == 1

    def test_account_balances_correctly_adjusted_for_work_account(self) -> None:
        self.datetime_service.freeze_time(datetime.datetime(2021, 10, 2, 10))
        plan = self.plan_generator.create_plan(
            approved=True,
            is_public_service=False,
            activation_date=self.datetime_service.now(),
            timeframe=5,
        )
        self.datetime_service.freeze_time(datetime.datetime(2021, 10, 3, 9))
        expected_payout_factor = 1
        expected_payout = expected_payout_factor * plan.production_costs.labour_cost / 5
        self.payout()

        assert (
            self.account_repository.get_account_balance(plan.planner.work_account)
            == expected_payout
        )

    def test_sum_of_payouts_is_equals_to_costs_for_labour(self) -> None:
        self.datetime_service.freeze_time(datetime.datetime(2021, 10, 2, 10))
        plan = self.plan_generator.create_plan(
            approved=True,
            is_public_service=False,
            activation_date=self.datetime_service.now(),
            timeframe=5,
        )
        self.datetime_service.freeze_time(datetime.datetime(2021, 10, 12, 11))
        self.payout()

        assert (
            self.account_repository.get_account_balance(plan.planner.work_account)
            == plan.production_costs.labour_cost
        )

    def test_account_balances_correctly_adjusted_for_work_accounts_with_two_active_plans(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime.datetime(2021, 10, 2, 10))
        plan1 = self.plan_generator.create_plan(
            approved=True,
            is_public_service=False,
            timeframe=5,
            activation_date=self.datetime_service.now(),
            costs=ProductionCosts(Decimal(1), Decimal(1), Decimal(1)),
        )

        plan2 = self.plan_generator.create_plan(
            approved=True,
            is_public_service=False,
            timeframe=2,
            activation_date=self.datetime_service.now(),
            costs=ProductionCosts(Decimal(3), Decimal(3), Decimal(3)),
        )

        self.datetime_service.freeze_time(datetime.datetime(2021, 10, 3, 9))
        expected_payout_factor = 1
        expected_payout1 = (
            expected_payout_factor * plan1.production_costs.labour_cost / 5
        )
        expected_payout2 = (
            expected_payout_factor * plan2.production_costs.labour_cost / 2
        )
        self.payout()

        assert (
            self.account_repository.get_account_balance(plan1.planner.work_account)
            == expected_payout1
        )
        assert (
            self.account_repository.get_account_balance(plan2.planner.work_account)
            == expected_payout2
        )

    def test_account_balances_correctly_adjusted_for_work_accounts_with_public_and_productive_plans_of_different_timeframes(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime.datetime(2021, 10, 2, 10))
        plan1 = self.plan_generator.create_plan(
            activation_date=self.datetime_service.now(),
            is_public_service=False,
            timeframe=2,
            costs=ProductionCosts(Decimal(1), Decimal(1), Decimal(1)),
        )

        plan2 = self.plan_generator.create_plan(
            activation_date=self.datetime_service.now(),
            is_public_service=True,
            timeframe=5,
            costs=ProductionCosts(Decimal(3), Decimal(3), Decimal(3)),
        )
        self.datetime_service.freeze_time(datetime.datetime(2021, 10, 3, 9))
        # (A − ( P o + R o )) / (A + A o) =
        # (1/2 - (3/5 + 3/5)) / (1/2 + 3/5) =
        # -0.7 / 1.1 = -0.636363636
        expected_payout_factor = Decimal(-0.636363636)
        expected_payout1 = round(
            (
                expected_payout_factor
                * plan1.production_costs.labour_cost
                / plan1.timeframe
            ),
            2,
        )
        expected_payout2 = round(
            (
                expected_payout_factor
                * plan2.production_costs.labour_cost
                / plan2.timeframe
            ),
            2,
        )
        self.payout()

        assert (
            self.account_repository.get_account_balance(plan1.planner.work_account)
            == expected_payout1
        )
        assert (
            self.account_repository.get_account_balance(plan2.planner.work_account)
            == expected_payout2
        )

    def test_account_balances_correctly_adjusted_with_public_plan_not_yet_activated(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime.datetime(2021, 10, 2, 10))
        plan1 = self.plan_generator.create_plan(
            activation_date=self.datetime_service.now(),
            is_public_service=False,
            timeframe=2,
            costs=ProductionCosts(Decimal(1), Decimal(1), Decimal(1)),
        )

        plan2 = self.plan_generator.create_plan(
            approved=True,
            activation_date=None,
            is_public_service=True,
            timeframe=5,
            costs=ProductionCosts(Decimal(3), Decimal(3), Decimal(3)),
        )

        self.datetime_service.freeze_time(datetime.datetime(2021, 10, 3, 9))
        expected_payout_factor = Decimal(1)
        expected_payout1 = round(
            (
                expected_payout_factor
                * plan1.production_costs.labour_cost
                / plan1.timeframe
            ),
            2,
        )
        expected_payout2 = 0
        self.payout()

        assert (
            self.account_repository.get_account_balance(plan1.planner.work_account)
            == expected_payout1
        )
        assert (
            self.account_repository.get_account_balance(plan2.planner.work_account)
            == expected_payout2
        )

    def test_that_wages_are_paid_out_twice_after_25_hours_when_plan_has_timeframe_of_3(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime.datetime(2021, 1, 1, 10))
        self.plan_generator.create_plan(
            activation_date=self.datetime_service.now(), timeframe=3
        )
        self.datetime_service.freeze_time(datetime.datetime(2021, 1, 2, 11))
        self.payout()

        self.assertEqual(self.count_transactions_of_type_a(), 2)

    def test_that_wages_are_paid_out_twice_after_two_days(self) -> None:
        self.datetime_service.freeze_time(datetime.datetime(2021, 1, 1, 1))
        self.plan_generator.create_plan(
            activation_date=self.datetime_service.now(), timeframe=3
        )
        self.payout()
        self.datetime_service.freeze_time(datetime.datetime(2021, 1, 2, 1))
        self.payout()
        self.assertEqual(self.count_transactions_of_type_a(), 2)

    def test_that_a_company_receives_wage_if_activation_is_before_midnight_and_no_payout_until_next_morning_and_timeframe_of_1(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime.datetime(2021, 1, 1, 23, 45))
        self.plan_generator.create_plan(
            activation_date=self.datetime_service.now(), timeframe=1
        )
        self.datetime_service.freeze_time(datetime.datetime(2021, 1, 2, 0, 1))
        self.payout()
        self.assertEqual(self.count_transactions_of_type_a(), 1)

    def test_that_company_receives_correct_wage_credit(self) -> None:
        planner = self.company_generator.create_company()
        expected_wage_payout = Decimal("3")
        self.datetime_service.freeze_time(datetime.datetime(2021, 1, 1, 23, 45))
        self.plan_generator.create_plan(
            planner=planner,
            activation_date=self.datetime_service.now(),
            timeframe=1,
            costs=ProductionCosts(
                labour_cost=expected_wage_payout,
                resource_cost=Decimal("0"),
                means_cost=Decimal("0"),
            ),
        )
        self.datetime_service.freeze_time(datetime.datetime(2021, 1, 2, 0, 1))
        self.payout()
        self.assertEqual(
            self.get_company_work_account_balance(planner), expected_wage_payout
        )

    def get_company_work_account_balance(self, company: Company) -> Decimal:
        show_my_accounts_response = self.show_my_accounts(
            ShowMyAccountsRequest(company.id)
        )
        return show_my_accounts_response.balances[2]

    def count_transactions_of_type_a(self) -> int:
        return len(
            [
                transaction
                for transaction in self.transaction_repository.transactions
                if transaction.receiving_account.account_type == AccountTypes.a
            ]
        )
