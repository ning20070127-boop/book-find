from urllib.parse import quote
import requests
from flask import Flask, render_template, request

app = Flask(__name__, template_folder="../templates")
API_URL = "https://openlibrary.org/search.json"
FIELDS = "title,author_name,first_publish_year,cover_i,isbn,key"
HEADERS = {"User-Agent": "UniBookPortal/1.0 (student-project@example.com)"}
SEARCH_ALIASES = {
    "魔道祖師": 'title:"Mo Dao Zu Shi" OR title:"Grandmaster of Demonic Cultivation"',
    "魔道祖师": 'title:"Mo Dao Zu Shi" OR title:"Grandmaster of Demonic Cultivation"',
}
TAIWAN_BOOKS = {
    "sunrise_house": [
        {"title": "日昇之屋 1", "author": "Jeong Seokchan", "year": 2026, "isbn": "9786267818640", "cover_url": "https://cdnec.sanmin.com.tw/product_images/626/626781864.jpg"},
        {"title": "日昇之屋 2", "author": "Jeong Seokchan", "year": 2026, "isbn": "9786267818657", "cover_url": "https://cdnec.sanmin.com.tw/product_images/626/626781865.jpg"},
    ],
    "scum_villain": [
        {"title": "人渣反派自救系統 上（新裝版）", "author": "墨香銅臭", "year": 2022, "isbn": "9789864944842", "cover_url": "https://cdnec.sanmin.com.tw/product_images/986/986494484.jpg"},
        {"title": "人渣反派自救系統 中（新裝版）", "author": "墨香銅臭", "year": 2022, "isbn": "9789864944859", "cover_url": "https://cdnec.sanmin.com.tw/product_images/986/986494485.jpg"},
        {"title": "人渣反派自救系統 下（新裝版）", "author": "墨香銅臭", "year": 2022, "isbn": "9789864944866", "cover_url": "https://cdnec.sanmin.com.tw/product_images/986/986494486.jpg"},
    ],
    "flashlight": [
        {"title": "FLASHLIGHT 1", "author": "YANGMA", "year": 2026, "isbn": "9786264359351", "cover_url": "https://img.shoplineapp.com/media/image_clips/6957836ed6971efdb9f3c908/original.jpg?1767342957=&owner_id=655b0f3c9b81d900188b35f1"},
    ],
}


def make_book(title, author, year, isbn, cover_url):
    term = quote(str(isbn or title), safe="")
    return {
        "title": title,
        "author": author,
        "year": year,
        "cover_url": cover_url,
        "links": {
            "kingstone": f"https://www.kingstone.com.tw/search/key/{term}/",
            "readmoo": f"https://readmoo.com/search/keyword?q={term}",
            "hyread": f"https://ebook.hyread.com.tw/searchList.jsp?search_field=FullText&search_input={term}",
        },
    }


def contains_chinese(text):
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def search_books(query):
    compact_query = query.casefold().replace(" ", "")
    local_books = None
    if "日昇之屋" in query or "日升之屋" in query:
        local_books = TAIWAN_BOOKS["sunrise_house"]
    elif "人渣反派自救" in query:
        local_books = TAIWAN_BOOKS["scum_villain"]
    elif "flashlight" in compact_query or "flashlige" in compact_query:
        local_books = TAIWAN_BOOKS["flashlight"]
    if local_books is not None:
        return [make_book(**book) for book in local_books], None

    if query in {"國文", "數學"}:
        return [], "「國文／數學」是科目分類，對應很多出版社、年級與冊次。請輸入課本完整書名、年級／冊次、出版社或 ISBN，才能找到正確版本。"

    # Open Library rejects plain queries shorter than three characters. A
    # title/author field query keeps short Chinese terms searchable.
    api_query = SEARCH_ALIASES.get(query, query)
    if api_query == query and len(query) < 3:
        phrase = query.replace("\\", "\\\\").replace('"', '\\"')
        api_query = f'title:"{phrase}" OR author:"{phrase}"'

    try:
        response = requests.get(API_URL, params={"q": api_query, "limit": 12, "fields": FIELDS}, headers=HEADERS, timeout=6)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("docs"), list):
            raise ValueError("Unexpected Open Library response")
    except requests.Timeout:
        return [], "搜尋服務回應較慢，請稍後再試。"
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 422:
            return [], "Open Library 無法處理這組搜尋條件，請改用更完整的書名、作者或 ISBN。"
        return [], "目前無法取得書籍資料，請稍後再試。"
    except requests.RequestException:
        return [], "連線 Open Library 失敗，請檢查網路後再試。"
    except (ValueError, requests.exceptions.JSONDecodeError):
        return [], "書籍資料格式暫時無法讀取，請稍後再試。"
    except Exception:
        return [], "搜尋時發生暫時性問題，請稍後再試。"

    docs = payload["docs"]
    if contains_chinese(query) and query not in SEARCH_ALIASES:
        docs = [
            item for item in docs
            if isinstance(item, dict)
            and (query in str(item.get("title", ""))
                 or any(query in str(name) for name in (item.get("author_name") or [])))
        ]

    books = []
    for item in docs:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or "未提供書名"
        authors = item.get("author_name")
        author = ", ".join(str(name) for name in authors[:2] if name) if isinstance(authors, list) and authors else "作者不詳"
        if not author:
            author = "作者不詳"
        isbns = item.get("isbn")
        isbn = isbns[0] if isinstance(isbns, list) and isbns else None
        cover_id = item.get("cover_i")
        cover_url = None
        if cover_id:
            cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg?default=false"
        elif isinstance(isbns, list) and isbns and isbns[0]:
            cover_url = f"https://covers.openlibrary.org/b/isbn/{quote(str(isbns[0]), safe='')}-M.jpg?default=false"
        books.append(make_book(title, author, item.get("first_publish_year") or "年份未知", isbn, cover_url))
    if contains_chinese(query) and not books:
        return [], "Open Library 的台灣中文書目涵蓋有限，這次沒有找到相符書目。可改用完整 ISBN，或補上作者／出版社名稱搜尋。"
    return books, None


@app.route("/", methods=["GET"])
def index():
    query = request.args.get("q", "").strip()
    books, error = search_books(query) if query else ([], None)
    return render_template("index.html", query=query, books=books, error=error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
