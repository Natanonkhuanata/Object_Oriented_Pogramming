"""
ตัวจำลองการปลดหนี้ (Debt Payoff Simulator) - เวอร์ชันให้ผู้ใช้กรอกหนี้เอง
"""

from abc import ABC, abstractmethod
from copy import deepcopy


# ======================================================================
# 1) DEBT: abstract class + ลูกแต่ละแบบคิดดอกเบี้ยต่างกัน (Polymorphism)
# ======================================================================
class Debt(ABC): # Main class ของหหนี้แต่ละชนิด
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


class CreditCard(Debt): # หนี้บัตรเครดิต: ดอกเบี้ยแบบลดต้นลดดอก (compounding interest)
    def __init__(self, name, balance, min_payment, annual_rate=0.18):
        super().__init__(name, balance, min_payment)
        self.annual_rate = annual_rate

    def monthly_interest(self):
        return self.balance * self.annual_rate / 12

    @property
    def effective_rate(self):
        return self.annual_rate


class CarLoan(Debt): # หนี้รถยนต์: ดอกเบี้ยแบบ flat rate (คิดจากเงินตั้งต้นเสมอ)
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


class StudentLoan(Debt): # หนนี้กยศ. / เงินกู้เพื่อการศึกษา: ดอกเบี้ยแบบลดต้นลดดอก
    def __init__(self, name, balance, min_payment, annual_rate=0.01):
        super().__init__(name, balance, min_payment)
        self.annual_rate = annual_rate

    def monthly_interest(self):
        return self.balance * self.annual_rate / 12

    @property
    def effective_rate(self):
        return self.annual_rate


class LoanShark(Debt): # หนี้นอกระบบ: ดอกเบี้ยรวมไม่ควรเกิน 5% ต่อสัปดาห์ หรือ 260% ต่อปี และ 20% ต่อเดือน ตามกฏหมายของประเทศไทย
    """หนี้นอกระบบ: ดอกเบี้ยรายสัปดาห์ แพงที่สุดในกลุ่ม"""

    def __init__(self, name, balance, min_payment, weekly_rate=0.05):
        super().__init__(name, balance, min_payment)
        self.weekly_rate = weekly_rate

    def monthly_interest(self):
        return self.balance * self.weekly_rate * 4

    @property
    def effective_rate(self):
        return self.weekly_rate * 52


class PersonalLoan(Debt): # หนี้ส่วนบุคคล: ดอกเบี้ยแบบลดต้นลดดอก 
    """สินเชื่อส่วนบุคคล: ดอกเบี้ยลดต้นลดดอกแบบธนาคารทั่วไป"""

    def __init__(self, name, balance, min_payment, annual_rate=0.10):
        super().__init__(name, balance, min_payment)
        self.annual_rate = annual_rate

    def monthly_interest(self):
        return self.balance * self.annual_rate / 12

    @property
    def effective_rate(self):
        return self.annual_rate


# แมปชนิดหนี้ที่ให้ผู้ใช้เลือก กับ class และอัตราดอกเบี้ยเริ่มต้น
DEBT_TYPES = {
    "1": ("บัตรเครดิต", CreditCard, 0.18, "annual_rate"),
    "2": ("ผ่อนรถ", CarLoan, 0.03, "flat_rate"),
    "3": ("กยศ. / เงินกู้เพื่อการศึกษา", StudentLoan, 0.01, "annual_rate"),
    "4": ("หนี้นอกระบบ", LoanShark, 0.03, "weekly_rate"),
    "5": ("สินเชื่อส่วนบุคคล", PersonalLoan, 0.10, "annual_rate"),
}


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
        self.debts = deepcopy(debts)
        self.budget = monthly_budget
        self.strategy = strategy

    def run(self, max_months=600):
        months, total_interest, history = 0, 0.0, []

        while any(not d.is_paid_off for d in self.debts) and months < max_months:
            months += 1

            for d in self.debts:
                interest = d.monthly_interest()
                d.balance += interest
                total_interest += interest

            budget = self.budget
            for d in self.debts:
                budget -= d.pay(d.min_payment)

            while budget > 0.01:
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
# 4) REPORT
# ======================================================================
class SimulationReport:
    def __init__(self, strategy_name, months, total_interest, history):
        self.strategy_name = strategy_name
        self.months = months
        self.total_interest = total_interest
        self.history = history

    def __str__(self):
        years = self.months // 12
        rem_months = self.months % 12
        duration = f"{years} ปี {rem_months} เดือน" if years else f"{rem_months} เดือน"
        return (
            f"{self.strategy_name}\n"
            f"  หมดหนี้ใน {self.months} เดือน ({duration})\n"
            f"  ดอกเบี้ยรวมที่ต้องจ่าย {self.total_interest:,.0f} บาท"
        )


def compare_strategies(debts, budget, strategies):
    reports = [Simulator(debts, budget, s).run() for s in strategies]
    return sorted(reports, key=lambda r: r.total_interest)


# ======================================================================
# 5) INPUT: ให้ผู้ใช้กรอกหนี้ของตัวเองทีละก้อน
# ======================================================================
def ask_float(prompt, min_value=0):
    """รับตัวเลขจากผู้ใช้ วนถามใหม่ถ้ากรอกผิดหรือค่าต่ำกว่าที่กำหนด"""
    while True:
        raw = input(prompt).strip().replace(",", "")
        try:
            value = float(raw)
            if value < min_value:
                print(f"  ค่าต้องไม่น้อยกว่า {min_value} ลองใหม่อีกครั้ง")
                continue
            return value
        except ValueError:
            print("  กรุณากรอกเป็นตัวเลข เช่น 15000 หรือ 15000.50")


def choose_debt_type():
    print("\nเลือกประเภทหนี้:")
    for key, (label, _, _, _) in DEBT_TYPES.items():
        print(f"  {key}. {label}")
    while True:
        choice = input("กรุณากรอกหมายเลข (หรือพิมพ์ 'จบ' ถ้ากรอกครบแล้ว): ").strip()
        if choice.lower() in ("จบ", "done", "exit"):
            return None
        if choice in DEBT_TYPES:
            return choice
        print("  เลือกไม่ถูกต้อง ลองใหม่อีกครั้ง")


def collect_debts_from_user():
    """วนรับหนี้ทีละก้อนจากผู้ใช้ จนกว่าจะพิมพ์ 'จบ'"""
    debts = []
    print("=== กรอกรายการหนี้ของคุณ ===")

    while True:
        type_key = choose_debt_type()
        if type_key is None:
            break

        label, debt_class, default_rate, rate_field = DEBT_TYPES[type_key]
        name = input(f"ชื่อหนี้ (เช่น '{label} ธนาคาร A'): ").strip() or label
        balance = ask_float("ยอดหนี้คงเหลือ (บาท): ", min_value=1)
        min_payment = ask_float("ยอดผ่อนขั้นต่ำต่อเดือน (บาท): ", min_value=1)

        rate_prompt = {
            "annual_rate": f"ดอกเบี้ยต่อปี % (ค่าเริ่มต้น {default_rate:.1%}, เคาะ Enter ใช้ค่าเริ่มต้น): ",
            "flat_rate": f"ดอกเบี้ย flat rate ต่อปี % (ค่าเริ่มต้น {default_rate:.1%}): ",
            "weekly_rate": f"ดอกเบี้ยต่อสัปดาห์ % (ค่าเริ่มต้น {default_rate:.1%}): ",
        }[rate_field]

        raw_rate = input(rate_prompt).strip()
        rate = float(raw_rate) / 100 if raw_rate else default_rate

        debt = debt_class(name, balance, min_payment, **{rate_field: rate})
        debts.append(debt)
        print(f"  ➜ เพิ่มแล้ว: {debt}")

    return debts


def ask_monthly_budget(debts):
    min_total = sum(d.min_payment for d in debts)
    print(f"\nยอดผ่อนขั้นต่ำรวมของคุณคือ {min_total:,.0f} บาท/เดือน")
    while True:
        budget = ask_float("งบที่พร้อมจ่ายหนี้ต่อเดือน (บาท): ", min_value=1)
        if budget < min_total:
            print(f"  งบต้องไม่น้อยกว่ายอดขั้นต่ำรวม {min_total:,.0f} บาท ลองใหม่")
            continue
        return budget


# ======================================================================
# 6) MAIN: เชื่อมทุกส่วนเข้าด้วยกัน
# ======================================================================
def main():
    debts = collect_debts_from_user()
    if not debts:
        print("ไม่มีหนี้ให้วิเคราะห์ จบโปรแกรม")
        return

    budget = ask_monthly_budget(debts)

    print("\n" + "=" * 50)
    print("สรุปหนี้ทั้งหมดของคุณ")
    print("=" * 50)
    for d in debts:
        print(f"  {d}")
    print(f"\nงบที่ใช้จ่ายหนี้ต่อเดือน: {budget:,.0f} บาท")

    strategies = [SnowballStrategy(), AvalancheStrategy(), HybridStrategy()]
    results = compare_strategies(debts, budget, strategies)

    print("\n" + "=" * 50)
    print("ผลการวิเคราะห์ (เรียงจากดอกเบี้ยรวมน้อยสุด)")
    print("=" * 50)
    for rank, report in enumerate(results, start=1):
        print(f"\nอันดับ {rank}: {report}")

    best = results[0]
    print(f"\n💡 กลยุทธ์ที่เหมาะกับคุณที่สุด (ดอกเบี้ยถูกสุด): {best.strategy_name}")


if __name__ == "__main__":
    main()