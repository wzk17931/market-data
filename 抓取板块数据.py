# coding: utf-8
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import pandas as pd
from datetime import datetime
import os

timestamp = datetime.now().strftime("%m-%d_%H-%M-%S")


# 目标页面 URL，请确保此 URL 可访问
# url = "https://emdata.eastmoney.com/appdc/bkld/index.html?tab1=0&tab2=4&tab3=1"# tab2=3 代表主力资金流入，tab2=4 代表成交额
user_id = 0 #0 代表涨幅，3 代表主力资金流入，4 代表成交额，记得手动改写！！！



if user_id == 0:
    type = "涨幅" # 主力资金净流入or成交额
    url = "https://emdata.eastmoney.com/appdc/bkld/index.html?tab1=0&tab2=0&tab3=1"
elif user_id == 3:
    type = "主力资金流入" # 主力资金净流入or成交额
    url = "https://emdata.eastmoney.com/appdc/bkld/index.html?tab1=0&tab2=3&tab3=1"
elif user_id == 4:
    type = "成交额"
    url = "https://emdata.eastmoney.com/appdc/bkld/index.html?tab1=0&tab2=4&tab3=1"
#output = f"{type}_{timestamp}.csv" 
output = os.path.join("过往数据", f"{type}_{timestamp}行情.csv")

def scrape_funds():
    # 1) 配置 Selenium 无头模式
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    
    # 2) 启动浏览器
    driver = webdriver.Chrome(options=chrome_options)
    
    # 3) 访问目标网页
    driver.get(url)
    
    # 4) 显式等待，确保至少有一个 <div class="column"> 出现
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.column")))
    
    # 额外等待几秒钟，确保动态内容加载完成
    time.sleep(10)
    
    # 5) 找到所有位于 class="column" 下的 <div class="tablecell"> 元素
    tablecells = driver.find_elements(By.CSS_SELECTOR, "div.column .tablecell")
    
    results = []
    for cell in tablecells:
        try:
            # 尝试提取 code 属性、板块名称和资金流动金额
            code_attr = cell.get_attribute("code")
            block_name = cell.find_element(By.CSS_SELECTOR, "div.name").text.strip()
            flow_amount = cell.find_element(By.CSS_SELECTOR, "div.content > div").text.strip()
            
            results.append((code_attr, block_name, flow_amount))
        except NoSuchElementException:
            print("跳过一个不符合预期结构的 tablecell")
    
    # 6) 仅快速打印前五个结果用于验证
    print("前五个提取结果：")
    for item in results[:5]:
        print(item)
    
    # 7) 将所有结果保存到 CSV 表格中
    df = pd.DataFrame(results, columns=["code", "板块", "资金流动"])
    df.to_csv(output, index=False, encoding="utf-8-sig")
    print(f"结果已保存到{output}")
    
    # 8) 关闭浏览器
    driver.quit()
    return results

if __name__ == "__main__":
    data = scrape_funds()
