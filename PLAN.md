# Orpheus LLM 自然語言控制計畫

## 目標
讓這個 Discord 音樂機器人除了 `!play` 這類指令外，也能聽懂自然語言，例如：

- `請幫我播放周杰倫 稻香`
- `幫我暫停`
- `下一首`
- `現在在播什麼`

重點不是直接把播放器重寫，而是：

1. 保留現在已經能用的 `play / pause / skip / now_playing` 指令流程
2. 在「收到訊息」的地方多加一層 LLM 判斷
3. 讓 LLM 只負責「判斷你想做什麼」
4. 真正執行播放，還是交給原本的 bot 指令

## 你要先理解的現況

目前這個專案的責任分工大致是：

- `bot.py`
  - 啟動 Discord bot
  - 載入各個 cog
- `src/cogs/player.py`
  - 定義 `!play`、`!pause`、`!skip`、`!join` 等指令
- `src/cogs/message.py`
  - 處理一般訊息事件 `on_message`
- `src/utils/play_utils.py`
  - 真正處理進語音、排隊、播放、播完接下一首
- `src/utils/ytb_utils.py`
  - 把關鍵字或 YouTube 連結轉成可播放音訊

所以如果要支援「請幫我播放某某歌」，最好的切入點通常不是改播放器，而是改 `on_message`。

## 實作策略

### 第 1 階段：先定義自然語言要轉成什麼格式

先不要急著接 API，先決定 LLM 回來要長什麼樣子。

建議格式：

```json
{
  "action": "play",
  "query": "周杰倫 稻香"
}
```

或：

```json
{
  "action": "pause",
  "query": ""
}
```

建議先把 action 控制在少數幾種：

- `play`
- `pause`
- `resume`
- `skip`
- `stop`
- `join`
- `leave`
- `now_playing`
- `none`

這樣做的原因是：

- LLM 容易亂講，但如果輸出格式很小，穩定度會高很多
- 我們可以把 LLM 限制成「分類器」，不是讓它直接控制整個 bot

### 第 2 階段：新增一個 LLM 工具模組

建議新增：

- `src/utils/llm_utils.py`

這個檔案只做一件事：

- 傳入使用者原話
- 回傳結構化意圖，例如 `{"action": "play", "query": "YOASOBI Idol"}`

這層不要碰 Discord，也不要碰播放邏輯，單純做「文字 -> 意圖」。

建議裡面包含：

1. `is_llm_enabled()`
   - 檢查有沒有 API key
2. `parse_music_request(text: str) -> dict`
   - 呼叫 LLM
   - 要求它只回 JSON
3. `fallback_parse(text: str) -> dict`
   - 如果 LLM 壞掉，至少還能吃簡單句型

### 第 3 階段：在設定檔補 LLM 環境變數

建議在 `src/config.py` 加上：

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_BASE_URL`（可選，若你之後想接相容服務）

`.env` 可能會長這樣：

```env
DISCORD_TOKEN=...
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
```

如果你之後不一定用 OpenAI，也可以把命名改成更中性的：

- `LLM_API_KEY`
- `LLM_MODEL`
- `LLM_BASE_URL`

但如果你現在只是先學接法，直接用 OpenAI 命名最直覺。

### 第 4 階段：在 `message.py` 攔自然語言

`src/cogs/message.py` 裡的 `on_message` 是最自然的入口。

流程建議是：

1. 忽略 bot 自己的訊息
2. 如果是 `!` 開頭的正式指令，就不要碰，交給原本 command system
3. 判斷這句話是不是在對 bot 下命令
4. 如果像是命令，就送去 `llm_utils.parse_music_request(...)`
5. 根據回傳的 `action`，再去呼叫原本的 command

也就是：

- `請幫我播放稻香` -> invoke `play`
- `幫我暫停` -> invoke `pause`
- `下一首` -> invoke `skip`

這邊的關鍵觀念是：

不是自己重寫一份 pause / skip / play，
而是「把自然語言翻譯成你現有的 command 呼叫」。

這樣有三個好處：

1. 既有功能不用重做
2. Bug 只會集中在自然語言判斷層
3. 未來指令行為改了，也只要維護一套

### 第 5 階段：設計觸發規則，避免 bot 對所有聊天都亂回

這一步非常重要。

如果你把所有訊息都丟給 LLM，會有幾個問題：

- 成本高
- 延遲高
- bot 可能把一般聊天誤判成播放命令

所以建議先限制只有以下情況才進 LLM：

1. 訊息有 mention bot
2. 句子包含明顯控制詞，例如：
   - `播放`
   - `暫停`
   - `下一首`
   - `跳過`
   - `繼續播放`
   - `現在在播什麼`
3. 或者你指定一個自然語言前綴，例如：
   - `小歐 幫我播稻香`
   - `bot 請播放告五人`

這樣比較不會誤觸。

### 第 6 階段：把 LLM 輸出映射回原本指令

這一段是整個設計最核心的地方。

你會從 `on_message` 拿到一個 `ctx`，然後：

- 找到對應 command
- 用 `ctx.invoke(...)` 呼叫它

概念像這樣：

```python
cmd = self.bot.get_command("play")
await ctx.invoke(cmd, search="周杰倫 稻香")
```

其他動作也是一樣：

- `pause` -> `self.bot.get_command("pause")`
- `skip` -> `self.bot.get_command("skip")`
- `now_playing` -> `self.bot.get_command("now_playing")`

也就是說，LLM 不直接碰播放器，只是幫你選 command 和參數。

### 第 7 階段：做 fallback，避免 LLM 掛掉整台 bot 就失能

建議一定要有 fallback。

例如：

- 如果沒有設定 API key，就用簡單關鍵字規則
- 如果 LLM timeout 或回傳格式錯誤，就回退到 regex

最低限度規則可以先做：

- `請幫我播放(.*)` -> `play`
- `暫停` -> `pause`
- `繼續` -> `resume`
- `下一首|跳過` -> `skip`

這樣就算 LLM 暫時不能用，你還是能展示一個可用版本。

## 建議修改檔案

如果你要自己動手，建議順序如下：

1. `src/config.py`
   - 新增 LLM 相關設定
2. `requirements.txt`
   - 加入 OpenAI SDK 或你選的 LLM client
3. `src/utils/llm_utils.py`
   - 新增 LLM 解析模組
4. `src/cogs/message.py`
   - 接上自然語言入口
5. `README.md`
   - 補 `.env` 和使用方式說明

## 建議學習順序

不要一次全改，照下面順序學最快：

### Step 1
先看懂 `player.py` 的 `play()` 怎麼呼叫 `play_utils.play(...)`

你要先知道：

- 真正播放不是在 `message.py`
- `message.py` 只是入口

### Step 2
在 `message.py` 先不用 LLM，直接硬寫：

- 如果訊息是 `請幫我播放稻香`
- 就呼叫 `play`

先把「自然語言入口 -> invoke command」打通。

### Step 3
確認上一步沒問題後，再把「硬寫字串判斷」換成「LLM 回 JSON」

### Step 4
最後才補 fallback、README、環境變數整理

這樣你學到的是完整拆解，不會一開始就被 API 細節淹沒。

## 風險與注意事項

### 1. 不要讓 LLM 直接回 Python 指令

錯誤方向：

- 叫 LLM 回傳 `!play 稻香`
- 或更糟，讓它回傳可執行程式碼

正確方向：

- 只讓它回固定 JSON

### 2. 不要讓所有訊息都進 LLM

否則 bot 會：

- 很吵
- 很慢
- 很花錢

### 3. `on_message` 很容易和原本指令系統打架

如果你之後改成覆寫 `bot.on_message()`，要記得處理 command flow。

目前這個專案用 cog listener，比較安全，但還是要注意：

- `!play` 這種正式指令不要被自然語言層攔走

### 4. 語音控制前提仍然存在

即使自然語言成功判斷成 `play`，使用者還是要：

- 已經在語音頻道裡

因為真正限制是在 `play_utils.get_voice_client(ctx)`。

## 最小可行版本（MVP）

如果你只想先做能展示的版本，先完成這些就夠了：

1. 在 `.env` 加 `OPENAI_API_KEY`
2. 新增 `src/utils/llm_utils.py`
3. 讓 `message.py` 能辨識：
   - `請幫我播放 ...`
   - `暫停`
   - `下一首`
4. 成功轉呼叫既有 `play / pause / skip`

這樣你就已經完成「不用打 bot 指令，直接講人話控制播放」。

## 我建議你下一步怎麼學

最適合的教學節奏是：

1. 我先帶你做「不用 LLM 的自然語言版」
2. 你看懂 `ctx.invoke(...)` 怎麼把句子接到原本指令
3. 再把那一層替換成真正的 LLM

這樣你不會一開始就卡在 API、JSON parsing、prompt 設計。

如果你要，我下一步可以直接用你這個專案的檔案結構，帶你做：

「第一課：先不用 LLM，做一個 `請幫我播放 XXX` 就能觸發 `!play` 的版本」
