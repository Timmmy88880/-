# 台股晨訊

每日台股與半導體供應鏈晨間簡報的系統提示範本。

## 內容

- [`prompts/taiwan-stock-morning-brief.md`](prompts/taiwan-stock-morning-brief.md) — 完整系統提示,供搭配具備即時搜尋能力的助理於每日 07:00(台北時間)產出「台股晨訊」。

## 使用方式

1. 複製 `prompts/taiwan-stock-morning-brief.md` 的內容作為系統提示。
2. 將下列佔位符替換為實際內容:
   - `{{WATCHLIST}}`:自選股清單(代號｜名稱,每行一檔)
   - `{{TOP_N}}`:台股焦點區塊要列出的則數
   - `{{OVERSEAS_SECTION}}`:額外的海外/國際觀察區塊內容,無則留空
3. 每日搭配當日日期與(選擇性的)MOPS 重訊資料作為使用者訊息送出,產生晨訊。

## 資料來源

- 正式來源:經濟日報、工商時報、中央社、聯合報、鉅亨網、ETtoday、Yahoo 股市、財報狗(台股新聞);BBC、CNN、彭博(國際新聞)。
- 輔助工具:`https://jianxuanchiustock.netlify.app/?stock=<代號>` — 個股查詢用的非官方個人網站,僅供輔助比對,引用時需標註「輔助工具來源,非官方」並與正式來源交叉核對。目前此網域在部分執行環境的網路出口代理下會被擋(`EGRESS_BLOCKED`),若遇到連線失敗,需改用正式來源或人工提供資料。
