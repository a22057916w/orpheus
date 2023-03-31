from bs4 import BeautifulSoup

html = """
<div class="class1 class2">
    <p>hello world 1</p>
</div>
<div class="class1">
    <p>hello world 2</p>
</div>

<div class="class1 class2">
    <p>hello world 3</p>

"""

soup = BeautifulSoup(html, "html.parser")

# 使用 select 方法來搜尋有 class1 與 class2 兩個 class 的 div 標籤
div_tags = soup.select(".class1.class2")

# 取得每個 div 標籤內的文字
for div_tag in div_tags:
    text = div_tag.text
    print(text)
