from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Iterator, List, Union
from uuid import UUID

from arbeitszeit.entities import (
    Account,
    AccountTypes,
    Company,
    Member,
    Plan,
    ProductionCosts,
    ProductOffer,
    Purchase,
    SocialAccounting,
    Transaction,
)


class CompanyWorkerRepository(ABC):
    @abstractmethod
    def add_worker_to_company(self, company: Company, worker: Member) -> None:
        pass

    @abstractmethod
    def get_company_workers(self, company: Company) -> List[Member]:
        pass


class PurchaseRepository(ABC):
    @abstractmethod
    def add(self, purchase: Purchase) -> None:
        pass

    @abstractmethod
    def get_purchases_descending_by_date(
        self, user: Union[Member, Company]
    ) -> Iterator[Purchase]:
        pass


class PlanRepository(ABC):
    @abstractmethod
    def create_plan(
        self,
        planner: Company,
        costs: ProductionCosts,
        product_name: str,
        production_unit: str,
        amount: int,
        description: str,
        timeframe_in_days: int,
        is_public_service: bool,
        creation_timestamp: datetime,
    ) -> Plan:
        pass

    @abstractmethod
    def get_plan_by_id(self, id: UUID) -> Plan:
        pass


class TransactionRepository(ABC):
    @abstractmethod
    def create_transaction(
        self,
        date: datetime,
        account_from: Account,
        account_to: Account,
        amount: Decimal,
        purpose: str,
    ) -> Transaction:
        pass

    @abstractmethod
    def add(self, transaction: Transaction) -> None:
        pass

    @abstractmethod
    def all_transactions_sent_by_account(self, account: Account) -> List[Transaction]:
        pass

    @abstractmethod
    def all_transactions_received_by_account(
        self, account: Account
    ) -> List[Transaction]:
        pass


class AccountRepository(ABC):
    @abstractmethod
    def add(self, account: Account) -> None:
        pass

    @abstractmethod
    def create_account(self, account_type: AccountTypes) -> Account:
        pass


class OfferRepository(ABC):
    @abstractmethod
    def query_offers_by_name(self, query: str) -> Iterator[ProductOffer]:
        pass

    @abstractmethod
    def query_offers_by_description(self, query: str) -> Iterator[ProductOffer]:
        pass

    @abstractmethod
    def all_active_offers(self) -> Iterator[ProductOffer]:
        pass

    @abstractmethod
    def create_offer(
        self,
        plan: Plan,
        creation_datetime: datetime,
        name: str,
        description: str,
        amount_available: int,
    ) -> ProductOffer:
        pass


class MemberRepository(ABC):
    @abstractmethod
    def create_member(
        self, email: str, name: str, password: str, account: Account
    ) -> Member:
        pass

    @abstractmethod
    def has_member_with_email(self, email: str) -> bool:
        pass


class AccountOwnerRepository(ABC):
    @abstractmethod
    def get_account_owner(
        self, account: Account
    ) -> Union[Member, Company, SocialAccounting]:
        pass


class CompanyRepository(ABC):
    @abstractmethod
    def create_company(
        self,
        email: str,
        name: str,
        password: str,
        means_account: Account,
        labour_account: Account,
        resource_account: Account,
        products_account: Account,
    ) -> Company:
        pass

    @abstractmethod
    def has_company_with_email(self, email: str) -> bool:
        pass
