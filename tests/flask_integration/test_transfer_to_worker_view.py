from arbeitszeit_flask.database.repositories import CompanyWorkerRepository

from .flask import ViewTestCase


class AuthenticatedCompanyTests(ViewTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.company, _, self.email = self.login_company()
        self.company = self.confirm_company(company=self.company, email=self.email)
        self.url = "company/transfer_to_worker"
        self.company_worker_repository = self.injector.get(CompanyWorkerRepository)

    def test_company_gets_200_when_accessing_page(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_posting_without_data_results_in_400(self) -> None:
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)

    def test_company_gets_200_when_posting_correct_data(self) -> None:
        worker = self.member_generator.create_member()
        self.company_worker_repository.add_worker_to_company(self.company, worker)
        response = self.client.post(
            self.url,
            data=dict(member_id=str(worker.id), amount="10"),
        )
        self.assertEqual(response.status_code, 200)

    def test_company_gets_404_when_posting_incorrect_data_with_worker_not_in_company(
        self,
    ) -> None:
        worker = self.member_generator.create_member()
        response = self.client.post(
            self.url,
            data=dict(member_id=str(worker.id), amount="10"),
        )
        self.assertEqual(response.status_code, 404)

    def test_company_gets_400_when_posting_incorrect_data_with_negative_amount(
        self,
    ) -> None:
        worker = self.member_generator.create_member()
        self.company_worker_repository.add_worker_to_company(self.company, worker)
        response = self.client.post(
            self.url,
            data=dict(member_id=str(worker.id), amount="-10"),
        )
        self.assertEqual(response.status_code, 400)
