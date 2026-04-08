# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "beautifulsoup4",
#     "requests",
# ]
# ///
import requests
from bs4 import BeautifulSoup
import time
import os

def send_telegram_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Telegram 傳送失敗: {e}")

def crawl_ptt(keyword, pages=5):
    base_url = "https://www.ptt.cc"
    url = base_url + "/bbs/drama-ticket/index.html"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }

    results = []
    
    for _ in range(pages):
        try:
            res = requests.get(url, headers=headers)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"連線錯誤: {e}")
            break
            
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 解析各篇文章
        articles = soup.find_all('div', class_='r-ent')
        
        for article in articles:
            title_div = article.find('div', class_='title')
            # 排除已刪除的文章
            if title_div and title_div.a:
                title = title_div.a.text
                article_url = base_url + title_div.a['href']
                date = article.find('div', class_='date').text.strip()
                author = article.find('div', class_='author').text
                
                # 若包含關鍵字，加入結果
                if keyword in title:
                    results.append({
                        'title': title,
                        'url': article_url,
                        'date': date,
                        'author': author
                    })
        
        # 尋找「上一頁」的連結
        paging = soup.find('div', class_='btn-group btn-group-paging')
        if paging:
            prev_link = paging.find_all('a')[1]
            if 'href' in prev_link.attrs:
                url = base_url + prev_link['href']
            else:
                break # 已經是最前面了
        else:
            break
            
        # 避免請求過於頻繁阻擋爬蟲，稍微暫停
        time.sleep(0.5)
        
    return results

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PTT Drama-Ticket 票券爬蟲")
    parser.add_argument("-k", "--keyword", type=str, help="想搜尋的演唱會/票券關鍵字", default=None)
    parser.add_argument("-p", "--pages", type=int, default=5, help="預計搜尋頁數")
    args = parser.parse_args()

    if args.keyword:
        keyword = args.keyword
        pages = args.pages
    else:
        print("==== PTT Drama-Ticket 票券爬蟲 ====")
        keyword = input("請輸入你想搜尋的演唱會/票券關鍵字: ")
        page_input = input("請輸入預計搜尋頁數 (按 Enter 預設搜尋近期 5 頁): ")
        
        if page_input.isdigit():
            pages = int(page_input)
        else:
            pages = 5
        
    print(f"\n正在尋找關鍵字「{keyword}」的票券中...\n")
    found_tickets = crawl_ptt(keyword, pages)
    
    tg_token = os.environ.get("TG_BOT_TOKEN")
    tg_chat_id = os.environ.get("TG_CHAT_ID")
    
    tg_message = f"🎫 <b>PTT 演唱會票券搜尋結果</b>\n🔍 關鍵字: {keyword}\n\n"
    
    if len(found_tickets) == 0:
        print("未找到相關票券。你可以嘗試增加搜尋頁數，或是稍微修改關鍵字。")
        tg_message += "目前沒有找到相關票券。QQ"
    else:
        print(f"找到共 {len(found_tickets)} 筆結果：\n")
        
        # 為了避免 Telegram 訊息過長，如果結果很多，我們會限制筆數
        MAX_RESULTS = 20 
        display_tickets = found_tickets[:MAX_RESULTS]
        
        tg_message += f"找到共 {len(found_tickets)} 筆結果：\n\n"
        
        for ticket in display_tickets:
            print(f"時間: {ticket['date']} | 作者: {ticket['author']}")
            print(f"標題: {ticket['title']}")
            print(f"連結: {ticket['url']}")
            print("-" * 50)
            
            tg_message += f"📅 {ticket['date']} | 👤 {ticket['author']}\n"
            tg_message += f"📝 <a href='{ticket['url']}'>{ticket['title']}</a>\n\n"
            
        if len(found_tickets) > MAX_RESULTS:
            tg_message += f"...還有 {len(found_tickets) - MAX_RESULTS} 筆結果因篇幅較長未顯示。"
            
    if tg_token and tg_chat_id:
        send_telegram_message(tg_token, tg_chat_id, tg_message)
        print("\n[✔] 結果已發送至 Telegram。")
