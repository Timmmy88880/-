#!/usr/bin/env python3
"""台股晨訊:每天 07:00(Asia/Taipei)由 launchd 觸發。

流程:
1. 從證交所/櫃買 OpenAPI 抓「每日重大訊息」,過濾自選股(避開 MOPS 網頁 JS 動態載入問題)
2. 呼叫 Claude(含網路搜尋)依 morning_note_prompt.md 產出晨訊
3. 存成 ~/MorningNote/YYYY-MM-DD.md,並跳出 macOS 通知

需求:pip install anthropic requests ; 環境變數 ANTHROPIC_API_KEY
注意:此腳本未在實機測試,OpenAPI 欄位名稱請先用 --check-mops 確認。
"""
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

# ---------- 設定 ----------
MODEL = "claude-sonnet-5"
TOP_N = 50                 # 台股焦點則數上限
INCLUDE_OVERSEAS = False   # True 時加入「海外個股」區塊
MAX_SEARCHES = 40
OUT_DIR = Path.home() / "MorningNote"
BASE = Path(__file__).resolve().parent
TZ = ZoneInfo("Asia/Taipei")

WATCHLIST = {
    "晶圓代工/先進封測": {"2330": "台積電", "2303": "聯電", "5347": "世界", "3711": "日月光投控", "6239": "力成", "6257": "矽格"},
    "IC設計/矽智財": {"2454": "聯發科", "2379": "瑞昱", "5274": "信驊", "3443": "創意", "3661": "世芯-KY"},
    "CoWoS/半導體設備與耗材": {
        "3131": "弘塑", "3583": "辛耘", "3680": "家登", "6438": "迅得", "2467": "志聖", "3455": "由田",
        "6664": "群翊", "6937": "天虹", "6953": "家碩", "7822": "倍利科", "7853": "政美應用", "8027": "鈦昇",
        "1560": "中砂", "1727": "中華化", "6488": "環球晶"},
    "廠務工程/循環經濟": {"2404": "漢唐", "6196": "帆宣", "6826": "和淞", "6903": "巨漢", "6944": "兆聯", "6894": "衛司特"},
    "AI伺服器/散熱/滑軌零組件": {
        "2059": "川湖", "3017": "奇鋐", "3324": "雙鴻", "3533": "嘉澤", "6584": "南俊國際", "6805": "富世達",
        "8210": "勤誠", "2308": "台達電", "2301": "光寶科", "4931": "新盛力"},
    "CCL/PCB/被動元件": {
        "2383": "台光電", "6274": "台燿", "8358": "金居", "2313": "華通", "3037": "欣興", "3715": "定穎投控",
        "4958": "臻鼎-KY", "6191": "精成科", "2472": "立隆電", "3026": "禾伸堂", "3357": "台慶科",
        "6449": "鈺邦", "8042": "金山電"},
    "光通訊/III-V族/記憶體": {
        "3081": "聯亞", "2455": "全新", "4991": "環宇-KY", "3105": "穩懋", "8086": "宏捷科", "2337": "旺宏",
        "2344": "華邦電", "2408": "南亞科", "3260": "威剛", "6531": "愛普*", "8299": "群聯"},
}
CODES = {c: n for grp in WATCHLIST.values() for c, n in grp.items()}

MOPS_URLS = {
    "上市": "https://openapi.twse.com.tw/v1/opendata/t187ap04_L",
    "上櫃": "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap04_O",
}

OVERSEAS_SECTION = """### 八、海外個股晨報(可選)
追蹤:SMFG/SMBC、MUFG、Goldman Sachs、Morgan Stanley、Citigroup、JPMorgan、Wells Fargo、Bank of America、Apple、Analog Devices、Texas Instruments、Home Depot、Mastercard、Visa。
挑過去 24 小時最重要的 3–5 則(財報、購併、監管、人事、評等/分析師動作、重大產品或法律事件);沒有重大消息的公司略過,全部都沒有就明說。
每則:標題(含公司)/重點概覽(2–3 句)/深入分析(長期影響與背景)/原始來源連結(真實 URL)。"""

WEEKDAY = "一二三四五六日"


def _pick(row: dict, *keys: str) -> str:
    for k in keys:
        v = row.get(k)
        if v not in (None, ""):
            return str(v).strip()
    return ""


def fetch_mops() -> tuple[list[dict], list[str]]:
    hits, errors = [], []
    for market, url in MOPS_URLS.items():
        try:
            r = requests.get(url, timeout=30, headers={"accept": "application/json"})
            r.raise_for_status()
            rows = r.json()
        except Exception as e:  # noqa: BLE001
            errors.append(f"{market}:{e}")
            continue
        for raw in rows:
            row = {str(k).strip(): v for k, v in raw.items()}
            code = _pick(row, "公司代號", "SecuritiesCompanyCode", "Code")
            if code in CODES:
                hits.append({
                    "市場": market,
                    "代號": code,
                    "名稱": CODES[code],
                    "發言日期": _pick(row, "發言日期", "Date"),
                    "發言時間": _pick(row, "發言時間", "Time"),
                    "主旨": _pick(row, "主旨", "Subject"),
                })
    return hits, errors


def build_system() -> str:
    text = (BASE / "morning_note_prompt.md").read_text(encoding="utf-8")
    wl = "\n".join(
        f"- {grp}:" + "、".join(f"{c}{n}" for c, n in items.items()) for grp, items in WATCHLIST.items()
    )
    return (text.replace("{{WATCHLIST}}", wl)
                .replace("{{TOP_N}}", str(TOP_N))
                .replace("{{OVERSEAS_SECTION}}", OVERSEAS_SECTION if INCLUDE_OVERSEAS else ""))


def generate(now: dt.datetime) -> str:
    import anthropic

    hits, errors = fetch_mops()
    mops_note = (
        f"MOPS OpenAPI 過濾後的自選股重訊(發言日期為民國年 yyyMMdd,可能包含前一日):\n{json.dumps(hits, ensure_ascii=False, indent=1)}"
        if not errors or hits else
        f"MOPS OpenAPI 取得失敗:{'; '.join(errors)}。請改用搜尋,並在報告中註明可信度較低。"
    )
    user = (
        f"今天是 {now:%Y-%m-%d}(週{WEEKDAY[now.weekday()]}),台北時間 {now:%H:%M}。請產出今天的台股晨訊。\n\n{mops_note}"
    )

    client = anthropic.Anthropic()
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": MAX_SEARCHES}]
    messages = [{"role": "user", "content": user}]
    final = ""
    for _ in range(8):  # 處理 pause_turn 續跑
        with client.messages.stream(
            model=MODEL, max_tokens=16000, system=build_system(), tools=tools, messages=messages
        ) as stream:
            msg = stream.get_final_message()
        final = "".join(b.text for b in msg.content if b.type == "text")
        if msg.stop_reason != "pause_turn":
            break
        messages.append({"role": "assistant", "content": msg.content})

    i = final.find("# 台股晨訊")
    return final[i:] if i >= 0 else final


def main() -> int:
    now = dt.datetime.now(TZ)
    if "--check-mops" in sys.argv:
        hits, errors = fetch_mops()
        print(json.dumps({"hits": hits, "errors": errors}, ensure_ascii=False, indent=1))
        return 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{now:%Y-%m-%d}.md"
    try:
        out.write_text(generate(now), encoding="utf-8")
        title, msg = "台股晨訊已產生", str(out)
    except Exception as e:  # noqa: BLE001
        title, msg = "台股晨訊失敗", str(e)[:200]
        print(msg, file=sys.stderr)
    subprocess.run(["osascript", "-e", f'display notification "{msg}" with title "{title}"'], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
