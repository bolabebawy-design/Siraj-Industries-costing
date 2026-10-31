"""
Siraj Industries - Product Costing System
نظام حساب تكاليف المنتجات - مصانع سراج

طريقة التشغيل:
    python main.py
    python main.py --product "Glow IP20 60x60 40W On-Off"
    python main.py --list
    python main.py --machines
"""

import argparse
import sys
from pathlib import Path

# إضافة المجلد الحالي للـ path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box

import config
from loaders.machine_loader import load_machines, print_machines_summary
from loaders.product_loader import (
    list_available_products,
    load_product_from_sheet,
    get_default_route,
)
from core.cost_calculator import CostCalculator
from core.models import ProcessStep


console = Console()


def show_banner():
    console.print(Panel(
        f"[bold cyan]{config.COMPANY_NAME}[/bold cyan]\n"
        f"[bold]{config.COMPANY_NAME_AR}[/bold]\n\n"
        "نظام حساب تكاليف المنتجات\n"
        "Product Costing System",
        border_style="blue",
        padding=(1, 4),
    ))


def cmd_list_products():
    """عرض كل المنتجات المتاحة"""
    try:
        products = list_available_products()
        console.print(f"\n[bold green]عدد المنتجات المتاحة: {len(products)}[/bold green]\n")

        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("اسم المنتج", style="cyan")

        for i, name in enumerate(products, 1):
            table.add_row(str(i), name)

        console.print(table)
    except FileNotFoundError as e:
        console.print(f"[red]خطأ: {e}[/red]")
        console.print(f"[yellow]تأكد من وجود الملف في: {config.PRODUCTS_FILE}[/yellow]")


def cmd_show_machines():
    """عرض ملخص الماكينات"""
    try:
        machines = load_machines()
        print_machines_summary(machines)
    except FileNotFoundError as e:
        console.print(f"[red]خطأ: {e}[/red]")
        console.print(f"[yellow]تأكد من وجود الملف في: {config.MACHINES_FILE}[/yellow]")


def cmd_calculate(product_name: str, detailed: bool = True):
    """حساب تكلفة منتج معين"""
    console.print(f"\n[bold]جاري تحميل البيانات...[/bold]")

    try:
        machines = load_machines()
        console.print(f"  ✓ تم تحميل {len(machines)} ماكينة")
    except Exception as e:
        console.print(f"[red]فشل تحميل الماكينات: {e}[/red]")
        return

    # مسار التصنيع
    route = get_default_route(product_name)
    if not route:
        console.print("[yellow]⚠ لا يوجد مسار تصنيع افتراضي لهذا المنتج. سيتم حساب المواد فقط.[/yellow]")

    try:
        product = load_product_from_sheet(product_name, process_route=route)
        console.print(f"  ✓ تم تحميل المنتج: {product.name}")
        console.print(f"  ✓ عدد أصناف المواد: {len(product.materials)}")
    except Exception as e:
        console.print(f"[red]فشل تحميل المنتج: {e}[/red]")
        return

    # الحساب
    calculator = CostCalculator(machines)
    result = calculator.calculate_full_cost(product)

    console.print()
    calculator.print_result(result, detailed=detailed)

    return result


def interactive_mode():
    """وضع تفاعلي"""
    show_banner()

    while True:
        console.print("\n[bold cyan]القائمة الرئيسية[/bold cyan]")
        console.print("  1. حساب تكلفة منتج")
        console.print("  2. عرض كل المنتجات")
        console.print("  3. عرض تكلفة الماكينات")
        console.print("  4. خروج")

        choice = Prompt.ask("\nاختر", choices=["1", "2", "3", "4"], default="1")

        if choice == "1":
            products = list_available_products()
            console.print("\n[dim]اكتب جزء من اسم المنتج أو الرقم[/dim]")
            query = Prompt.ask("اسم المنتج")

            # لو رقم
            if query.isdigit():
                idx = int(query) - 1
                if 0 <= idx < len(products):
                    product_name = products[idx]
                else:
                    console.print("[red]رقم غير صحيح[/red]")
                    continue
            else:
                # بحث
                matches = [p for p in products if query.lower() in p.lower()]
                if not matches:
                    console.print("[red]لم يتم العثور على منتج[/red]")
                    continue
                if len(matches) == 1:
                    product_name = matches[0]
                else:
                    console.print("\nنتائج البحث:")
                    for i, m in enumerate(matches[:15], 1):
                        console.print(f"  {i}. {m}")
                    sel = Prompt.ask("اختر رقم", default="1")
                    product_name = matches[int(sel) - 1]

            cmd_calculate(product_name)

        elif choice == "2":
            cmd_list_products()

        elif choice == "3":
            cmd_show_machines()

        elif choice == "4":
            console.print("\n[bold]مع السلامة 👋[/bold]\n")
            break


def main():
    parser = argparse.ArgumentParser(
        description="Siraj Industries - Product Costing System"
    )
    parser.add_argument("--product", "-p", type=str, help="اسم المنتج لحساب تكلفته")
    parser.add_argument("--list", "-l", action="store_true", help="عرض كل المنتجات")
    parser.add_argument("--machines", "-m", action="store_true", help="عرض تكلفة الماكينات")
    parser.add_argument("--interactive", "-i", action="store_true", help="الوضع التفاعلي")

    args = parser.parse_args()

    if args.list:
        show_banner()
        cmd_list_products()
    elif args.machines:
        show_banner()
        cmd_show_machines()
    elif args.product:
        show_banner()
        cmd_calculate(args.product)
    else:
        # الوضع التفاعلي افتراضي
        interactive_mode()


if __name__ == "__main__":
    main()
