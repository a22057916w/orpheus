from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup

# 設定 Chrome 瀏覽器的選項
options = webdriver.ChromeOptions()
options.add_argument("--headless") # 不開啟瀏覽器視窗

# 建立 Chrome 瀏覽器物件
driver = webdriver.Chrome(options=options)

url = "https://www.youtube.com/playlist?list=PL1urwPG3M3NKahUbWDj_Y1qgwtRvhMpN7"
# 前往要爬取的網頁
driver.get(url)

# Render the dynamic content to static HTML
html = driver.page_source
# print(html)

with open("html.txt", "w", encoding="utf-8") as f:
    f.write(html)

# Parse the static HTML
soup = BeautifulSoup(html, 'html.parser')

# 找出所有影片連結所在的元素 by css selector
video_links = soup.select('a.yt-simple-endpoint.style-scope.ytd-playlist-video-renderer')

# 印出每個影片的 URL
for link in video_links:
    video_url = 'https://www.youtube.com' + link['href']
    print(video_url)
