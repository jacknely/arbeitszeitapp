from __future__ import annotations

from functools import wraps

from injector import Binder, CallableProvider, ClassProvider, Injector, inject

from arbeitszeit import entities
from arbeitszeit import repositories as interfaces
from project.extensions import db
from project.models import Account, Company, Member, Offer, SocialAccounting

from .repositories import (
    AccountingRepository,
    AccountOwnerRepository,
    AccountRepository,
    CompanyRepository,
    CompanyWorkerRepository,
    MemberRepository,
    ProductOfferRepository,
    PurchaseRepository,
    TransactionRepository,
)


def configure_injector(binder: Binder) -> None:
    binder.bind(
        interfaces.OfferRepository,
        to=ClassProvider(ProductOfferRepository),
    )
    binder.bind(
        interfaces.TransactionRepository,
        to=ClassProvider(TransactionRepository),
    )
    binder.bind(
        interfaces.CompanyWorkerRepository,
        to=ClassProvider(CompanyWorkerRepository),
    )
    binder.bind(
        interfaces.PurchaseRepository,
        to=ClassProvider(PurchaseRepository),
    )

    binder.bind(
        entities.SocialAccounting,
        to=CallableProvider(get_social_accounting),
    )
    binder.bind(
        interfaces.AccountRepository,
        to=ClassProvider(AccountRepository),
    )
    binder.bind(
        interfaces.MemberRepository,
        to=ClassProvider(MemberRepository),
    )

    binder.bind(
        interfaces.PurchaseRepository,
        to=ClassProvider(PurchaseRepository),
    )

    binder.bind(
        interfaces.AccountOwnerRepository,
        to=ClassProvider(AccountOwnerRepository),
    )


@inject
def get_social_accounting(
    accounting_repo: AccountingRepository,
) -> entities.SocialAccounting:
    return accounting_repo.get_or_create_social_accounting()


_injector = Injector(configure_injector)


def with_injection(original_function):
    """When you wrap a function, make sure that the parameters to be
    injected come after the the parameters that the caller should
    provide.
    """

    @wraps(original_function)
    def wrapped_function(*args, **kwargs):
        return _injector.call_with_injection(
            inject(original_function), args=args, kwargs=kwargs
        )

    return wrapped_function


def commit_changes():
    db.session.commit()


@with_injection
def lookup_product_provider(
    product_offer: entities.ProductOffer,
    company_repository: CompanyRepository,
) -> entities.Company:
    offer_orm = Offer.query.filter_by(id=product_offer.id).first()
    plan_orm = offer_orm.plan
    company_orm = plan_orm.company
    return company_repository.object_from_orm(company_orm)


# User


def get_user_by_mail(email) -> Member:
    """returns first user in User, filtered by email."""
    member = Member.query.filter_by(email=email).first()
    return member


# Company


def get_company_by_mail(email) -> Company:
    """returns first company in Company, filtered by mail."""
    company = Company.query.filter_by(email=email).first()
    return company


def add_new_company(email, name, password) -> Company:
    """
    adds a new company to Company.
    """
    new_company = Company(email=email, name=name, password=password)
    db.session.add(new_company)
    db.session.commit()
    return new_company


def add_new_accounts_for_company(company_id):
    for type in ["p", "r", "a", "prd"]:
        new_account = Account(
            account_owner_company=company_id,
            account_type=type,
        )
        db.session.add(new_account)
        db.session.commit()


# create one social accounting with id=1
def create_social_accounting_in_db() -> None:
    social_accounting = SocialAccounting.query.filter_by(id=1).first()
    if not social_accounting:
        social_accounting = SocialAccounting(id=1)
        db.session.add(social_accounting)
        db.session.commit()


def add_new_account_for_social_accounting():
    account = Account.query.filter_by(account_owner_social_accounting=1).first()
    if not account:
        account = Account(
            account_owner_social_accounting=1,
            account_type="accounting",
        )
        db.session.add(account)
        db.session.commit()
