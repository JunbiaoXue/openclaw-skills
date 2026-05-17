import urllib.request
import json
import csv
import time

# 从中彩网抓取双色球历史数据
def fetch_ssq_data(page=1, page_size=100):
    url = f"https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=ssq&issueCount=&issueStart=&issueEnd=&dayStart=&dayEnd=&pageNo={page}&pageSize={page_size}&week=&systemType=PC"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.cwl.gov.cn/',
        'Accept': 'application/json'
    }
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data
    except Exception as e:
        print(f"Error fetching page {page}: {e}")
        return None

# 获取总页数
print("正在获取数据总页数...")
first_page = fetch_ssq_data(page=1, page_size=100)
if first_page and 'result' in first_page:
    total = first_page.get('count', 0)
    print(f"总记录数: {total}")
    
    # 抓取所有数据
    all_data = []
    pages = (total // 100) + 1
    
    for page in range(1, pages + 1):
        print(f"正在抓取第 {page}/{pages} 页...")
        data = fetch_ssq_data(page=page, page_size=100)
        if data and 'result' in data:
            all_data.extend(data['result'])
        time.sleep(0.5)  # 避免请求过快
    
    # 保存为CSV
    with open('ssq_history.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['期号', '日期', '红球1', '红球2', '红球3', '红球4', '红球5', '红球6', '蓝球'])
        
        for item in all_data:
            code = item.get('code', '')
            date = item.get('date', '')
            red = item.get('red', '').split(',')
            blue = item.get('blue', '')
            
            if len(red) == 6:
                writer.writerow([code, date] + red + [blue])
    
    print(f"\n✅ 数据已保存到 ssq_history.csv，共 {len(all_data)} 条记录")
else:
    print("❌ 数据获取失败")
