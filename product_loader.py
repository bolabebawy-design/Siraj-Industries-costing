"""
Product BOM Loader
تحميل قائمة المواد (BOM) من شيتات المنتجات
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import re
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from core.models import Product, MaterialItem, ProcessStep
import config


def list_available_products(file_path: Path = None) -> List[str]:
    """يرجع قائمة بأسماء كل المنتجات (أسماء الشيتات)"""
    path = file_path or config.PRODUCTS_FILE
    if not path.exists():
        raise FileNotFoundError(f"ملف المنتجات غير موجود: {path}")

    wb = load_workbook(path, read_only=True, data_only=True)
    # استبعاد الشيتات الخاصة
    exclude = {"Rate", "Home", "Sheet1", "Sheet2", "Sheet3"}
    products = [name.strip() for name in wb.sheetnames if name.strip() not in exclude]
    wb.close()
    return products


def load_product_from_sheet(
    product_name: str,
    file_path: Path = None,
    process_route: Optional[List[ProcessStep]] = None,
) -> Product:
    """
    يحمل منتج من شيت معين ويستخرج الـ BOM.

    ملاحظات على هيكل الشيت:
    - الصفوف الأولى تحتوي على headers
    - الأعمدة تقريباً:
        B: Category
        D: Selection
        E: Unit
        F: QTY
        G: U/P
        H: Total
        I: Freight
        J: Duties
        K: Total Currency
        L: Total L.E.
        ...
    """
    path = file_path or config.PRODUCTS_FILE
    if not path.exists():
        raise FileNotFoundError(f"ملف المنتجات غير موجود: {path}")

    wb = load_workbook(path, data_only=True)

    # البحث عن الشيت (مع تجاهل المسافات الزائدة)
    sheet_name = None
    for name in wb.sheetnames:
        if name.strip() == product_name.strip():
            sheet_name = name
            break

    if sheet_name is None:
        # محاولة بحث جزئي
        for name in wb.sheetnames:
            if product_name.strip().lower() in name.strip().lower():
                sheet_name = name
                break

    if sheet_name is None:
        available = list_available_products(path)
        raise ValueError(
            f"المنتج '{product_name}' غير موجود.\n"
            f"المنتجات المتاحة (أول 10): {available[:10]}"
        )

    ws = wb[sheet_name]
    materials = _extract_materials(ws)
    packing_cost = _extract_packing_cost(ws)

    product = Product(
        name=product_name.strip(),
        materials=materials,
        process_route=process_route or [],
        packing_cost_egp=packing_cost,
    )

    # محاولة استخراج معلومات إضافية من الاسم
    _enrich_product_info(product)

    wb.close()
    return product


def _extract_materials(ws: Worksheet) -> List[MaterialItem]:
    """استخراج عناصر الـ BOM من الشيت"""
    materials = []

    # نبدأ من الصف 3 تقريباً (بعد الـ headers)
    for row_idx in range(1, min(ws.max_row + 1, 80)):
        category = _cell_str(ws, row_idx, 2)          # Column B
        selection = _cell_str(ws, row_idx, 4)         # Column D
        unit = _cell_str(ws, row_idx, 5)              # Column E
        qty = _cell_float(ws, row_idx, 6)             # Column F
        unit_price = _cell_float(ws, row_idx, 7)      # Column G
        freight = _cell_float(ws, row_idx, 9)         # Column I
        duties = _cell_float(ws, row_idx, 10)         # Column J

        # تخطي الصفوف الفارغة أو الـ headers
        if not selection and not category:
            continue
        if selection.lower() in ("selection", "unit", ""):
            continue
        if category.lower() in ("category", "over head & labour", "man power", "power"):
            continue

        # تحديد إذا كان محلي أم مستورد
        # عادة المواد المحلية يكون لها قيم في عمود Local
        local_val = _cell_float(ws, row_idx, 16)     # عمود Local تقريباً
        is_local = local_val > 0 and unit_price == 0

        # تحديد العملة (افتراضي USD للمواد المستوردة)
        currency = "USD"
        if is_local or unit_price == 0:
            # لو السعر بالجنيه مباشرة
            currency = "EGP"

        # بعض الأصناف المحلية سعرها بالجنيه في عمود U/P
        if unit_price > 0 and unit_price < 50 and not freight:
            # احتمال تكون جنيه (مثل البراغي والسلك)
            pass

        item = MaterialItem(
            category=category or "General",
            selection=selection,
            unit=unit or "Pcs",
            qty=qty if qty > 0 else 1.0,
            unit_price=unit_price,
            currency=currency,
            is_local=is_local,
            freight=freight,
            duties=duties,
        )

        # فقط نضيف العناصر اللي لها تكلفة أو كمية واضحة
        if item.qty > 0 and (item.unit_price > 0 or item.freight > 0 or item.duties > 0 or is_local):
            materials.append(item)

    return materials


def _extract_packing_cost(ws: Worksheet) -> float:
    """محاولة استخراج تكلفة التعبئة من الشيت"""
    packing_total = 0.0
    for row_idx in range(1, min(ws.max_row + 1, 80)):
        category = _cell_str(ws, row_idx, 2).lower()
        selection = _cell_str(ws, row_idx, 4).lower()

        if "packing" in category or "carton" in selection or "master box" in selection \
                or "plastic bag" in selection or "foam" in selection and "packing" in category:
            # نأخذ قيمة Total L.E. إن وجدت
            total_le = _cell_float(ws, row_idx, 12)  # Column L تقريباً
            if total_le > 0:
                packing_total += total_le
            else:
                # أو U/P * QTY
                qty = _cell_float(ws, row_idx, 6)
                up = _cell_float(ws, row_idx, 7)
                packing_total += qty * up

    return packing_total


def _enrich_product_info(product: Product):
    """استخراج معلومات من اسم المنتج"""
    name = product.name.lower()

    # IP Rating
    if "ip20" in name:
        product.ip_rating = "IP20"
    elif "ip54" in name:
        product.ip_rating = "IP54"
    elif "ip65" in name:
        product.ip_rating = "IP65"

    # Control type
    if "dali" in name:
        product.control_type = "Dali"
    elif "phase cut" in name:
        product.control_type = "Phase Cut"
    elif "0-10v" in name or "0-10" in name:
        product.control_type = "0-10V"
    elif "on-off" in name or "on/off" in name:
        product.control_type = "On-Off"

    # Power
    match = re.search(r"(\d+)\s*w", name)
    if match:
        product.power_watt = float(match.group(1))


def _cell_str(ws: Worksheet, row: int, col: int) -> str:
    val = ws.cell(row=row, column=col).value
    if val is None:
        return ""
    return str(val).strip()


def _cell_float(ws: Worksheet, row: int, col: int) -> float:
    val = ws.cell(row=row, column=col).value
    try:
        if val is None:
            return 0.0
        return float(val)
    except (ValueError, TypeError):
        return 0.0


# ============================================================
# Process Routes (يمكن نقلها لاحقاً لملف Excel منفصل)
# ============================================================

# أمثلة أولية - يجب تعديلها حسب الواقع في المصنع
DEFAULT_PROCESS_ROUTES: Dict[str, List[ProcessStep]] = {
    "Glow IP20 60x60 40W On-Off": [
        ProcessStep("LASER CUTTING MACHINE", time_minutes=4.0),
        ProcessStep("CNC PRESS BRAKE", time_minutes=2.5),
        ProcessStep("Paint shop", time_minutes=10.0),
        ProcessStep("line A", time_minutes=15.0),
        ProcessStep("Smt Line", time_minutes=3.0),
    ],
    "Glow IP20 60x60 40W Dali": [
        ProcessStep("LASER CUTTING MACHINE", time_minutes=4.0),
        ProcessStep("CNC PRESS BRAKE", time_minutes=2.5),
        ProcessStep("Paint shop", time_minutes=10.0),
        ProcessStep("line A", time_minutes=16.0),
        ProcessStep("Smt Line", time_minutes=3.0),
    ],
    # أضف باقي المنتجات هنا أو من ملف Excel
}


def get_default_route(product_name: str) -> List[ProcessStep]:
    """يرجع مسار تصنيع افتراضي إن وجد"""
    # بحث دقيق
    if product_name in DEFAULT_PROCESS_ROUTES:
        return DEFAULT_PROCESS_ROUTES[product_name]

    # بحث جزئي
    for key, route in DEFAULT_PROCESS_ROUTES.items():
        if key.lower() in product_name.lower() or product_name.lower() in key.lower():
            return route

    return []
