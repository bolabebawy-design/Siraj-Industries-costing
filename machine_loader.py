"""
Machine Cost Loader
تحميل بيانات تكلفة الماكينات من ملف Machines cost-hour-1.xlsx
"""

from pathlib import Path
from typing import Dict
import pandas as pd
from openpyxl import load_workbook

from core.models import Machine
import config


def load_machines(file_path: Path = None) -> Dict[str, Machine]:
    """
    يقرأ شيت 'Machinery Cost' ويعيد قاموس بالماكينات.
    المفتاح = اسم الماكينة
    """
    path = file_path or config.MACHINES_FILE

    if not path.exists():
        raise FileNotFoundError(f"ملف الماكينات غير موجود: {path}")

    # قراءة باستخدام pandas للسهولة
    df = pd.read_excel(path, sheet_name="Machinery Cost", header=0)

    # تنظيف أسماء الأعمدة
    df.columns = [str(c).strip() for c in df.columns]

    machines = {}

    for _, row in df.iterrows():
        name = str(row.get("Machine", "")).strip()
        if not name or name.lower() == "nan" or name == "":
            continue

        station = str(row.get("Station", "")).strip()
        if station.lower() == "nan":
            station = ""

        # التكلفة بالساعة هي الأهم
        cost_per_hour = _safe_float(row.get("Machine/hour"))
        cost_per_day = _safe_float(row.get("Machine/day"))

        machine = Machine(
            name=name,
            station=station,
            cost_per_hour_egp=cost_per_hour,
            cost_per_day_egp=cost_per_day,
            depreciation_per_day=_safe_float(row.get("Deperation")),
            energy_per_day=_safe_float(row.get("Energy EGP")),
            utilities_per_day=_safe_float(row.get("Utilities")),
            manuf_consumables_per_day=_safe_float(row.get("Manufacture Consumables EGP")),
            maint_consumables_per_day=_safe_float(row.get("Maint Consumables EGP")),
            manpower_per_day=_safe_float(row.get("Man power EGP")),
            price_egp=_safe_float(row.get("Price EGP")),
            depreciation_class=str(row.get("Deperation Class", "")).strip(),
        )
        machines[name] = machine

    return machines


def _safe_float(value) -> float:
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def print_machines_summary(machines: Dict[str, Machine]):
    """طباعة ملخص الماكينات"""
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console()
    table = Table(title="ملخص تكلفة الماكينات (ج.م / ساعة)", box=box.ROUNDED)

    table.add_column("المحطة", style="cyan")
    table.add_column("الماكينة")
    table.add_column("تكلفة/ساعة", justify="right", style="green")
    table.add_column("تكلفة/يوم", justify="right")

    # ترتيب حسب المحطة ثم الاسم
    sorted_machines = sorted(machines.values(), key=lambda m: (m.station, m.name))

    for m in sorted_machines:
        table.add_row(
            m.station or "-",
            m.name,
            f"{m.cost_per_hour_egp:,.2f}",
            f"{m.cost_per_day_egp:,.2f}",
        )

    console.print(table)
    console.print(f"\n[bold]إجمالي الماكينات المحملة: {len(machines)}[/bold]")
