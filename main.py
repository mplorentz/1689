from bs4 import BeautifulSoup
import urllib.request
import sys
import re
from parser import *

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

def get_chapters_of_confession(confession_html):
    soup = BeautifulSoup(confession_html, 'html5lib')
    paragraphs = soup.find_all('p')
    chapters = []
    current_chapter = []

    for paragraph in paragraphs:
        if is_chapter_title(paragraph):
            chapters.append(current_chapter)
            current_chapter = [paragraph]
        else:
            current_chapter.append(paragraph)

    chapters.append(current_chapter)

    return [c for c in chapters if c]
    #return chapters

def is_chapter_title(paragraph):
    return paragraph.find('a') 

def get_verses_from_paragraph(paragraph):
    lines = str(paragraph).split('<br/>')
    verse_lines = [l for l in lines if looks_like_verse_references(l)]
    clean_verse_lines = [BeautifulSoup(l, 'html5lib').text[2:].replace('\n', '')for l in verse_lines]
    return clean_verse_lines

def looks_like_verse_references(line):
    soup = BeautifulSoup(line, 'html5lib')
    first_tag = str([c.contents[0] for c in soup.font.children][0])
    matcher = re.compile('<b>[0-9]</b>')
    return matcher.match(first_tag)


    #def __init__(self, book, start_chapter, end_chapter, start_verse, end_verse):
    #    self.book = book
    #    self.start_chapter = start_chapter
    #    self.end_chapter = end_chapter
    #    self.start_verse = start_verse
    #    self.end_verse = end_verse


def get_references_from_verse_line(verse_line):
    parser = ReferenceParser()
    parser.start(verse_line)
    return parser.references

def main():
    #book = sys.argv[1]
    #chapter = sys.argv[2]
    #verse = sys.argv[3]
    #html = get_asv_html(book, chapter, verse)

    with open('confession.html', 'r', encoding='iso-8859-1') as f:
        confession_html = f.read()

    chapters = get_chapters_of_confession(confession_html)
    verse_lines = []
    for chapter in chapters:
        for paragraph in chapter:
            #verses = get_verses_from_paragraph(paragraph)
            #if len(verses) > 0:
            #    verse_lines.append(verses)
            #print(get_references_from_verse_line(verse_line[2]))
            for verse_line in get_verses_from_paragraph(paragraph):
                for verse_reference in get_references_from_verse_line(verse_line):
                    print("%s" % (verse_reference))
    #verse_line = verse_lines[0][0]
    #print(verse_line)
    #parser = ReferenceParser()
    #parser.start(verse_line)
    #print([str(s) for s in parser.references])


if __name__ == "__main__":
    main()
