"""
ตัวจำลองการปลดหนี้ (Debt Payoff Simulator)
แสดงการใช้ OOP: Abstraction, Inheritance, Polymorphism, Strategy Pattern
"""

from abc import ABC, abstractmethod
from copy import deepcopy


# ======================================================================
# 1) DEBT: abstract class + ลูกแต่ละแบบคิดดอกเบี้ยต่างกัน (Polymorphism)
# ======================================================================
class Debt(ABC): # Main class
    def __init__(self, name, balance, min_payment):
        self.name = name
        self.balance = balance
        self.min_payment = min_payment

    @abstractmethod
    def monthly_interest(self):
        """ดอกเบี้ยที่เกิดขึ้นในเดือนนี้ (แต่ละชนิดคิดไม่เหมือนกัน)"""

    @property
    @abstractmethod
    def effective_rate(self):
        """ดอกเบี้ยต่อปีแบบเทียบเท่า ใช้จัดอันดับความอันตรายของหนี้"""

    @property
    def is_paid_off(self):
        return self.balance <= 0.01

    def pay(self, amount):
        paid = min(amount, self.balance)
        self.balance -= paid
        return paid

    def __repr__(self):
        return f"<{self.name}: {self.balance:,.0f} บาท @ {self.effective_rate:.1%}>"


class CreditCard(Debt):
    def __init__(self, name, balance, min_payment, annual_rate=0.18):
        super().__init__(name, balance, min_payment)
        self.annual_rate = annual_rate

    def monthly_interest(self):
        return self.balance * self.annual_rate / 12

    @property
    def effective_rate(self):
        return self.annual_rate


class CarLoan(Debt):
    """ดอกเบี้ยแบบ flat rate: คิดจากเงินต้นตั้งต้นเสมอ ไม่ใช่ยอดคงเหลือ"""

    def __init__(self, name, balance, min_payment, flat_rate=0.03):
        super().__init__(name, balance, min_payment)
        self.principal = balance
        self.flat_rate = flat_rate

    def monthly_interest(self):
        return self.principal * self.flat_rate / 12 if not self.is_paid_off else 0

    @property
    def effective_rate(self):
        return self.flat_rate * 1.8  # ค่าประมาณ effective rate ของ flat rate


class StudentLoan(Debt):
    def __init__(self, name, balance, min_payment, annual_rate=0.01):
        super().__init__(name, balance, min_payment)
        self.annual_rate = annual_rate

    def monthly_interest(self):
        return self.balance * self.annual_rate / 12

    @property
    def effective_rate(self):
        return self.annual_rate


class LoanShark(Debt):
    """หนี้นอกระบบ: ดอกเบี้ยรายสัปดาห์ แพงที่สุดในกลุ่ม"""

    def __init__(self, name, balance, min_payment, weekly_rate=0.05):
        super().__init__(name, balance, min_payment)
        self.weekly_rate = weekly_rate

    def monthly_interest(self):
        return self.balance * self.weekly_rate * 4

    @property
    def effective_rate(self):
        return self.weekly_rate * 52


# ======================================================================
# 2) STRATEGY: เลือกว่าจะโปะหนี้ก้อนไหนก่อน (Strategy Pattern)
# ======================================================================
class PayoffStrategy(ABC):
    name = "base"

    @abstractmethod
    def pick_target(self, debts):
        ...


class SnowballStrategy(PayoffStrategy):
    name = "Snowball (ยอดน้อยสุดก่อน)"

    def pick_target(self, debts):
        return min(debts, key=lambda d: d.balance)


class AvalancheStrategy(PayoffStrategy):
    name = "Avalanche (ดอกเบี้ยสูงสุดก่อน)"

    def pick_target(self, debts):
        return max(debts, key=lambda d: d.effective_rate)


class HybridStrategy(PayoffStrategy):
    """ปิดหนี้นอกระบบก่อนเสมอ (อันตรายสุด) แล้วค่อยใช้ Avalanche กับที่เหลือ"""

    name = "Hybrid (หนี้นอกระบบก่อน แล้ว Avalanche)"

    def pick_target(self, debts):
        sharks = [d for d in debts if isinstance(d, LoanShark)]
        pool = sharks if sharks else debts
        return max(pool, key=lambda d: d.effective_rate)


# ======================================================================
# 3) SIMULATOR: วนจำลองทีละเดือนจนกว่าหนี้จะหมด
# ======================================================================
class Simulator:
    def __init__(self, debts, monthly_budget, strategy):
        min_total = sum(d.min_payment for d in debts)
        if monthly_budget < min_total:
            raise ValueError(
                f"งบ {monthly_budget:,.0f} น้อยกว่ายอดขั้นต่ำรวม {min_total:,.0f}"
            )
        self.debts = deepcopy(debts)  # แต่ละกลยุทธ์เริ่มจากข้อมูลชุดเดียวกัน
        self.budget = monthly_budget
        self.strategy = strategy

    def run(self, max_months=600):
        months, total_interest, history = 0, 0.0, []

        while any(not d.is_paid_off for d in self.debts) and months < max_months:
            months += 1

            for d in self.debts:  # (1) คิดดอกเบี้ยทุกหนี้
                interest = d.monthly_interest()
                d.balance += interest
                total_interest += interest

            budget = self.budget  # (2) จ่ายขั้นต่ำทุกหนี้
            for d in self.debts:
                budget -= d.pay(d.min_payment)

            while budget > 0.01:  # (3) โปะหนี้เป้าหมายตามกลยุทธ์
                active = [d for d in self.debts if not d.is_paid_off]
                if not active:
                    break
                target = self.strategy.pick_target(active)
                budget -= target.pay(budget)

            history.append(round(sum(d.balance for d in self.debts), 2))

        return SimulationReport(
            strategy_name=self.strategy.name,
            months=months,
            total_interest=round(total_interest, 2),
            history=history,
        )


# ======================================================================
# 4) REPORT: ผลลัพธ์ของการจำลองหนึ่งรอบ
# ======================================================================
class SimulationReport:
    def __init__(self, strategy_name, months, total_interest, history):
        self.strategy_name = strategy_name
        self.months = months
        self.total_interest = total_interest
        self.history = history

    def __str__(self):
        return (
            f"{self.strategy_name}\n"
            f"  หมดหนี้ใน {self.months} เดือน | ดอกเบี้ยรวม {self.total_interest:,.0f} บาท"
        )


def compare_strategies(debts, budget, strategies):
    """รันทุกกลยุทธ์บนหนี้ชุดเดียวกัน แล้วคืนรายงานเรียงตามดอกเบี้ยรวมน้อยสุด"""
    reports = [Simulator(debts, budget, s).run() for s in strategies]
    return sorted(reports, key=lambda r: r.total_interest)


# ======================================================================
# ทดลองรัน
# ======================================================================
print()
print()
if __name__ == "__main__":
    my_debts = [
        CreditCard("บัตรเครดิต A", 40_000, 1_600, annual_rate=0.20),
        CarLoan("ผ่อนรถ", 150_000, 5_000, flat_rate=0.03),
        StudentLoan("กยศ.", 80_000, 1_000, annual_rate=0.01),
        LoanShark("หนี้นอกระบบ", 20_000, 1_500, weekly_rate=0.03),
    ]
    budget = 15_000

    strategies = [SnowballStrategy(), AvalancheStrategy(), HybridStrategy()]
    results = compare_strategies(my_debts, budget, strategies)

    print(f"หนี้ทั้งหมด: {my_debts}\n")
    print(f"เปรียบเทียบ {len(strategies)} กลยุทธ์ (งบ {budget:,.0f} บาท/เดือน)\n")
    for rank, report in enumerate(results, start=1):
        print(f"อันดับ {rank}: {report}\n")


while True:

    try:
        total_Debt = float(input("How many Total Debt >> "))
        feel = input("How are you feeling >> ")
        income_month = float(input("How many income on Monthly >> "))
        income_year = float(input("How many income on year >> "))


    except ValueError:
        print("Need for Value")
