"""
Siraj Industries - نظام حساب تكاليف المنتجات
واجهة ويب جاهزة باستخدام Streamlit
"""

import streamlit as st
import sys
from pathlib import Path

# إضافة المسار
sys.path.insert(0, str(Path(__file__).parent))

import config
from loaders.machine_loader import load_machines
from loaders.product_loader import (
    list_available_products,
    load_product_from_sheet,
    get_default_route,
)
from core.cost_calculator import CostCalculator
from core.models import ProcessStep

# ======================
# إعداد الصفحة
# ======================
st.set_page_config(
    page_title="Siraj Costing System",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ======================
# تحميل البيانات (Cache)
# ======================
@st.cache_data(show_spinner="جاري تحميل بيانات الماكينات...")
def get_machines():
    return load_machines()


@st.cache_data(show_spinner="جاري تحميل قائمة المنتجات...")
def get_products_list():
    return list_available_products()


# ======================
# الواجهة
# ======================
def main():
    # العنوان
    st.markdown(
        f"""
        <div style="text-align:center; padding: 10px 0 20px 0;">
            <h1 style="color:#1E3A5F; margin-bottom:0;">💡 {config.COMPANY_NAME}</h1>
            <h3 style="color:#4A6FA5; margin-top:5px;">{config.COMPANY_NAME_AR}</h3>
            <p style="color:#666;">نظام حساب تكاليف منتجات الإضاءة</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # الشريط الجانبي
    with st.sidebar:
        st.header("⚙️ الإعدادات")

        usd_rate = st.number_input(
            "سعر الدولار (ج.م)",
            min_value=1.0,
            max_value=200.0,
            value=float(config.EXCHANGE_RATE_USD),
            step=0.5,
        )
        overhead_pct = st.slider(
            "نسبة الـ Overhead (%)",
            min_value=0,
            max_value=50,
            value=int(config.DEFAULT_OVERHEAD_PERCENTAGE * 100),
        )
        profit_margin = st.slider(
            "هامش الربح المقترح (%)",
            min_value=0,
            max_value=100,
            value=int(config.DEFAULT_PROFIT_MARGIN * 100),
        )

        st.divider()
        st.caption("الإصدار 1.0 | Siraj Industries")

    # تحميل البيانات
    try:
        machines = get_machines()
        products = get_products_list()
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {e}")
        st.info(f"تأكد من وجود الملفات في مجلد: `{config.DATA_DIR}`")
        return

    # اختيار المنتج
    st.subheader("📦 اختر المنتج")
    col1, col2 = st.columns([3, 1])

    with col1:
        selected_product = st.selectbox(
            "المنتج",
            options=products,
            index=0,
            label_visibility="collapsed",
        )

    with col2:
        calculate_btn = st.button("احسب التكلفة", type="primary", use_container_width=True)

    # عرض معلومات سريعة
    st.caption(f"عدد المنتجات المتاحة: **{len(products)}** | عدد الماكينات: **{len(machines)}**")

    if calculate_btn or "last_result" in st.session_state:
        if calculate_btn:
            with st.spinner("جاري حساب التكلفة..."):
                route = get_default_route(selected_product)
                product = load_product_from_sheet(selected_product, process_route=route)

                calculator = CostCalculator(
                    machines=machines,
                    exchange_rate_usd=usd_rate,
                    overhead_pct=overhead_pct / 100,
                    profit_margin=profit_margin / 100,
                )
                result = calculator.calculate_full_cost(product)
                st.session_state["last_result"] = result
                st.session_state["last_product"] = product
                st.session_state["last_route"] = route

        result = st.session_state.get("last_result")
        product = st.session_state.get("last_product")
        route = st.session_state.get("last_route", [])

        if result:
            # ===== النتائج الرئيسية =====
            st.divider()
            st.subheader(f"نتائج التكلفة: {result.product_name}")

            # كروت الملخص
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("إجمالي التكلفة", f"{result.total_cost_egp:,.0f} ج.م")
            m2.metric("سعر البيع المقترح", f"{result.suggested_price_egp:,.0f} ج.م")
            m3.metric("تكلفة المواد", f"{result.material_total_egp:,.0f} ج.م")
            m4.metric("تكلفة التشغيل", f"{result.process_machine_egp:,.0f} ج.م")

            # تفاصيل أكثر
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 ملخص التكاليف",
                "🔧 تفاصيل التشغيل",
                "📋 المواد (BOM)",
                "⚠️ ملاحظات",
            ])

            with tab1:
                import pandas as pd

                summary_data = {
                    "البند": [
                        "مواد محلية",
                        "مواد مستوردة",
                        "إجمالي المواد",
                        "تكلفة الماكينات",
                        "تكلفة العمالة",
                        "التعبئة",
                        "الـ Overhead",
                        "الإجمالي النهائي",
                    ],
                    "القيمة (ج.م)": [
                        result.material_local_egp,
                        result.material_imported_egp,
                        result.material_total_egp,
                        result.process_machine_egp,
                        result.process_labor_egp,
                        result.packing_egp,
                        result.overhead_egp,
                        result.total_cost_egp,
                    ],
                }
                df_summary = pd.DataFrame(summary_data)
                df_summary["القيمة (ج.م)"] = df_summary["القيمة (ج.م)"].apply(
                    lambda x: f"{x:,.2f}"
                )
                st.dataframe(df_summary, use_container_width=True, hide_index=True)

                # نسبة المساهمة
                st.markdown("#### توزيع التكلفة")
                total = result.total_cost_egp or 1
                chart_data = pd.DataFrame({
                    "البند": ["مواد", "تشغيل ماكينات", "تعبئة", "Overhead"],
                    "النسبة": [
                        result.material_total_egp / total * 100,
                        result.process_machine_egp / total * 100,
                        result.packing_egp / total * 100,
                        result.overhead_egp / total * 100,
                    ],
                })
                st.bar_chart(chart_data.set_index("البند"))

            with tab2:
                if result.breakdown.get("process_details"):
                    process_rows = []
                    for step in result.breakdown["process_details"]:
                        process_rows.append({
                            "الماكينة": step["machine"],
                            "المحطة": step.get("station", ""),
                            "الوقت (دقيقة)": step["minutes"],
                            "تكلفة الساعة (ج.م)": f"{step['cost_per_hour']:,.2f}",
                            "التكلفة (ج.م)": f"{step['machine_cost']:,.2f}",
                        })
                    st.dataframe(
                        pd.DataFrame(process_rows),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.warning(
                        "لا يوجد مسار تصنيع مسجل لهذا المنتج.\n"
                        "أضف الأوقات في `loaders/product_loader.py` → `DEFAULT_PROCESS_ROUTES`"
                    )

                # عرض المسار الحالي
                if route:
                    st.markdown("**مسار التصنيع المستخدم:**")
                    for i, step in enumerate(route, 1):
                        st.write(f"{i}. {step.machine_name} — {step.time_minutes} دقيقة")

            with tab3:
                if result.breakdown.get("materials_details"):
                    mat_rows = []
                    for item in result.breakdown["materials_details"]:
                        mat_rows.append({
                            "التصنيف": item["category"],
                            "الصنف": item["selection"],
                            "الكمية": item["qty"],
                            "سعر الوحدة": item["unit_price"],
                            "العملة": item["currency"],
                            "محلي؟": "نعم" if item["is_local"] else "لا",
                            "التكلفة (ج.م)": f"{item['total_egp']:,.2f}",
                        })
                    st.dataframe(
                        pd.DataFrame(mat_rows),
                        use_container_width=True,
                        hide_index=True,
                    )
                    st.caption(f"عدد الأصناف: {len(mat_rows)}")
                else:
                    st.info("لا توجد تفاصيل مواد.")

            with tab4:
                if result.warnings:
                    for w in result.warnings:
                        st.warning(w)
                else:
                    st.success("لا توجد تحذيرات.")

                st.markdown("---")
                st.markdown(
                    """
                    **ملاحظات هامة:**
                    - تكلفة المواد حالياً قد تشمل كل البدائل الموجودة في الشيت (High/Med/Low).
                    - دقة حساب التشغيل تعتمد على تعريف أوقات الماكينات في `DEFAULT_PROCESS_ROUTES`.
                    - يُفضل مراجعة الـ BOM يدوياً للتأكد من اختيار المكونات الصحيحة.
                    """
                )

    # تذييل
    st.divider()
    st.caption(
        f"سعر الصرف المستخدم: {usd_rate} ج.م | Overhead: {overhead_pct}% | "
        f"هامش الربح: {profit_margin}%"
    )


if __name__ == "__main__":
    main()
