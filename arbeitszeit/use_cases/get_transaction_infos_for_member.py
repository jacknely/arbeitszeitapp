from dataclasses import dataclass
from itertools import chain
from typing import Dict, List, Union

from injector import inject

from arbeitszeit.entities import AccountTypes, Company, Member
from arbeitszeit.repositories import (
    AccountOwnerRepository,
    MemberRepository,
    TransactionRepository,
)


@inject
@dataclass
class GetTransactionInfosForMember:
    transaction_repository: TransactionRepository
    member_repository: MemberRepository
    acount_owner_repository: AccountOwnerRepository

    def __call__(self, member: Member) -> List[Dict]:
        """
        This function returns informations about all the transactions a Member object is involved in.

        The following information about every transaction is stored in a Dictionary:
        - user role: str ("sender" or "receiver")
        - transaction: Transaction
        - sender: Union[Member, Company]
        - receiver: Union[Member, Company]

        Returns:
        List of Dictionaries
        """

        all_transactions = list(
            chain(
                self.transaction_repository.all_transactions_sent_by_account(
                    member.account
                ),
                self.transaction_repository.all_transactions_received_by_account(
                    member.account
                ),
            )
        )

        all_transactions_sorted = sorted(
            all_transactions, key=lambda x: x.date, reverse=True
        )

        list_of_trans_infos = []

        for transaction in all_transactions_sorted:
            trans_info: Dict = {}
            sender: Union[Member, Company]

            sending_account = transaction.account_from
            # currently members can only receive money from companies (accounttype "a")
            if sending_account.account_type.name in [
                AccountTypes.p.name,
                AccountTypes.r.name,
                AccountTypes.a.name,
                AccountTypes.prd.name,
            ]:
                sender = self.acount_owner_repository.get_company_for_account(
                    sending_account
                )
            elif sending_account == member.account:
                sender = member

            receiving_account = transaction.account_to
            # currently members can send money only to companies (accounttype "prd")
            if receiving_account.account_type.name == AccountTypes.prd.name:
                receiver: Union[
                    Member, Company
                ] = self.acount_owner_repository.get_company_for_account(
                    receiving_account
                )
            elif receiving_account == member.account:
                receiver = member

            trans_info["user_role"] = "sender" if (sender == member) else "receiver"
            assert trans_info["user_role"]
            trans_info["transaction"] = transaction
            trans_info["sender"] = sender
            trans_info["receiver"] = receiver
            list_of_trans_infos.append(trans_info)

        return list_of_trans_infos
