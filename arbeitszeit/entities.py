from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Callable, Dict, List, Optional, Union
from uuid import UUID


@dataclass
class SocialAccounting:
    account: Account


class Member:
    def __init__(
        self,
        id: UUID,
        name: str,
        email: str,
        account: Account,
    ) -> None:
        self._id = id
        self.name = name
        self.account = account
        self.email = email

    @property
    def id(self):
        return self._id

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Member):
            return self.id == other.id

        return False

    def accounts(self) -> List[Account]:
        return [self.account]


class Company:
    def __init__(
        self,
        id: UUID,
        email: str,
        name: str,
        means_account: Account,
        raw_material_account: Account,
        work_account: Account,
        product_account: Account,
        workers: List[Member],
    ) -> None:
        self._id = id
        self.email = email
        self.name = name
        self.means_account = means_account
        self.raw_material_account = raw_material_account
        self.work_account = work_account
        self.product_account = product_account
        self.workers = workers

    @property
    def id(self) -> UUID:
        return self._id

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Company):
            return self.id == other.id

        return False

    def accounts(self) -> List[Account]:
        return [
            self.means_account,
            self.raw_material_account,
            self.work_account,
            self.product_account,
        ]


class AccountTypes(Enum):
    p = "p"
    r = "r"
    a = "a"
    prd = "prd"
    member = "member"
    accounting = "accounting"


class Account:
    def __init__(
        self,
        id: UUID,
        account_type: AccountTypes,
        balance: Decimal,
        change_credit: Callable[[Decimal], None],
    ) -> None:
        self.id = id
        self.account_type = account_type
        self.balance = balance
        self._change_credit = change_credit

    def change_credit(self, amount: Decimal) -> None:
        self.balance += amount
        self._change_credit(amount)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Account):
            return (self.id == other.id) and (self.account_type == other.account_type)

        return False


@dataclass
class ProductionCosts:
    labour_cost: Decimal
    resource_cost: Decimal
    means_cost: Decimal

    def total_cost(self) -> Decimal:
        return self.labour_cost + self.resource_cost + self.means_cost


class Plan:
    def __init__(
        self,
        id: UUID,
        plan_creation_date: datetime,
        planner: Company,
        production_costs: ProductionCosts,
        prd_name: str,
        prd_unit: str,
        prd_amount: int,
        description: str,
        timeframe: int,
        is_public_service: bool,
        approved: bool,
        approval_date: Optional[datetime],
        approval_reason: Optional[str],
        approve: Callable[[bool, str, datetime], None],
        is_active: bool,
        expired: bool,
        renewed: bool,
        activation_date: datetime,
        expiration_relative: Optional[int],
        expiration_date: Optional[datetime],
        last_certificate_payout: Optional[datetime],
    ) -> None:
        self.id = id
        self.plan_creation_date = plan_creation_date
        self.planner = planner
        self.production_costs = production_costs
        self.prd_name = prd_name
        self.prd_unit = prd_unit
        self.prd_amount = prd_amount
        self.description = description
        self.timeframe = timeframe
        self.is_public_service = is_public_service
        self.approved = approved
        self.approval_date = approval_date
        self.approval_reason = approval_reason
        self._approve_call = approve
        self.is_active = is_active
        self.expired = expired
        self.renewed = renewed
        self.expiration_relative = expiration_relative
        self.expiration_date = expiration_date
        self.activation_date = activation_date
        self.last_certificate_payout = last_certificate_payout

    def approve(self, approval_date: datetime) -> None:
        self.approved = True
        self.approval_date = approval_date
        self.approval_reason = "approved"
        self._approve_call(True, "approved", approval_date)

    def deny(self, denial_date: datetime) -> None:
        self.approved = False
        self.approval_date = denial_date
        self.approval_reason = "not approved"
        self._approve_call(False, "not approved", denial_date)

    def price_per_unit(self) -> Decimal:
        cost_per_unit = self.production_costs.total_cost() / self.prd_amount
        return cost_per_unit if not self.is_public_service else Decimal(0)

    def expected_sales_value(self) -> Decimal:
        """
        For productive plans, sales value should equal total cost.
        Public services are not expected to sell,
        they give away their product for free.
        """
        return (
            self.production_costs.total_cost()
            if not self.is_public_service
            else Decimal(0)
        )


class ProductOffer:
    def __init__(
        self,
        id: UUID,
        name: str,
        amount_available: int,
        deactivate_offer_in_db: Callable[[], None],
        decrease_amount_available: Callable[[int], None],
        active: bool,
        description: str,
        plan: Plan,
    ) -> None:
        self._id = id
        self.name = name
        self._amount_available = amount_available
        self._deactivate = deactivate_offer_in_db
        self._decrease_amount = decrease_amount_available
        self.active = active
        self.description = description
        self.plan = plan

    def deactivate(self) -> None:
        self.active = False
        self._deactivate()

    def decrease_amount_available(self, amount: int) -> None:
        self._amount_available -= amount
        self._decrease_amount(amount)

    def price_per_unit(self) -> Decimal:
        return self.plan.price_per_unit()

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def amount_available(self) -> int:
        return self._amount_available


class PurposesOfPurchases(Enum):
    means_of_prod = "means_of_prod"
    raw_materials = "raw_materials"
    consumption = "consumption"


@dataclass
class Purchase:
    purchase_date: datetime
    product_offer: ProductOffer
    buyer: Union[Member, Company]
    price: Decimal
    amount: int
    purpose: PurposesOfPurchases


@dataclass
class TransactionInfo:
    date: datetime
    sender_name: str
    receiver_name: str
    transaction_volumes: Dict[AccountTypes.value, Decimal]
    purpose: str


@dataclass
class Transaction:
    id: UUID
    date: datetime
    account_from: Account
    account_to: Account
    amount: Decimal
    purpose: str

    def adjust_balances(self) -> None:
        """this method adjusts the balances of the two accounts
        that are involved in this transaction."""
        self.account_from.change_credit(-self.amount)
        self.account_to.change_credit(self.amount)
