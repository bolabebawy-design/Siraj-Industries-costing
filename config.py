"""
Siraj Industries - Costing System Configuration
إعدادات نظام التكاليف - مصانع سراج
"""

from pathlib import Path

# ======================
# Paths
# ======================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

PRODUCTS_FILE = DATA_DIR / "Flare Products Costing Sheet -.xlsx"
MACHINES_FILE = DATA_DIR / "Machines cost-hour-1.xlsx"

# ======================
# Currency & Rates
# ======================
EXCHANGE_RATE_USD = 56.0          # سعر الدولار الحالي
EXCHANGE_RATE_EUR = 61.0          # سعر اليورو التقريبي (عدل حسب الحاجة)

# من ملف Rates
WORKING_DAYS_PER_YEAR = 280
WORKING_DAYS_PER_MONTH = 24
HOURS_PER_SHIFT = 8
SHIFTS_PER_DAY = 1

# ======================
# Costing Assumptions
# ======================
DEFAULT_OVERHEAD_PERCENTAGE = 0.12      # 12% overhead
DEFAULT_PROFIT_MARGIN = 0.25            # 25% هامش ربح مقترح
DEFAULT_WASTE_PERCENTAGE = 0.03         # 3% هالك مواد

# ======================
# Machine Name Mapping (اختياري للتوحيد)
# ======================
MACHINE_ALIASES = {
    "LASER CUTTING MACHINE": "LASER CUTTING MACHINE",
    "CNC PRESS BRAKE": "CNC PRESS BRAKE",
    "HYDRAULIC SHEARING MACHINE": "HYDRAULIC SHEARING MACHINE",
    "CNC Router Machine": "CNC Router Machine",
    "Paint shop": "Paint shop",
    "line A": "line A",
    "line B": "line B",
    "Smt Line": "Smt Line",
    "AUTO WELDING MACHINE+N2 gen.": "AUTO WELDING MACHINE+N2 gen.",
    "HANDHELD WELDING MACHINE+N2 gen.": "HANDHELD WELDING MACHINE+N2 gen.",
}

# ======================
# Display
# ======================
CURRENCY_SYMBOL = "ج.م"
COMPANY_NAME = "Siraj Industries"
COMPANY_NAME_AR = "مصانع سراج"
