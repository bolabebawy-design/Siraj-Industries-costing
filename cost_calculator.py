"""
Cost Calculator Engine
محرك حساب التكاليف
"""

from typing import Dict, List, Optional
from .models import Product, Machine, CostResult, MaterialItem
import config


class CostCalculator:
    """
    يحسب التكلفة الكاملة لمنتج بناءً على:
    - تكلفة المواد (Local + Imported)
    - تكلفة التشغيل على الماكينات
    - تكلفة العمالة
    - التعبئة
    - الـ Overhead
    """

    def __init__(
        self,
        machines: Dict[str, Machine],
        exchange_rate_usd: float = None,
        exchange_rate_eur: float = None,
        overhead_pct: float = None,
        profit_margin: float = None,
    ):
        self.machines = machines
        self.usd_rate = exchange_rate_usd or config.EXCHANGE_RATE_USD
        self.eur_rate = exchange_rate_eur or config.EXCHANGE_RATE_EUR
        self.overhead_pct = overhead_pct if overhead_pct is not None else config.DEFAULT_OVERHEAD_PERCENTAGE
        self.profit_margin = profit_margin if profit_margin is not None else config.DEFAULT_PROFIT_MARGIN

    def calculate_material_cost(self, product: Product) -> dict:
        local = 0.0
        imported = 0.0
        details = []

        for item in product.materials:
            total_egp = item.total_egp(self.usd_rate, self.eur_rate)

            if item.is_local:
                local += total_egp
            else:
                imported += total_egp

            details.append({
                "category": item.category,
                "selection": item.selection,
                "qty": item.qty,
                "unit_price": item.unit_price,
                "currency": item.currency,
                "is_local": item.is_local,
                "total_egp": round(total_egp, 2),
            })

        return {
            "local_egp": local,
            "imported_egp": imported,
            "total_egp": local + imported,
            "details": details,
        }

    def calculate_process_cost(self, product: Product) -> dict:
        total_machine = 0.0
        total_labor = 0.0
        breakdown = []
        warnings = []

        for step in product.process_route:
            machine = self.machines.get(step.machine_name)

            if machine is None:
                # محاولة البحث بدون حساسية لحالة الأحرف
                machine = self._find_machine_fuzzy(step.machine_name)

            if machine is None:
                warnings.append(f"الماكينة غير موجودة: {step.machine_name}")
                continue

            hours = step.time_hours
            machine_cost = hours * machine.cost_per_hour_egp

            # تكلفة العمالة الإضافية (لو العدد > 1 يمكن تعديل المنطق لاحقاً)
            # حالياً نفترض أن تكلفة العمالة مدمجة في cost_per_hour للماكينة
            labor_cost = 0.0

            total_machine += machine_cost
            total_labor += labor_cost

            breakdown.append({
                "machine": machine.name,
                "station": machine.station,
                "minutes": step.time_minutes,
                "hours": round(hours, 4),
                "cost_per_hour": round(machine.cost_per_hour_egp, 2),
                "machine_cost": round(machine_cost, 2),
                "operators": step.operators,
            })

        return {
            "machine_cost_egp": total_machine,
            "labor_cost_egp": total_labor,
            "total_process_egp": total_machine + total_labor,
            "breakdown": breakdown,
            "warnings": warnings,
        }

    def _find_machine_fuzzy(self, name: str) -> Optional[Machine]:
        name_lower = name.lower().strip()
        for key, machine in self.machines.items():
            if key.lower().strip() == name_lower:
                return machine
            if name_lower in key.lower() or key.lower() in name_lower:
                return machine
        return None

    def calculate_full_cost(
        self,
        product: Product,
        include_overhead: bool = True,
        custom_overhead_pct: Optional[float] = None,
    ) -> CostResult:
        """
        الحساب الكامل لتكلفة المنتج
        """
        materials = self.calculate_material_cost(product)
        process = self.calculate_process_cost(product)

        packing = product.packing_cost_egp

        direct_cost = (
            materials["total_egp"]
            + process["total_process_egp"]
            + packing
        )

        overhead_pct = custom_overhead_pct if custom_overhead_pct is not None else self.overhead_pct
        overhead = direct_cost * overhead_pct if include_overhead else 0.0

        total_cost = direct_cost + overhead
        suggested_price = total_cost * (1 + self.profit_margin)

        warnings = process.get("warnings", [])

        if not product.process_route:
            warnings.append("لا يوجد مسار تصنيع (Process Route) مسجل لهذا المنتج")

        if materials["total_egp"] == 0:
            warnings.append("تكلفة المواد = صفر - تأكد من تحميل الـ BOM")

        result = CostResult(
            product_name=product.name,
            material_local_egp=materials["local_egp"],
            material_imported_egp=materials["imported_egp"],
            material_total_egp=materials["total_egp"],
            process_machine_egp=process["machine_cost_egp"],
            process_labor_egp=process["labor_cost_egp"],
            packing_egp=packing,
            overhead_egp=overhead,
            total_cost_egp=total_cost,
            suggested_price_egp=suggested_price,
            breakdown={
                "materials_details": materials["details"],
                "process_details": process["breakdown"],
            },
            warnings=warnings,
        )
        return result

    def print_result(self, result: CostResult, detailed: bool = True):
        """طباعة نتيجة منسقة"""
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich import box

        console = Console()

        # العنوان
        console.print(Panel(
            f"[bold cyan]{result.product_name}[/bold cyan]\n"
            f"إجمالي التكلفة: [bold green]{result.total_cost_egp:,.2f} ج.م[/bold green]\n"
            f"سعر البيع المقترح: [bold yellow]{result.suggested_price_egp:,.2f} ج.م[/bold yellow]",
            title="نتيجة حساب التكلفة",
            border_style="blue",
        ))

        # جدول الملخص
        table = Table(title="ملخص التكاليف", box=box.ROUNDED, show_header=True)
        table.add_column("البند", style="cyan")
        table.add_column("القيمة (ج.م)", justify="right", style="green")

        table.add_row("مواد محلية", f"{result.material_local_egp:,.2f}")
        table.add_row("مواد مستوردة", f"{result.material_imported_egp:,.2f}")
        table.add_row("إجمالي المواد", f"{result.material_total_egp:,.2f}")
        table.add_row("تكلفة الماكينات", f"{result.process_machine_egp:,.2f}")
        table.add_row("تكلفة العمالة", f"{result.process_labor_egp:,.2f}")
        table.add_row("التعبئة", f"{result.packing_egp:,.2f}")
        table.add_row("الـ Overhead", f"{result.overhead_egp:,.2f}")
        table.add_row("[bold]الإجمالي[/bold]", f"[bold]{result.total_cost_egp:,.2f}[/bold]")

        console.print(table)

        if result.warnings:
            console.print("\n[bold red]تحذيرات:[/bold red]")
            for w in result.warnings:
                console.print(f"  • {w}")

        if detailed and result.breakdown.get("process_details"):
            console.print("\n")
            ptable = Table(title="تفاصيل التشغيل على الماكينات", box=box.SIMPLE)
            ptable.add_column("الماكينة")
            ptable.add_column("الوقت (دقيقة)", justify="right")
            ptable.add_column("تكلفة الساعة", justify="right")
            ptable.add_column("التكلفة", justify="right")

            for step in result.breakdown["process_details"]:
                ptable.add_row(
                    step["machine"],
                    f"{step['minutes']:.1f}",
                    f"{step['cost_per_hour']:,.2f}",
                    f"{step['machine_cost']:,.2f}",
                )
            console.print(ptable)
