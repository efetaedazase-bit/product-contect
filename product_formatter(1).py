"""
product_formatter.py
---------------------
اسکریپتی برای خواندن فایل اکسل محصولات (فرمت داخلی فروشگاه) و تبدیل آن
به فرمت مورد نیاز برای آپلود گروهی (bulk upload) در یک مارکت‌پلیس هدف.

هدف: وقتی محتوای یک محصول در یک کانال فروش آماده است، به‌جای بازنویسی
دستی برای هر مارکت‌پلیس، این اسکریپت به‌صورت خودکار محصولات را با رعایت
محدودیت‌های هر پلتفرم (طول عنوان، طول توضیحات، نگاشت دسته‌بندی، وضعیت
موجودی و واحد قیمت) آماده می‌کند.

استفاده:
    python product_formatter.py --input sample_products.xlsx --marketplace basalam --output output_basalam.csv

نویسنده: نمونه‌کار فریلنسری (Portfolio Sample)
"""

import argparse
import sys
import pandas as pd


# ----------------------------------------------------------------------
# تنظیمات مخصوص هر مارکت‌پلیس
# در پروژه واقعی، این بخش می‌تواند بر اساس مستندات رسمی هر پلتفرم تکمیل شود.
# ----------------------------------------------------------------------
MARKETPLACE_RULES = {
    "basalam": {
        "title_max_len": 60,
        "description_max_len": 300,
        "price_unit": "toman",  # باسلام قیمت را به تومان می‌پذیرد
        "category_map": {
            "مراقبت پوست": "skincare",
            "مراقبت مو": "haircare",
            "آرایشی لب": "lip-makeup",
        },
    },
    "digikala": {
        "title_max_len": 80,
        "description_max_len": 500,
        "price_unit": "rial",  # دیجی‌کالا قیمت را به ریال می‌پذیرد
        "category_map": {
            "مراقبت پوست": "skin-care",
            "مراقبت مو": "hair-care",
            "آرایشی لب": "lip-cosmetics",
        },
    },
}

REQUIRED_INPUT_COLUMNS = [
    "product_id",
    "product_name",
    "brand",
    "price_toman",
    "stock",
    "short_description",
    "category",
    "image_url",
]


def load_products(input_path: str) -> pd.DataFrame:
    """خواندن فایل اکسل ورودی و بررسی وجود ستون‌های ضروری."""
    try:
        df = pd.read_excel(input_path)
    except FileNotFoundError:
        sys.exit(f"خطا: فایل ورودی پیدا نشد -> {input_path}")
    except Exception as e:
        sys.exit(f"خطا در خواندن فایل اکسل: {e}")

    missing = [col for col in REQUIRED_INPUT_COLUMNS if col not in df.columns]
    if missing:
        sys.exit(f"خطا: ستون‌های ضروری در فایل ورودی وجود ندارند: {missing}")

    return df


def truncate_text(text: str, max_len: int) -> str:
    """کوتاه کردن متن در صورت عبور از محدودیت طول، با افزودن '…' در انتها."""
    if not isinstance(text, str):
        return text
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def convert_price(price_toman: float, price_unit: str) -> int:
    """تبدیل قیمت بر اساس واحد مورد نیاز مارکت‌پلیس هدف."""
    if price_unit == "rial":
        return int(price_toman) * 10
    return int(price_toman)


def map_category(category: str, category_map: dict) -> str:
    """نگاشت دسته‌بندی داخلی فروشگاه به کد دسته‌بندی مارکت‌پلیس هدف."""
    return category_map.get(category, "uncategorized")


def transform_row(row: pd.Series, rules: dict) -> dict:
    """تبدیل یک ردیف محصول (فرمت داخلی) به فرمت خروجی مارکت‌پلیس هدف."""
    return {
        "sku": row["product_id"],
        "title": truncate_text(f'{row["brand"]} - {row["product_name"]}', rules["title_max_len"]),
        "description": truncate_text(row["short_description"], rules["description_max_len"]),
        "price": convert_price(row["price_toman"], rules["price_unit"]),
        "availability": "موجود" if row["stock"] and row["stock"] > 0 else "ناموجود",
        "category_code": map_category(row["category"], rules["category_map"]),
        "image_url": row["image_url"],
    }


def convert_products(df: pd.DataFrame, marketplace: str) -> pd.DataFrame:
    """اجرای تبدیل روی کل دیتافریم محصولات برای یک مارکت‌پلیس مشخص."""
    if marketplace not in MARKETPLACE_RULES:
        sys.exit(
            f"خطا: مارکت‌پلیس '{marketplace}' پشتیبانی نمی‌شود. "
            f"گزینه‌های موجود: {list(MARKETPLACE_RULES.keys())}"
        )

    rules = MARKETPLACE_RULES[marketplace]
    rows = [transform_row(row, rules) for _, row in df.iterrows()]
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(
        description="تبدیل فایل اکسل محصولات به فرمت آپلود گروهی مارکت‌پلیس هدف"
    )
    parser.add_argument("--input", required=True, help="مسیر فایل اکسل ورودی محصولات")
    parser.add_argument(
        "--marketplace",
        required=True,
        choices=list(MARKETPLACE_RULES.keys()),
        help="مارکت‌پلیس هدف برای تولید فایل خروجی",
    )
    parser.add_argument("--output", required=True, help="مسیر فایل CSV خروجی")

    args = parser.parse_args()

    df = load_products(args.input)
    result_df = convert_products(df, args.marketplace)
    result_df.to_csv(args.output, index=False, encoding="utf-8-sig")

    print(f"✅ {len(result_df)} محصول با موفقیت برای '{args.marketplace}' آماده و در '{args.output}' ذخیره شد.")


if __name__ == "__main__":
    main()
