from __future__ import annotations

import random
from pathlib import Path
import pandas as pd

from core import utils 


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path | str) -> pd.DataFrame:
    """Simulate nhiều dạng data corruption trên DataFrame.

    Pseudo-code:
    1. Drop mot so latest records.
    2. Blank summary o mot so dong.
    3. Inject noise vao text.
    4. Lam title bi truncate.
    5. Lam published date cu di.
    6. Add duplicate rows.
    7. Rebuild `text_for_embedding`.
    8. Ghi corruption log vao output_log_path.
    """
    # Tạo bản sao để không làm ảnh hưởng đến DataFrame gốc
    df_corrupted = df.copy()
    log = []
    
    # 1. Drop một số latest records (Dựa vào age_days, số càng nhỏ càng mới)
    if "age_days" in df_corrupted.columns:
        # Sắp xếp để đưa các bài mới nhất lên đầu
        df_corrupted = df_corrupted.sort_values(by="age_days")
        drop_count = max(1, int(len(df_corrupted) * 0.1)) # Xóa 10% dữ liệu mới nhất
        dropped_ids = df_corrupted.iloc[:drop_count]["paper_id"].tolist()
        
        df_corrupted = df_corrupted.iloc[drop_count:]
        log.append({"action": "drop_latest_records", "count": drop_count, "dropped_ids": dropped_ids})

    # 2. Blank summary ở một số dòng (10% số dòng ngẫu nhiên)
    blank_idx = df_corrupted.sample(frac=0.1, random_state=42).index
    df_corrupted.loc[blank_idx, "summary"] = ""
    log.append({"action": "blank_summary", "affected_ids": df_corrupted.loc[blank_idx, "paper_id"].tolist()})

    # 3. Inject noise vào text (Thêm chuỗi rác vào tóm tắt)
    noise_idx = df_corrupted.sample(frac=0.1, random_state=43).index
    df_corrupted.loc[noise_idx, "summary"] = df_corrupted.loc[noise_idx, "summary"].astype(str) + " [CORRUPTED_NOISE_!@#123]"
    log.append({"action": "inject_noise", "affected_ids": df_corrupted.loc[noise_idx, "paper_id"].tolist()})

    # 4. Làm title bị truncate (Cắt tiêu đề còn 15 ký tự)
    trunc_idx = df_corrupted.sample(frac=0.1, random_state=44).index
    df_corrupted.loc[trunc_idx, "title"] = df_corrupted.loc[trunc_idx, "title"].apply(lambda x: str(x)[:15] + "...")
    log.append({"action": "truncate_title", "affected_ids": df_corrupted.loc[trunc_idx, "paper_id"].tolist()})

    # 5. Làm published date cũ đi (Trừ đi 5 năm)
    old_date_idx = df_corrupted.sample(frac=0.1, random_state=45).index
    temp_dates = pd.to_datetime(df_corrupted.loc[old_date_idx, "published"], errors="coerce")
    # Trừ đi 5 năm (DateOffset) và format lại thành chuỗi YYYY-MM-DD
    df_corrupted.loc[old_date_idx, "published"] = (temp_dates - pd.DateOffset(years=5)).dt.strftime("%Y-%m-%d")
    if "age_days" in df_corrupted.columns:
        df_corrupted.loc[old_date_idx, "age_days"] += (5 * 365) # Cập nhật tuổi đời tương ứng
    log.append({"action": "age_published_date", "affected_ids": df_corrupted.loc[old_date_idx, "paper_id"].tolist()})

    # 6. Add duplicate rows (Lấy 3 dòng ngẫu nhiên và dán xuống cuối)
    dup_rows = df_corrupted.sample(n=min(3, len(df_corrupted)), random_state=46)
    df_corrupted = pd.concat([df_corrupted, dup_rows], ignore_index=True)
    log.append({"action": "add_duplicates", "count": len(dup_rows), "duplicated_ids": dup_rows["paper_id"].tolist()})

    # 7. Rebuild `text_for_embedding`
    # Ghép nối lại các trường thông tin sau khi chúng đã bị làm hỏng
    df_corrupted["text_for_embedding"] = (
        "Title: " + df_corrupted["title"].fillna("") + "\n" +
        "Authors: " + df_corrupted["authors_joined"].fillna("") + "\n" +
        "Published: " + df_corrupted["published"].astype(str).fillna("") + "\n" +
        "Categories: " + df_corrupted["categories_joined"].fillna("") + "\n" +
        "Summary: " + df_corrupted["summary"].fillna("")
    )
    
    # Cập nhật lại độ dài summary nếu có
    if "summary_chars" in df_corrupted.columns:
        df_corrupted["summary_chars"] = df_corrupted["summary"].fillna("").str.len()

    # 8. Ghi corruption log vào output_log_path
    # Sử dụng hàm utils.write_json để lưu trữ log dạng JSON một cách an toàn
    utils.write_json(Path(output_log_path), log)

    return df_corrupted