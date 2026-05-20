## 🧠 AI 每日猜謎系統 (Candidate Guess)
本功能每天自動定時選題，並透過 Google Gemini API 生成具有幽默感與誤導性的 3 句提示。全伺服器玩家將共同挑戰這道謎題，並即時統計首殺與答對排名。

### ⚙️ 技術亮點
* **高可用故障重試 (Failure Retry)**：若遇到 Google AI 伺服器過載或流量限制，系統將在一小時內每 5 分鐘自動更換 Key 並重試（最多 12 次）。
* **智能模糊判定**：
  1. 限制輸入 30 字元內，防止惡意洗版。
  2. 支援「包含判定」（例如答案是「張飛」，輸入「我想是張飛吧」亦視為正確）。
  3. 自動比對 AI 母庫中提供的各式別名與英文縮寫（`maybe_ans`）。
* **動態榮譽榜**：答對時自動清理玩家的正確答案訊息，並發送金色榮譽 Embed，動態抓取玩家頭像與名次。

### 📃 使用方式
1. 使用管理員指令 `/candidate_channel_register` 登記活動頻道。
2. 在 `data/guess_candidate/candidate_pool.json` 中配置你的人物/對象母庫。

**配置範例 (candidate_pool.json)：**
```json
{
  "history_western": {
    "name": "西方歷史人物",
    "pool": ["達伽馬", "拿破崙", "凱薩大帝"]
  },
  "cs_scientists": {
    "name": "資工領域的科學家",
    "pool": ["林納斯·托瓦茲", "艾倫·圖靈"]
  }
}