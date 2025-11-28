import requests
from collections import deque
from bs4 import BeautifulSoup
from urllib.parse import urljoin

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
                response = requests.get(url, headers=headers, timeout=7)
                soup = BeautifulSoup(response.text, "html.parser")

                # Select content block
                content = soup.select_one("div.mw-parser-output")
                if not content:
                    continue

                # Extract clean page text
                full_text = content.get_text(separator=" ", strip=True)

                # Extract image (OpenGraph first, then fallback)
                og_image = soup.find("meta", property="og:image")
                if og_image and og_image.get("content"):
                    image_url = og_image["content"]
                else:
                    first_img = content.find("img")
                    image_url = (
                        "https:" + first_img["src"]
                        if first_img and first_img.get("src", "").startswith("//")
                        else None
                    )

                # Save page info
                pages[url] = {
                    "title": soup.title.string.strip() if soup.title else url,
                    "text": full_text,
                    "image": image_url,
                }

                self.visited.add(url)

                # Add new links to queue
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    if href.startswith("/wiki/") and ":" not in href:
                        full_url = urljoin(url, href)
                        if full_url not in self.visited:
                            self.queue.append(full_url)

            except Exception as e:
                print("Error fetching:", url, "|", e)
                continue

        print(f"Finished crawling {len(pages)} pages.")
        return pages
