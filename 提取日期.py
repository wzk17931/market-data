# -*- coding: utf-8 -*-
"""
横向滚动抓取东方财富“板块流动”页面全部交易日期
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
from datetime import datetime
import os

timestamp = datetime.now().strftime("%m-%d_%H-%M-%S")


# 目标页面 url，请确保此 url 可访问
# url = "https://emdata.eastmoney.com/appdc/bkld/index.html?tab1=0&tab2=4&tab3=1"# tab2=3 代表主力资金流入，tab2=4 代表成交额
user_id = 0 #0 代表涨幅日期，3 代表主力资金流入日期，4 代表成交额日期，需要手动改！！！

if user_id == 0:
    type = "涨幅" # 主力资金净流入or成交额
    url = "https://emdata.eastmoney.com/appdc/bkld/index.html?tab1=0&tab2=0&tab3=1"
elif user_id == 3:
    type = "主力资金流入日期" # 主力资金净流入or成交额
    url = "https://emdata.eastmoney.com/appdc/bkld/index.html?tab1=0&tab2=3&tab3=1"
elif user_id == 4:
    type = "成交额日期"
    url = "https://emdata.eastmoney.com/appdc/bkld/index.html?tab1=0&tab2=4&tab3=1"
#output = f"{type}_{timestamp}.csv" 
output = os.path.join("过往数据", f"{type}_{timestamp}日期.csv")



"""
url = "https://emdata.eastmoney.com/appdc/bkld/index.html?tab1=0&tab2=4&tab3=1"# tab2=3 代表资金流入，tab2=4 代表成交额
output = "成交额日期.csv"# 记得更改文件名，资金净流入日期or成交额日期.csv
"""

def scrape_dates():
    # 1. 浏览器配置
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")   # 无界面渲染
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=3")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)

        # 2. 等待日期条出现
        wait = WebDriverWait(driver, 15)
        date_box = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "dateList"))
        )

        # 3. 横向无限滚动并收集唯一日期
        dates = set()
        prev_len, stable_rounds = 0, 0

        while True:
            # 3‑1 收集当前可见日期
            for cell in date_box.find_elements(By.CSS_SELECTOR, "div.tablecell"):
                txt = cell.text.strip()
                if txt and txt != "排名":
                    dates.add(txt)

            # 3‑2 判断是否已到最右侧
            right_gap = driver.execute_script(
                "return arguments[0].scrollWidth - arguments[0].scrollLeft - arguments[0].clientWidth;",
                date_box
            )
            if right_gap <= 0:
                stable_rounds += 1
            else:
                stable_rounds = 0

            # 3‑3 连续两轮无新增日期且已到末尾 → 结束
            if len(dates) == prev_len and stable_rounds >= 2:
                break
            prev_len = len(dates)

            # 3‑4 横向滚动一个视口宽度
            driver.execute_script(
                "arguments[0].scrollLeft += arguments[0].clientWidth;", date_box
            )
            time.sleep(0.5)   # 让懒加载完成

        # 4. 写 CSV（日期倒序）
        with open(output, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["日期"])
            for d in sorted(dates, reverse=True):
                writer.writerow([d])

        print(f"成功提取 {len(dates)} 条日期，已保存至 {output}")
        return dates

    finally:
        driver.quit()


if __name__ == "__main__":
    scrape_dates()
