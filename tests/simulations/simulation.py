from decimal import Decimal

from arbeitszeit.entities import ProductionCosts
from arbeitszeit.price_calculator import calculate_price
from tests.data_generators import CompanyGenerator, CooperationGenerator, PlanGenerator

from tests.flask_integration.dependency_injection import injection_test


def add_start_and_end_statements(func):
    def decorated_func(self, *args, **kwargs):
        self.start_statement(self.name, self.research_question)
        result = func(self, *args, **kwargs)
        self.end_statement()
        return result

    return decorated_func


class Simulation:
    @injection_test
    def __init__(
        self,
        company_generator: CompanyGenerator,
        plan_generator: PlanGenerator,
        coop_generator: CooperationGenerator,
    ) -> None:
        self.company_generator = company_generator
        self.plan_generator = plan_generator
        self.coop_generator = coop_generator

    def start_statement(self, name, research_question):
        print(
            f"""============\nSTART SIMULATION...\n\nNAME: {name}\nRESEARCH QUESTION: {research_question}\n"""
        )

    def end_statement(self):
        print("""\nEND SIMULATION...\n============""")


class CooperationOfTwoPlans(Simulation):
    def __init__(self) -> None:
        super().__init__()
        self.name = type(self).__name__
        self.research_question = "How do plan attributes affect the coop price?"

    @add_start_and_end_statements
    def simulate(self):
        TIMEFRAME1, TIMEFRAME2 = 100, 10
        COST1, COST2 = 20, 30
        AMOUNT1, AMOUNT2 = 20, 40
        plan1 = self.plan_generator.create_plan(
            timeframe=TIMEFRAME1,
            costs=ProductionCosts(Decimal(COST1), Decimal(0), Decimal(0)),
            amount=AMOUNT1,
        )
        plan2 = self.plan_generator.create_plan(
            timeframe=TIMEFRAME2,
            costs=ProductionCosts(Decimal(COST2), Decimal(0), Decimal(0)),
            amount=AMOUNT2,
        )
        print(
            f"Two plans created...\n- Plan 1: Timeframe {TIMEFRAME1}, costs {COST1}, amount {AMOUNT1}.\n- Plan 2: Timeframe {TIMEFRAME2}, costs {COST2}, amount {AMOUNT2}."
        )
        print(f"- Plans have id: {plan1.id}, {plan2.id}")
        print()
        cooperation = self.coop_generator.create_cooperation(plans=[plan1, plan2])
        print(
            f"Coop created...\n- Coop has id: {cooperation.id}\n- Both plans joined this cooperation."
        )
        print()
        print("Price calculation...")
        price1 = calculate_price([plan1])
        price2 = calculate_price([plan2])
        coop_price = calculate_price([plan1, plan2])
        print(
            f"- Price for plan1 = {round(price1, 4)}\n- Price for plan2 = {round(price2, 4)}"
        )
        print(f"- Coop price = {round(coop_price, 4)}")
