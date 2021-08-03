"""The classes in this module should only provide instances of
entities. Never should these entities automatically be added to a
repository.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Union
from uuid import uuid4

from injector import inject

from arbeitszeit.datetime_service import DatetimeService
from arbeitszeit.entities import (
    Account,
    AccountTypes,
    Company,
    Member,
    Plan,
    ProductOffer,
    Purchase,
    PurposesOfPurchases,
    SocialAccounting,
)
from tests.datetime_service import TestDatetimeService


@inject
@dataclass
class OfferGenerator:
    id_generator: IdGenerator
    company_generator: CompanyGenerator

    def create_offer(
        self, *, name="Product name", amount=1, provider=None, description=""
    ):
        return ProductOffer(
            id=self.id_generator.get_id(),
            name=name,
            amount_available=amount,
            deactivate_offer_in_db=lambda: None,
            decrease_amount_available=lambda _: None,
            price_per_unit=Decimal(1),
            provider=self.company_generator.create_company()
            if provider is None
            else provider,
            active=True,
            description=description,
        )


@inject
@dataclass
class MemberGenerator:
    id_generator: IdGenerator
    account_generator: AccountGenerator
    email_generator: EmailGenerator

    def create_member(self, *, email: Optional[str] = None) -> Member:
        if not email:
            email = self.email_generator.get_random_email()
        assert email is not None
        return Member(
            id=self.id_generator.get_id(),
            name="Member name",
            email=email,
            account=self.account_generator.create_account(
                account_type=AccountTypes.member
            ),
        )


@inject
@dataclass
class CompanyGenerator:
    id_generator: IdGenerator
    account_generator: AccountGenerator

    def create_company(self) -> Company:
        return Company(
            id=self.id_generator.get_id(),
            name="Company name",
            means_account=self.account_generator.create_account(
                account_type=AccountTypes.p
            ),
            raw_material_account=self.account_generator.create_account(
                account_type=AccountTypes.r
            ),
            work_account=self.account_generator.create_account(
                account_type=AccountTypes.a
            ),
            product_account=self.account_generator.create_account(
                account_type=AccountTypes.prd
            ),
            workers=[],
        )


class IdGenerator:
    def __init__(self):
        self.current = 0

    def get_id(self) -> int:
        self.current += 1
        return self.current


@inject
@dataclass
class SocialAccountingGenerator:
    account_generator: AccountGenerator

    def create_social_accounting(self) -> SocialAccounting:
        return SocialAccounting(
            account=self.account_generator.create_account(
                account_type=AccountTypes.accounting
            ),
        )


@inject
@dataclass
class AccountGenerator:
    id_generator: IdGenerator

    def create_account(self, account_type=AccountTypes.p) -> Account:
        return Account(
            id=self.id_generator.get_id(),
            account_type=account_type,
            balance=Decimal(0),
            change_credit=lambda amount: None,
        )


class EmailGenerator:
    def get_random_email(self):
        return str(uuid4()) + "@cp.org"


@inject
@dataclass
class PlanGenerator:
    id_generator: IdGenerator
    company_generator: CompanyGenerator
    datetime_service: DatetimeService

    def create_plan(
        self, plan_creation_date=None, planner=None, timeframe=None, approved=False
    ) -> Plan:
        return Plan(
            id=self.id_generator.get_id(),
            plan_creation_date=self.datetime_service.now()
            if plan_creation_date is None
            else plan_creation_date,
            planner=self.company_generator.create_company()
            if planner is None
            else planner,
            costs_p=Decimal(10),
            costs_r=Decimal(20),
            costs_a=Decimal(30),
            prd_name="Produkt A",
            prd_unit="500 Gramm",
            prd_amount=100,
            description="Beschreibung für Produkt A.",
            timeframe=int(14) if timeframe is None else int(timeframe),
            approved=approved,
            approval_date=None,
            approval_reason=None,
            approve=lambda _1, _2, _3: None,
            expired=False,
            renewed=False,
            set_as_expired=lambda: None,
            set_as_renewed=lambda: None,
        )


@inject
@dataclass
class PurchaseGenerator:
    offer_generator: OfferGenerator
    member_generator: MemberGenerator
    company_generator: CompanyGenerator

    def create_purchase(
        self,
        buyer: Union[Member, Company],
        purchase_date=TestDatetimeService().now_minus_one_day(),
        amount=1,
    ) -> Purchase:
        return Purchase(
            purchase_date=purchase_date,
            product_offer=self.offer_generator.create_offer(),
            buyer=buyer,
            price=Decimal(10),
            amount=amount,
            purpose=PurposesOfPurchases.consumption,
        )
