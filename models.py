"""
Data Models for Siraj Costing System
نماذج البيانات لنظام التكاليف
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class Currency(Enum):
    EGP = "EGP"
    USD = "USD"
    EUR = "EUR"


class CostLevel(Enum):
    HIGH = "High"
    MED = "Med"
    LOW = "Low"


@dataclass
class MaterialItem:
    """عنصر في قائمة المواد (BOM)"""
    category: str                       # Body, LGP, Diffuser, Driver...
    selection: str                      # اسم الصنف أو الكود
    unit: str                           # Pcs, KG, Meter...
    qty: float
    unit_price: float
    currency: str = "USD"
    is_local: bool = False
    freight: float = 0.0
    duties: float = 0.0
    notes: str = ""

    @property
    def line_total_currency(self) -> float:
        """التكلفة بالعملة الأصلية (قبل التحويل)"""
        return (self.qty * self.unit_price) + self.freight + self.duties

    def total_egp(self, usd_rate: float = 56.0, eur_rate: float = 61.0) -> float:
        """التكلفة بالجنيه المصري"""
        total = self.line_total_currency
        curr = self.currency.upper()
        if curr in ("USD", "US$", "$"):
            return total * usd_rate
        elif curr in ("EUR", "EURO", "€"):
            return total * eur_rate
        else:
            # افترض أنها بالفعل بالجنيه
            return total


@dataclass
class ProcessStep:
    """خطوة تصنيع (تشغيل على ماكينة)"""
    machine_name: str
    time_minutes: float
    operators: int = 1
    notes: str = ""

    @property
    def time_hours(self) -> float:
        return self.time_minutes / 60.0


@dataclass
class Product:
    """منتج كامل"""
    name: str
    materials: List[MaterialItem] = field(default_factory=list)
    process_route: List[ProcessStep] = field(default_factory=list)
    packing_cost_egp: float = 0.0
    category: str = ""                  # مثلاً: Panel, Downlight, Linear...
    ip_rating: str = ""
    power_watt: Optional[float] = None
    control_type: str = ""              # On-Off, Dali, Phase Cut, 0-10V
    notes: str = ""

    def get_material_summary(self) -> Dict[str, float]:
        """ملخص سريع لعدد الأصناف حسب التصنيف"""
        summary = {}
        for item in self.materials:
            summary[item.category] = summary.get(item.category, 0) + 1
        return summary


@dataclass
class Machine:
    """ماكينة أو خط إنتاج"""
    name: str
    station: str                        # Welding, Machining, Paint shop, Assembly...
    cost_per_hour_egp: float
    cost_per_day_egp: float = 0.0
    depreciation_per_day: float = 0.0
    energy_per_day: float = 0.0
    utilities_per_day: float = 0.0
    manuf_consumables_per_day: float = 0.0
    maint_consumables_per_day: float = 0.0
    manpower_per_day: float = 0.0
    price_egp: float = 0.0
    depreciation_class: str = ""        # A, B, C
    notes: str = ""


@dataclass
class CostResult:
    """نتيجة حساب التكلفة لمنتج"""
    product_name: str
    material_local_egp: float = 0.0
    material_imported_egp: float = 0.0
    material_total_egp: float = 0.0
    process_machine_egp: float = 0.0
    process_labor_egp: float = 0.0
    packing_egp: float = 0.0
    overhead_egp: float = 0.0
    total_cost_egp: float = 0.0
    suggested_price_egp: float = 0.0
    breakdown: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "product": self.product_name,
            "materials": {
                "local": round(self.material_local_egp, 2),
                "imported": round(self.material_imported_egp, 2),
                "total": round(self.material_total_egp, 2),
            },
            "process": {
                "machine": round(self.process_machine_egp, 2),
                "labor": round(self.process_labor_egp, 2),
            },
            "packing": round(self.packing_egp, 2),
            "overhead": round(self.overhead_egp, 2),
            "total_cost_egp": round(self.total_cost_egp, 2),
            "suggested_selling_price": round(self.suggested_price_egp, 2),
            "warnings": self.warnings,
        }
