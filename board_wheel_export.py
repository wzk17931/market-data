"""
批量抓取东方财富“板块轮动”数据（tab3=1 前10后10），按日期分行，输出到 Excel。

特性：
- tab1=0（行业）、tab1=1（概念）分别写入两个 sheet。
- tab2=0/1/2/3/4 五个维度一起记录，并带上前10/后10标记。
- 直接调 datacenter 接口，不依赖 Selenium。
"""

import os
from datetime import datetime
from typing import Dict, List

import pandas as pd
import requests
from requests.adapters import HTTPAdapter, Retry


API_URL = "https://datacenter.eastmoney.com/securities/api/data/v1/get"

# tab1 映射：0=行业，1=概念（COMMON_TYPE2 分别为 2、3）
TAB1_MAP: Dict[int, str] = {0: "行业", 1: "概念"}
COMMON_TYPE2_MAP: Dict[int, str] = {0: "2", 1: "3"}

# tab2 映射到 COMMON_TYPE1 以及维度名称
TAB2_MAP: Dict[int, Dict[str, str]] = {
    0: {"common_type1": "001", "name": "涨幅"},
    1: {"common_type1": "004", "name": "涨停家数"},
    2: {"common_type1": "005", "name": "涨跌比"},
    3: {"common_type1": "003", "name": "主力净流入"},
    4: {"common_type1": "002", "name": "成交额"},
}


def _session_with_retry() -> requests.Session:
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_tab(tab1: int, tab2: int, page_size: int = 500) -> List[Dict]:
    """
    拉取某个 tab1/tab2 的全部分页数据。
    返回的字段只保留下游需要的键，以便直接写表。
    """
    sess = _session_with_retry()
    common_type1 = TAB2_MAP[tab2]["common_type1"]
    common_type2 = COMMON_TYPE2_MAP[tab1]
    tab1_name = TAB1_MAP[tab1]
    tab2_name = TAB2_MAP[tab2]["name"]

    rows: List[Dict] = []
    page_number = 1
    while True:
        params = {
            "reportName": "RPT_BOARD_WHEEL",
            "columns": "BOARD_CODE,BOARD_NAME,TRADE_DATE,INDICATORID,INDICATORID_RANK,COMMON_TYPE3",
            "filter": f'(COMMON_TYPE1="{common_type1}")(COMMON_TYPE2="{common_type2}")(INDICATORID_RANK<=10)',
            "source": "SECURITIES",
            "client": "APP",
            "sortColumns": "TRADE_DATE,INDICATORID_RANK",
            "sortTypes": "1,1",
            "pageNumber": page_number,
            "pageSize": page_size,
        }
        resp = sess.get(API_URL, params=params, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        result = payload.get("result") or {}
        data = result.get("data") or []

        for item in data:
            t3 = item.get("COMMON_TYPE3")
            direction = "前10" if t3 == "01" else "后10" if t3 == "02" else t3
            rows.append(
                {
                    "日期": item["TRADE_DATE"][:10],
                    "分类方式": tab1_name,
                    "维度": tab2_name,
                    "排名方向": direction,
                    "排名": item["INDICATORID_RANK"],
                    "指标值": item["INDICATORID"],
                    "板块名称": item["BOARD_NAME"],
                    "板块代码": item["BOARD_CODE"],
                }
            )

        pages = result.get("pages") or 1
        if page_number >= pages or not data:
            break
        page_number += 1

    return rows


def export_excel(all_rows: List[Dict], output_dir: str = "过往数据") -> str:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"板块轮动_tab3_1_{timestamp}.xlsx")

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for tab1_value, tab1_name in TAB1_MAP.items():
            sheet_rows = [r for r in all_rows if r["分类方式"] == tab1_name]
            if not sheet_rows:
                continue
            df = pd.DataFrame(sheet_rows)
            df = df.sort_values(
                ["日期", "维度", "排名方向", "排名"],
                ascending=[False, True, True, True],
            )
            df.to_excel(writer, sheet_name=tab1_name, index=False)

    return output_path


def main() -> None:
    all_rows: List[Dict] = []
    for tab1 in TAB1_MAP:
        for tab2 in TAB2_MAP:
            print(f"拉取 tab1={tab1}({TAB1_MAP[tab1]}), tab2={tab2}({TAB2_MAP[tab2]['name']}) ...")
            rows = fetch_tab(tab1, tab2)
            print(f"  获取 {len(rows)} 行")
            all_rows.extend(rows)

    output_path = export_excel(all_rows)
    print(f"已导出：{output_path}")


if __name__ == "__main__":
    main()
