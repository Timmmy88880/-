# 台股晨訊

每日台股與半導體供應鏈晨間簡報的系統提示範本。

## 內容

- [`prompts/taiwan-stock-morning-brief.md`](prompts/taiwan-stock-morning-brief.md) — 系統提示的文件版本(含佔位符說明),供人工閱讀與手動使用。
- [`scripts/morning_note_prompt.md`](scripts/morning_note_prompt.md) — 系統提示的純文字版本,供 `scripts/morning_note.py` 讀取後做字串替換,內容與上者同步。
- [`scripts/morning_note.py`](scripts/morning_note.py) — macOS `launchd` 自動化腳本:每日 07:00(Asia/Taipei)從證交所/櫃買 OpenAPI 抓自選股重訊、呼叫 Claude(含網路搜尋)產出晨訊、存成 `~/MorningNote/YYYY-MM-DD.md` 並跳出 macOS 通知。腳本內建自選股清單(依族群分組)、`TOP_N`、`INCLUDE_OVERSEAS` 等設定。
- [`scripts/requirements.txt`](scripts/requirements.txt) — 執行腳本所需的 Python 套件。

## 使用方式(手動)

1. 複製 `prompts/taiwan-stock-morning-brief.md` 的內容作為系統提示。
2. 將下列佔位符替換為實際內容:
   - `{{WATCHLIST}}`:自選股清單(代號｜名稱,每行一檔)
   - `{{TOP_N}}`:台股焦點區塊要列出的則數
   - `{{OVERSEAS_SECTION}}`:額外的海外/國際觀察區塊內容,無則留空
3. 每日搭配當日日期與(選擇性的)MOPS 重訊資料作為使用者訊息送出,產生晨訊。

## 使用方式(自動化腳本)

1. `pip install -r scripts/requirements.txt`
2. 設定環境變數 `ANTHROPIC_API_KEY`。
3. 先執行 `python3 scripts/morning_note.py --check-mops`,確認證交所/櫃買 OpenAPI 目前的欄位名稱與自選股清單能正確比對(腳本文件本身註明尚未在實機測試過)。
4. 確認無誤後,用 macOS `launchd` 設定每日 07:00(Asia/Taipei)執行 `python3 scripts/morning_note.py`(需自行建立對應的 `.plist`,本 repo 未附範例)。
5. 產出結果會寫入 `~/MorningNote/YYYY-MM-DD.md`,並跳出 macOS 通知告知成功或失敗。

## 資料來源

- 正式來源:經濟日報、工商時報、中央社、聯合報、鉅亨網、ETtoday、Yahoo 股市、財報狗(台股新聞);BBC、CNN、彭博(國際新聞)。
- 輔助工具:`https://jianxuanchiustock.netlify.app/?stock=<代號>` — 個股查詢用的非官方個人網站,僅供輔助比對,引用時需標註「輔助工具來源,非官方」並與正式來源交叉核對。目前此網域在部分執行環境的網路出口代理下會被擋(`EGRESS_BLOCKED`),若遇到連線失敗,需改用正式來源或人工提供資料。
