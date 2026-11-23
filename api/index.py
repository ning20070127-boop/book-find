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


def search_books(query):
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

    books = []
    for item in payload["docs"]:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or "未提供書名"
        authors = item.get("author_name")
        author = ", ".join(str(name) for name in authors[:2] if name) if isinstance(authors, list) and authors else "作者不詳"
        if not author:
            author = "作者不詳"
        isbns = item.get("isbn")
        term = quote(str(isbns[0] if isinstance(isbns, list) and isbns else title), safe="")
        cover_id = item.get("cover_i")
        cover_url = None
        if cover_id:
            cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg?default=false"
        elif isinstance(isbns, list) and isbns and isbns[0]:
            cover_url = f"https://covers.openlibrary.org/b/isbn/{quote(str(isbns[0]), safe='')}-M.jpg?default=false"
        books.append({
            "title": title, "author": author,
            "year": item.get("first_publish_year") or "年份未知",
            "cover_url": cover_url,
            "links": {
                "kingstone": f"https://www.kingstone.com.tw/search/key/{term}/",
                "readmoo": f"https://readmoo.com/search/keyword?q={term}",
                "hyread": f"https://ebook.hyread.com.tw/searchList.jsp?search_field=FullText&search_input={term}",
            },
        })
    return books, None


@app.route("/", methods=["GET"])
def index():
    query = request.args.get("q", "").strip()
    books, error = search_books(query) if query else ([], None)
    return render_template("index.html", query=query, books=books, error=error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
