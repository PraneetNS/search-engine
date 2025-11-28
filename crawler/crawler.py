import requests
from collections import deque
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from indexer.storage import save_index, load_index
save_index(idx.index, idx.doc_lengths)

class Crawler:
    def __init__(self, max_pages=50):
        self.visited = set()
        self.queue = deque()
        self.max_pages = max_pages

    def crawl(self, start_url):
        self.queue.append(start_url)
        pages = {}

        while self.queue and len(pages) < self.max_pages:
            url = self.queue.popleft()
            if url in self.visited:
                continue

            print("Crawling:", url)

            try:
                headers = {"User-Agent": "Mozilla/5.0 (compatible; MiniSearchBot/1.0)"}
                response = requests.get(url, headers=headers, timeout=5)

                soup = BeautifulSoup(response.text, 'html.parser')
                content = soup.select_one("div.mw-parser-output")

                if content:
                    pages[url] = content.get_text(separator=" ", strip=True)

                self.visited.add(url)

                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    if href.startswith("/wiki/") and ":" not in href:
                        full_url = urljoin(url, href)
                        self.queue.append(full_url)

            except Exception as e:
                print("Error:", e)
                continue

        return pages
