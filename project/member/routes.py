from typing import cast
from uuid import UUID

from flask import Response, render_template, request
from flask_login import current_user

from arbeitszeit import use_cases
from arbeitszeit_web.get_member_profile_info import GetMemberProfileInfoPresenter
from arbeitszeit_web.get_plan_summary import GetPlanSummarySuccessPresenter
from arbeitszeit_web.get_statistics import GetStatisticsPresenter
from arbeitszeit_web.pay_consumer_product import (
    PayConsumerProductController,
    PayConsumerProductPresenter,
)
from arbeitszeit_web.query_plans import QueryPlansController, QueryPlansPresenter
from arbeitszeit_web.query_products import (
    QueryProductsController,
    QueryProductsPresenter,
)
from project.database import AccountRepository, MemberRepository, commit_changes
from project.forms import PayConsumerProductForm, PlanSearchForm, ProductSearchForm
from project.models import Member
from project.url_index import MemberUrlIndex
from project.views import (
    Http404View,
    PayConsumerProductView,
    QueryPlansView,
    QueryProductsView,
)

from .blueprint import MemberRoute


@MemberRoute("/member/kaeufe")
def my_purchases(
    query_purchases: use_cases.QueryPurchases, member_repository: MemberRepository
) -> Response:
    member = member_repository.get_by_id(UUID(current_user.id))
    assert member is not None
    purchases = list(query_purchases(member))
    return Response(render_template("member/my_purchases.html", purchases=purchases))


@MemberRoute("/member/suchen", methods=["GET", "POST"])
def suchen(
    query_products: use_cases.QueryProducts,
    controller: QueryProductsController,
) -> Response:
    template_name = "member/query_products.html"
    search_form = ProductSearchForm(request.form)
    presenter = QueryProductsPresenter(
        MemberUrlIndex(),
    )
    view = QueryProductsView(
        search_form, query_products, presenter, controller, template_name
    )
    if request.method == "POST":
        return view.respond_to_post()
    else:
        return view.respond_to_get()


@MemberRoute("/member/query_plans", methods=["GET", "POST"])
def query_plans(
    query_plans: use_cases.QueryPlans,
    controller: QueryPlansController,
) -> Response:
    presenter = QueryPlansPresenter(MemberUrlIndex())
    template_name = "member/query_plans.html"
    search_form = PlanSearchForm(request.form)
    view = QueryPlansView(
        search_form, query_plans, presenter, controller, template_name
    )
    if request.method == "POST":
        return view.respond_to_post()
    else:
        return view.respond_to_get()


@MemberRoute("/member/pay_consumer_product", methods=["GET", "POST"])
@commit_changes
def pay_consumer_product(
    pay_consumer_product: use_cases.PayConsumerProduct,
    presenter: PayConsumerProductPresenter,
    controller: PayConsumerProductController,
) -> Response:
    view = PayConsumerProductView(
        form=PayConsumerProductForm(request.form),
        current_user=UUID(current_user.id),
        pay_consumer_product=pay_consumer_product,
        controller=controller,
        presenter=presenter,
    )
    if request.method == "POST":
        return view.respond_to_post()
    else:
        return view.respond_to_get()


@MemberRoute("/member/profile")
def profile(
    get_member_profile: use_cases.GetMemberProfileInfo,
    presenter: GetMemberProfileInfoPresenter,
) -> Response:
    member_profile = get_member_profile(UUID(current_user.id))
    view_model = presenter.present(member_profile)
    return Response(
        render_template(
            "member/profile.html",
            view_model=view_model,
        )
    )


@MemberRoute("/member/my_account")
def my_account(
    member_repository: MemberRepository,
    get_transaction_infos: use_cases.GetTransactionInfos,
    account_repository: AccountRepository,
) -> Response:
    # We can assume current_user to be a LocalProxy which delegates to
    # Member since we did a `user_is_member` check earlier
    member = member_repository.object_from_orm(cast(Member, current_user))
    list_of_trans_infos = get_transaction_infos(member)
    return render_template(
        "member/my_account.html",
        all_transactions_info=list_of_trans_infos,
        my_balance=account_repository.get_account_balance(member.account),
    )


@MemberRoute("/member/statistics")
def statistics(
    get_statistics: use_cases.GetStatistics,
    presenter: GetStatisticsPresenter,
) -> Response:
    use_case_response = get_statistics()
    view_model = presenter.present(use_case_response)
    return Response(render_template("member/statistics.html", view_model=view_model))


@MemberRoute("/member/plan_summary/<uuid:plan_id>")
def plan_summary(
    plan_id: UUID,
    get_plan_summary: use_cases.GetPlanSummary,
    presenter: GetPlanSummarySuccessPresenter,
) -> Response:
    use_case_response = get_plan_summary(plan_id)
    if isinstance(use_case_response, use_cases.PlanSummarySuccess):
        view_model = presenter.present(use_case_response)
        return Response(
            render_template("member/plan_summary.html", view_model=view_model.to_dict())
        )
    else:
        return Http404View(template="member/404.html").get_response()


@MemberRoute("/member/hilfe")
def hilfe() -> Response:
    return Response(render_template("member/help.html"))
