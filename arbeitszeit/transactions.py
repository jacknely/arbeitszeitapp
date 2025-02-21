from dataclasses import dataclass
from decimal import Decimal
from enum import Enum, auto
from typing import List, Union

from injector import inject

from .entities import AccountTypes, Company, Member, Transaction
from .repositories import TransactionRepository


class TransactionTypes(Enum):
    """
    'Subjective' transaction types, i.e. seen from a concrete user perspective.
    """

    credit_for_wages = auto()
    payment_of_wages = auto()
    incoming_wages = auto()
    credit_for_fixed_means = auto()
    payment_of_fixed_means = auto()
    credit_for_liquid_means = auto()
    payment_of_liquid_means = auto()
    expected_sales = auto()
    sale_of_consumer_product = auto()
    payment_of_consumer_product = auto()
    sale_of_fixed_means = auto()
    sale_of_liquid_means = auto()


@inject
@dataclass
class UserAccountingService:
    transaction_repository: TransactionRepository

    def get_all_transactions_sorted(
        self, user: Union[Member, Company]
    ) -> List[Transaction]:
        all_transactions = set()
        for account in user.accounts():
            all_transactions.update(
                self.transaction_repository.all_transactions_sent_by_account(account)
            )
            all_transactions.update(
                self.transaction_repository.all_transactions_received_by_account(
                    account
                )
            )
        all_transactions_sorted = sorted(
            all_transactions, key=lambda x: x.date, reverse=True
        )
        return all_transactions_sorted

    def get_account_transactions_sorted(
        self, user: Union[Member, Company], queried_account_type: AccountTypes
    ) -> List[Transaction]:
        for acc in user.accounts():
            if acc.account_type == queried_account_type:
                queried_account = acc
        transactions = set()
        transactions.update(
            self.transaction_repository.all_transactions_sent_by_account(
                queried_account
            )
        )
        transactions.update(
            self.transaction_repository.all_transactions_received_by_account(
                queried_account
            )
        )
        transactions_sorted = sorted(transactions, key=lambda x: x.date, reverse=True)
        return transactions_sorted

    def user_is_sender(
        self, transaction: Transaction, user: Union[Member, Company]
    ) -> bool:
        return transaction.sending_account in user.accounts()

    def get_transaction_type(
        self, transaction: Transaction, user_is_sender: bool
    ) -> TransactionTypes:
        """
        Based on wether the user is sender or receiver,
        this method returns the 'subjective' transaction type.
        """
        sending_account = transaction.sending_account.account_type
        receiving_account = transaction.receiving_account.account_type

        if user_is_sender:
            if sending_account == AccountTypes.a:
                transaction_type = TransactionTypes.payment_of_wages
            elif sending_account == AccountTypes.p:
                transaction_type = TransactionTypes.payment_of_fixed_means
            elif sending_account == AccountTypes.r:
                transaction_type = TransactionTypes.payment_of_liquid_means
            elif sending_account == AccountTypes.member:
                transaction_type = TransactionTypes.payment_of_consumer_product

        else:
            if sending_account == AccountTypes.accounting:
                if receiving_account == AccountTypes.a:
                    transaction_type = TransactionTypes.credit_for_wages
                elif receiving_account == AccountTypes.p:
                    transaction_type = TransactionTypes.credit_for_fixed_means
                elif receiving_account == AccountTypes.r:
                    transaction_type = TransactionTypes.credit_for_liquid_means
                elif receiving_account == AccountTypes.prd:
                    transaction_type = TransactionTypes.expected_sales
                elif receiving_account == AccountTypes.member:
                    transaction_type = TransactionTypes.incoming_wages

            elif sending_account == AccountTypes.p:
                transaction_type = TransactionTypes.sale_of_fixed_means
            elif sending_account == AccountTypes.r:
                transaction_type = TransactionTypes.sale_of_liquid_means
            elif sending_account == AccountTypes.member:
                transaction_type = TransactionTypes.sale_of_consumer_product

        assert transaction_type
        return transaction_type

    def get_transaction_volume(
        self,
        transaction: Transaction,
        user_is_sender: bool,
    ) -> Decimal:
        """
        Based on wether the user is sender or receiver,
        this method returns the 'subjective' transaction volume.
        """
        if user_is_sender:
            return -1 * transaction.amount_sent
        return transaction.amount_received
