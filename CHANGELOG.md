# 更新日誌

所有對 Orpheus Discord 音樂機器人的重要變更都會記錄在此。

## [2.0.0] - 2026-03-25

### 主要變更 - 從 Wavelink/Lavalink 遷移

整個機器人架構已全面重構，以移除 Wavelink 和 Lavalink 的依賴，改用現代化且維護良好的開源庫，實現更穩定的本地運行方案。

### 變更內容

#### 依賴套件 (requirements.txt)
- **更新**: `discord.py` 從 2.2.2 升至 >= 2.3.0（最新 API 支援）
- **新增**: `yt-dlp`（現代 YouTube 音訊下載器及元資料提取工具）
- **新增**: `spotipy`（Spotify Web API 包裝庫）
- **新增**: `python-dotenv`（環境變數管理）
- **移除**: `wavelink`（音訊節點播放器）
- **移除**: `pytube`（被 yt-dlp 取代）
- **移除**: `youtube_dl`（已棄用，被 yt-dlp 取代）
- **移除**: `selenium` 和 `bs4`（不再需要）

#### 配置設定 (config.py)
- 整合 `python-dotenv` 以從 `.env` 檔案安全加載憑證
- 修正變數名稱 `SPOTIFY_CLIENT_SECRET_ID` → `SPOTIFY_CLIENT_SECRET`
- 所有 API 憑證改為運行時動態加載，而非硬編碼

#### 核心播放系統 (utils/play_utils.py)
- **新增**: `Track` 類用於統一表示音樂軌道
  - 屬性: `title`、`author`、`url`、`duration`、`thumbnail`
- **移除**: 所有 `wavelink.Player` 和 `wavelink.GenericTrack` 引用
- **變更**: 語音客戶端改使用標準 `discord.VoiceClient`
- **變更**: 音訊播放改用 `discord.FFmpegPCMAudio` 代替 Wavelink
- **新增**: `on_track_end()` 回調函數，處理自動隊列推進和循環播放
- **更新**: 隊列管理改用 Python 原生 `collections.deque` 代替 Wavelink Queue
- **重命名**: `get_currenly_playing()` → `get_currently_playing()`（修正拼寫錯誤）
- **變更**: 循環屬性: `loopq` → `loop_all`（更清晰）

#### YouTube 支援 (utils/ytb_utils.py)
- **移除**: 所有 `wavelink.YouTubeTrack` 和 `wavelink.YouTubePlaylist` 使用
- **取代**: 用 `yt-dlp` 代替 `pytube` 進行穩健的 YouTube 音訊串流
- **新增**: `get_track_from_search()`（搜尋 YouTube 並返回 Track 物件）
- **新增**: `get_track_from_url()`（從 YouTube URL 提取軌道資訊）
- **新增**: `YDL_OPTS` 設定字典用於 yt-dlp 配置
- **變更**: 播放清單處理改使用 yt-dlp 的平面提取模式
- **改進**: 添加全面的 try-except 錯誤處理

#### Spotify 支援 (utils/spotify_utils.py)
- **移除**: 所有 `wavelink.ext.spotify` 使用
- **取代**: 改用 `spotipy` 庫訪問 Spotify API
- **新增**: Spotify 客戶端初始化，憑證來自 `.env`
- **變更**: Spotify 軌道播放改為在 YouTube 搜尋等價歌曲進行音訊播放
  - 提取歌曲名稱 + 藝人在 YouTube 上搜尋
  - 透過 yt-dlp 播放音訊（Spotify 不允許直接第三方串流）
- **新增**: Spotify 播放清單解析支援
- **新增**: Spotify 專輯解析支援
- **改進**: Spotify 連結 URL 解析（軌道/播放清單/專輯）

#### 嵌入訊息生成 (utils/embed_utils.py)
- **移除**: `wavelink` 導入和型別提示
- **新增**: `typing.Any` 用於靈活型別支援
- **變更**: `show_queue()` 改用 `deque` 代替 `wavelink.Queue`
- **更新**: 所有嵌入方法改為與新 `Track` 類兼容

#### 隊列工具程式 (utils/queue_utils.py)
- **移除**: `wavelink` 導入
- **新增**: `deque` 和 `typing` 導入
- **更新**: `add_to_previous_queue()` 改為接受 `Track` 物件
- **更新**: `shuffle()` 函數改用 deque 代替 wavelink Queue

#### 機器人主程式 (bot.py)
- **移除**: `wavelink` 和 `wavelink.ext.spotify` 導入
- **移除**: `tasks` 導入（不再需要）
- **移除**: `setup_hook()` 方法（無需連接 Lavalink 節點）
- **變更**: Token 加載改為使用 `config.DISCORD_TOKEN` 代替 `os.getenv()`
- **修正**: `load_extension()` 呼叫 - 改為 `await self.load_extension()`
- **簡化**: 機器人初始化 - 無需外部服務依賴

#### 播放器命令 (cogs/player.py)
- **移除**: 所有 `wavelink.Player` 型別提示
- **變更**: 語音客戶端改用 `discord.VoiceClient`
- **更新**: 所有命令改為與新隊列系統（deque）兼容
- **修正**: 隊列存取從 `vc.queue.is_empty` 和 `vc.queue.count` 改為簡單列表操作
- **更新**: `now_playing()` 命令改用 `vc.current_track`
- **更新**: `skipto()` 邏輯適配 deque 隊列
- **更新**: `remove()` 命令適配 deque 操作
- **更新**: `search()` 命令適配 deque 迭代

#### 循環和隊列命令 (cogs/loop_queue.py)
- **移除**: 註解掉的 `on_wavelink_track_end()` 監聽器（被 on_track_end 回調取代）
- **移除**: `Paginator` 導入（未使用）
- **變更**: 屬性名稱 `loopq` → `loop_all`
- **更新**: 循環邏輯改為與 deque 隊列兼容
- **更新**: 隊列複製改用 Python 列表 `copy()`

#### 環境配置
- **新增**: `.env` 檔案範本，包含以下佔位符:
  - `DISCORD_TOKEN`
  - `SPOTIFY_CLIENT_ID`
  - `SPOTIFY_CLIENT_SECRET`

### 修正項目

- Token 引用不一致（`os.getenv()` vs 配置加載）
- 拼寫錯誤: `get_currenly_playing()` → `get_currently_playing()`
- 原代碼拼寫錯誤: "Load moduel" → "Load module"
- 移除源代碼中硬編碼的 Spotify 憑證
- 修正 loop_queue.py 的文件字符串語法錯誤

### 移除項目

- `scripts/youtube.py`（舊棄用 YouTube 下載腳本）
- 所有 Lavalink/Java 伺服器要求（機器人現在獨立運行）
- Wavelink Node Pool 依賴
- 外部音訊伺服器基礎設施

### 重構的優勢

1. **獨立執行**: 機器人在本地運行，無需外部 Lavalink 伺服器
2. **更好維護**: 使用積極維護的庫（yt-dlp、spotipy）
3. **簡化部署**: 無需配置 Java/Lavalink
4. **更簡潔代碼**: 移除 200+ 行 Wavelink 樣板代碼
5. **安全性**: 憑證改由 `.env` 管理，不再硬編碼
6. **更好錯誤處理**: 全面的 try-except 區塊
7. **現代 Python**: 使用 deque 和型別提示

### 遷移說明

- 用戶必須在 `.env` 檔案中填入 Discord Token 和 Spotify API 憑證
- 必須在本地安裝 FFmpeg（用於音訊轉碼）
- 無需再執行 Lavalink.jar
- 機器人可直接透過 `python bot.py` 啟動

### 已知問題

- Spotify 播放品質取決於 YouTube 匹配結果（不是直接 Spotify 串流）
- 需要在系統上安裝 FFmpeg

### 後續步驟（第三階段 - 測試）

1. 在 `.env` 中填入實際憑證
2. 測試基本命令: `!play`、`!pause`、`!skip` 等
3. 驗證 YouTube 和 Spotify 播放功能
4. 測試隊列和循環功能
5. 驗證語音頻道管理功能
