# 校園找書｜Book Portal

專為大學生設計的書籍搜尋入口。使用 Open Library 查詢書目，並提供金石堂、Readmoo 與 HyRead 的搜尋跳轉，方便比較購買與圖書館借閱選項。

## 功能

- 依書名、作者或 ISBN 搜尋 Open Library。
- 顯示書名、最多兩位作者、首刷年份與封面，缺少資料時提供友善預設內容。
- 提供金石堂實體書、Readmoo 電子書及 HyRead 圖書館搜尋連結。
- Flask Serverless Function，適用 Vercel Python Runtime。

## 本機啟動

需要 Python 3.10 或更新版本。

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS / Linux：source .venv/bin/activate
pip install -r requirements.txt
python api/index.py
```

開啟 <http://127.0.0.1:5000>。

## 部署到 Vercel

1. 將專案推送到 GitHub Repository。
2. 登入 [Vercel](https://vercel.com/)，選擇 **Add New → Project**，匯入該 GitHub Repository。
3. Framework Preset 選擇 **Other**；保留根目錄設定，不需要 Build Command 或 Output Directory。
4. 按 **Deploy**。`vercel.json` 會將所有路徑導向 `api/index.py`。

安裝並登入 Vercel CLI 後，也可於專案根目錄執行：

```bash
vercel
vercel --prod
```

## 推送到新的 GitHub Repository

先在 GitHub 建立空白 Repository（不要勾選新增 README、License 或 .gitignore），再於專案根目錄執行：

```bash
git init
git add api/index.py templates/index.html requirements.txt vercel.json .gitignore README.md
git commit -m "Build university book portal"
git branch -M main
git remote add origin https://github.com/<你的GitHub帳號>/<Repository名稱>.git
git push -u origin main
```

將 remote URL 中的帳號與 Repository 名稱換成你的資料。之後即可在 Vercel 匯入此 Repository。

## 專案結構

```text
.
├── api/
│   └── index.py
├── templates/
│   └── index.html
├── requirements.txt
├── vercel.json
├── .gitignore
└── README.md
```
