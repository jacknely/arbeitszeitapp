from arbeitszeit.use_cases import GetMemberProfileInfo
from tests.data_generators import CompanyGenerator, MemberGenerator

from .dependency_injection import injection_test
from .repositories import CompanyWorkerRepository


@injection_test
def test_that_correct_workplace_email_is_shown(
    get_member_info: GetMemberProfileInfo,
    company_worker_repository: CompanyWorkerRepository,
    member_generator: MemberGenerator,
    company_generator: CompanyGenerator,
):
    worker = member_generator.create_member()
    workplace = company_generator.create_company(email="companyname@mail.com")
    company_worker_repository.add_worker_to_company(workplace, worker)

    member_info = get_member_info(worker.id)
    assert member_info.workplaces[0].workplace_email == "companyname@mail.com"


@injection_test
def test_that_correct_workplace_name_is_shown(
    get_member_info: GetMemberProfileInfo,
    company_worker_repository: CompanyWorkerRepository,
    member_generator: MemberGenerator,
    company_generator: CompanyGenerator,
):
    worker = member_generator.create_member()
    workplace = company_generator.create_company(name="SomeCompanyNameXY")
    company_worker_repository.add_worker_to_company(workplace, worker)

    member_info = get_member_info(worker.id)
    assert member_info.workplaces[0].workplace_name == "SomeCompanyNameXY"
