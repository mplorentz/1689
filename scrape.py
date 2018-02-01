from bs4 import BeautifulSoup
import urllib.request
import sys

def get_verse_text_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find(class_="scripture").find("span").next_sibling.next_sibling.text.strip()

def get_asv_html(book, chapter, verse):
    url = "https://www.biblestudytools.com/asv/%s/%s-%s.html" % (book, chapter, verse)

    req = urllib.request.Request(
        url,
        data=None,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
        }
    )

    return urllib.request.urlopen(req).read()

def main():
    book = sys.argv[1]
    chapter = sys.argv[2]
    verse = sys.argv[3]
    html = get_asv_html(book, chapter, verse)
    print(get_verse_text_from_html(html))


if __name__ == "__main__":
    main()
