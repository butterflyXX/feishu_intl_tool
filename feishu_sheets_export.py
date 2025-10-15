#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import sys
import requests
from typing import List


# 需要到飞书后台创建一个应用, 获取APP_ID和APP_SECRET,自己上网搜吧
APP_ID = ""
APP_SECRET = ""

# 这个就是多语言表格链接中的内容, https://XXX.feishu.cn/sheets/{SPREADSHEET_TOKEN}?sheet={SHEET_ID}
SPREADSHEET_TOKEN = ""
SHEET_ID = ""

# 要拉取的范围,比如从第一列到第六列,就是A1:F(这个自己尝试吧)
RANGE = "A1:F"

OUT_CSV = "language.csv"


TENANT_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
# Sheets 批量读取值
SHEETS_VALUES_GET_V2 = (
    "https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{token}/values/{range}"
)


def get_tenant_access_token() -> str:
    resp = requests.post(
        TENANT_TOKEN_URL,
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"获取tenant_access_token失败: {data}")
    return data["tenant_access_token"]


def fetch_sheet_values(token: str) -> List[List[str]]:
    headers = {"Authorization": f"Bearer {token}"}
    all_rows: List[List[str]] = []

    rng = f"{SHEET_ID}!{RANGE}"
    url = SHEETS_VALUES_GET_V2.format(token=SPREADSHEET_TOKEN, range=rng)
    resp = requests.get(url, headers=headers, params={"valueRenderOption": "ToString"}, timeout=25)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"读取表格失败({rng}): {data}")

    value_range = (data.get("data") or {}).get("valueRange") or {}
    values = value_range.get("values") or []
    for row in values:
        all_rows.append(["" if v is None else str(v) for v in row])

    return all_rows


def write_csv(rows: List[List[str]]) -> None:
    def is_empty_row(r: List[str]) -> bool:
        return all((c or "").strip() == "" for c in r)

    trimmed: List[List[str]] = []
    for r in rows:
        trimmed.append(r)
    while trimmed and is_empty_row(trimmed[-1]):
        trimmed.pop()

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for r in trimmed:
            writer.writerow(r)


def main():
    if not APP_ID or not APP_SECRET:
        print("❌ 请在脚本顶部填写 APP_ID / APP_SECRET 后再运行。")
        sys.exit(1)

    try:
        print("获取tenant_access_token...")
        tenant_token = get_tenant_access_token()

        print("读取Sheets数据...")
        rows = fetch_sheet_values(tenant_token)
        if not rows:
            print("⚠️ 读取到空数据，检查表是否有内容/权限是否正确")

        write_csv(rows)
        print(f"✅ 导出完成: {OUT_CSV}")
    except Exception as e:
        print(f"❌ 出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()