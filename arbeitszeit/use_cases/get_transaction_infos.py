from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Tuple, Union

from injector import inject

from arbeitszeit.entities import (
    AccountTypes,
    Company,
    Member,
    SocialAccounting,
    Transaction,
)
from arbeitszeit.repositories import AccountOwnerRepository
from arbeitszeit.transactions import UserAccountingService

User = Union[Member, Company]
UserOrSocialAccounting = Union[User, SocialAccounting]


@dataclass
class TransactionInfo:
    date: datetime
    sender_name: str
    receiver_name: str
    transaction_volumes: Dict[str, Decimal]
    purpose: str


@inject
@dataclass
class GetTransactionInfos:
    accounting_service: UserAccountingService
    acount_owner_repository: AccountOwnerRepository

    def __call__(self, user: Company) -> List[TransactionInfo]:
        return [
            self._create_info(user, transaction)
            for transaction in self.accounting_service.get_all_transactions_sorted(user)
        ]

    def _create_info(
        self,
        user: Company,
        transaction: Transaction,
    ) -> TransactionInfo:
        sender, user_is_sender = self._get_sender(transaction, user)
        receiver, user_is_receiver = self._get_receiver(transaction, user)
        sender_name = self._get_sender_name(sender, user_is_sender)
        receiver_name = self._get_receiver_name(receiver, user_is_receiver)

        transaction_volumes = self._get_volumes_for_company_transaction(
            transaction,
            user,
            user_is_sender,
            user_is_receiver,
        )

        return TransactionInfo(
            transaction.date,
            sender_name,
            receiver_name,
            transaction_volumes,
            transaction.purpose,
        )

    def _get_sender(
        self, transaction: Transaction, user: User
    ) -> Tuple[UserOrSocialAccounting, bool]:
        sender: UserOrSocialAccounting
        if transaction.sending_account in user.accounts():
            sender = user
            user_is_sender = True
        else:
            sender = self.acount_owner_repository.get_account_owner(
                transaction.sending_account
            )
            user_is_sender = False
        return sender, user_is_sender

    def _get_receiver(
        self, transaction: Transaction, user: User
    ) -> Tuple[UserOrSocialAccounting, bool]:
        receiver: UserOrSocialAccounting
        if transaction.receiving_account in user.accounts():
            receiver = user
            user_is_receiver = True
        else:
            receiver = self.acount_owner_repository.get_account_owner(
                transaction.receiving_account
            )
            user_is_receiver = False
        return receiver, user_is_receiver

    def _get_sender_name(
        self, sender: UserOrSocialAccounting, user_is_sender: bool
    ) -> str:
        if user_is_sender:
            sender_name = "Mir"
        elif isinstance(sender, (Company, Member)):
            sender_name = sender.name
        elif isinstance(sender, SocialAccounting):
            sender_name = "Öff. Buchhaltung"

        return sender_name

    def _get_receiver_name(
        self, receiver: UserOrSocialAccounting, user_is_receiver: bool
    ) -> str:
        if user_is_receiver:
            receiver_name = "Mich"
        elif isinstance(receiver, (Company, Member)):
            receiver_name = receiver.name
        else:
            receiver_name = "Öff. Buchführung"
        return receiver_name

    def _get_volumes_for_company_transaction(
        self,
        transaction: Transaction,
        user: Company,
        user_is_sender: bool,
        user_is_receiver: bool,
    ) -> Dict:
        if user_is_sender and user_is_receiver:  # company buys from itself
            transaction_volumes = self._get_volumes_for_company_transaction_if_company_is_sender_and_receiver(
                transaction,
                user,
            )

        elif user_is_sender:
            transaction_volumes = (
                self._get_volumes_for_company_transaction_if_company_is_sender(
                    transaction,
                    user,
                )
            )

        elif user_is_receiver:
            transaction_volumes = (
                self._get_volumes_for_company_transaction_if_company_is_receiver(
                    transaction,
                    user,
                )
            )

        return transaction_volumes

    def _get_volumes_for_company_transaction_if_company_is_sender_and_receiver(
        self, transaction: Transaction, user: Company
    ) -> Dict[str, Decimal]:
        transaction_volumes: Dict[str, Decimal] = {}
        transaction_volumes[AccountTypes.p.value] = (
            -1 * transaction.amount_sent
            if transaction.sending_account == user.means_account
            else Decimal(0)
        )
        transaction_volumes[AccountTypes.r.value] = (
            -1 * transaction.amount_sent
            if transaction.sending_account == user.raw_material_account
            else Decimal(0)
        )
        transaction_volumes[AccountTypes.a.value] = (
            -1 * transaction.amount_sent
            if transaction.sending_account == user.work_account
            else Decimal(0)
        )
        transaction_volumes[AccountTypes.prd.value] = (
            1 * transaction.amount_received
            if transaction.receiving_account == user.product_account
            else Decimal(0)
        )
        return transaction_volumes

    def _get_volumes_for_company_transaction_if_company_is_sender(
        self,
        transaction: Transaction,
        user: Company,
    ) -> Dict[str, Decimal]:
        transaction_volumes: Dict[str, Decimal] = {}
        factor = -1
        transaction_volumes[AccountTypes.p.value] = (
            factor * transaction.amount_sent
            if transaction.sending_account == user.means_account
            else Decimal(0)
        )
        transaction_volumes[AccountTypes.r.value] = (
            factor * transaction.amount_sent
            if transaction.sending_account == user.raw_material_account
            else Decimal(0)
        )
        transaction_volumes[AccountTypes.a.value] = (
            factor * transaction.amount_sent
            if transaction.sending_account == user.work_account
            else Decimal(0)
        )
        transaction_volumes[AccountTypes.prd.value] = (
            factor * transaction.amount_sent
            if transaction.sending_account == user.product_account
            else Decimal(0)
        )
        return transaction_volumes

    def _get_volumes_for_company_transaction_if_company_is_receiver(
        self,
        transaction: Transaction,
        user: Company,
    ) -> Dict[str, Decimal]:
        transaction_volumes: Dict[str, Decimal] = {}
        transaction_volumes[AccountTypes.p.value] = (
            transaction.amount_received
            if transaction.receiving_account == user.means_account
            else Decimal(0)
        )
        transaction_volumes[AccountTypes.r.value] = (
            transaction.amount_received
            if transaction.receiving_account == user.raw_material_account
            else Decimal(0)
        )
        transaction_volumes[AccountTypes.a.value] = (
            transaction.amount_received
            if transaction.receiving_account == user.work_account
            else Decimal(0)
        )
        transaction_volumes[AccountTypes.prd.value] = (
            transaction.amount_received
            if transaction.receiving_account == user.product_account
            else Decimal(0)
        )
        return transaction_volumes
