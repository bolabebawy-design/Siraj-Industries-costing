# Siraj Industries - نظام حساب تكاليف المنتجات

نظام بايثون لحساب تكلفة تصنيع منتجات الإضاءة في **مصانع سراج**.

---

## تشغيل سريع على جهازك

```bash
pip install -r requirements.txt
streamlit run app.py
```

يفتح المتصفح على: **http://localhost:8501**

---

## نشر على Streamlit Cloud (لينك دائم مجاني)

### الخطوة 1: اعمل حسابات (لو مش عندك)

1. حساب **GitHub**: https://github.com/signup
2. حساب **Streamlit Community Cloud**: https://share.streamlit.io  
   (ادخل بنفس حساب GitHub)

---

### الخطوة 2: ارفع المشروع على GitHub

#### طريقة سهلة (من الموقع):

1. ادخل على https://github.com/new
2. Repository name: `siraj-costing` (أو أي اسم)
3. خليه **Public**
4. دوس **Create repository**

5. بعد ما يتفتح الصفحة، دوس على **"uploading an existing file"**
6. اسحب كل محتويات فولدر المشروع (app.py + config.py + core + loaders + data + requirements.txt + README.md ...)
7. اكتب رسالة زي: `Initial commit - Siraj Costing System`
8. دوس **Commit changes**

#### أو من جهازك (لو عندك Git):

```bash
cd siraj_costing
git init
git add .
git commit -m "Initial commit - Siraj Costing System"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/siraj-costing.git
git push -u origin main
```

---

### الخطوة 3: ربط المشروع بـ Streamlit Cloud

1. ادخل على: https://share.streamlit.io
2. دوس **New app**
3. اختار:
   - **Repository**: `YOUR_USERNAME/siraj-costing`
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. دوس **Deploy**

هياخد دقيقة أو اتنين وبعدين هيديك لينك دائم شكله كده:

```
https://siraj-costing-xxxxx.streamlit.app
```

هذا اللينك يشتغل من أي مكان ومن أي جهاز بدون تثبيت.

---

### ملاحظات مهمة عند النشر

| النقطة | التفاصيل |
|--------|----------|
| الملفات الكبيرة | ملف المنتجات (~1MB) مقبول في Streamlit Cloud |
| التحديثات | أي تعديل تعمله على GitHub هيتحدث تلقائي بعد دقايق |
| الإعدادات | تقدر تغير سعر الدولار والـ Overhead من داخل الواجهة |
| الخصوصية | اللينك عام. لو عايز تخفيه، استخدم Password من إعدادات Streamlit |

---

## محتويات المشروع

```
siraj_costing/
├── app.py                  ← واجهة الويب (الملف الرئيسي)
├── main.py                 ← نسخة Terminal
├── config.py
├── requirements.txt
├── core/
│   ├── models.py
│   └── cost_calculator.py
├── loaders/
│   ├── machine_loader.py
│   └── product_loader.py
├── data/
│   ├── Flare Products Costing Sheet -.xlsx
│   └── Machines cost-hour-1.xlsx
└── README.md
```

---

## الإعدادات القابلة للتعديل

من ملف `config.py` أو من الشريط الجانبي في الواجهة:

- سعر الدولار
- نسبة الـ Overhead
- هامش الربح المقترح

---

## الدعم

لو واجهت أي مشكلة أثناء الرفع، ابعتلي:
- رسالة الخطأ
- صورة من الشاشة

وأقولك الحل فورًا.
