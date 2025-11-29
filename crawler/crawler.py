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

                content = soup.select_one("div.mw-parser-output")
                if not content:
                    continue

                # Extract valid text
                full_text = content.get_text(separator=" ", strip=True)

                # Find first featured image
                og_image = soup.find("meta", property="og:image")
                image_url = og_image["content"] if og_image else None

                if not image_url:
                    first_img = content.find("img")
                    if first_img and first_img.get("src", "").startswith("//"):
                        image_url = "https:" + first_img["src"]

                # Derive category from URL
                try:
                    category = url.split("/wiki/")[1].split("_")[0]
                except:
                    category = "general"

                # Store result
                pages[url] = {
                    "title": soup.title.string if soup.title else url,
                    "text": full_text,
                    "image": image_url,
                    "category": category.lower()
                }

                self.visited.add(url)

                # Queue discovery links
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
