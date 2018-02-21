from bs4 import BeautifulSoup
import urllib.request
import sys
import re

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

class VerseReference:
    book = None
    start_chapter = None
    end_chapter = None
    start_verse = None
    end_verse = None

    def __str__(self):
        if self.end_chapter is not None:
            return "%s %s:%s-%s:%s" % (self.book, self.start_chapter, self.start_verse, self.end_chapter, self.end_verse)
        elif self.end_verse is not None:
            return "%s %s:%s-%s" % (self.book, self.start_chapter, self.start_verse, self.end_verse)
        elif self.start_verse is None:
            return "%s %s" % (self.book, self.start_chapter)
        else:
            return "%s %s:%s" % (self.book, self.start_chapter, self.start_verse)


    #def __init__(self, book, start_chapter, end_chapter, start_verse, end_verse):
    #    self.book = book
    #    self.start_chapter = start_chapter
    #    self.end_chapter = end_chapter
    #    self.start_verse = start_verse
    #    self.end_verse = end_verse

# A nasty state machine that will process a line of verse references into VerseReference objects.
class ReferenceParser:
    references = []
    source = None
    i = 0
    accumulator = ""
    current_reference = None
    current_book = None
    current_chapter = None

    # The start state, called to start parsing source
    def start(self, source):
        self.source = source.replace(" ", "")
        self.book_start()

    # The state where the char at i is the start of a book name
    def book_start(self):
        self.current_reference = VerseReference()
        char = self.source[self.i]
        if char.isdigit():
            self.accumulator += char
            self.i += 1
        self.book_alpha()

    # The state where the previous char was an alphanumeric part of a book name
    def book_alpha(self):
        char = self.source[self.i]
        if char.isalpha():
            self.accumulator += char
            self.i += 1
            self.book_alpha()
        else:
            self.current_book = self.accumulator
            self.current_reference.book = self.current_book
            self.after_book()

    # The state where the previous char was the last char in a book's name
    def after_book(self):
        char = self.source[self.i]
        self.accumulator = ""

        if char == ".":
            self.i += 1
            
        self.chapter()
        
    # The state where the char at i is a chapter number or the colon right after a chapter number
    def chapter(self):
        #print("chapter. Remaining: %s" % (self.source[self.i:]))

        if self.i >= len(self.source):
            self.current_reference.start_chapter = self.accumulator
            self.end()
            return

        char = self.source[self.i]

        if char.isdigit():
            self.accumulator += char
            self.i += 1
            self.chapter()
        elif char == ":":
            self.current_chapter = self.accumulator
            self.current_reference.start_chapter = self.current_chapter
            self.accumulator = ""
            self.i += 1
            self.start_verse()
        else:
            print("error in chapter state. Remaining string: %s" % (self.source[self.i:]))

    # The state where the char at i is part of the start_verse of a VerseReference or a transition char immediately following the start_verse
    def start_verse(self):
        #print("start_verse. Remaining: %s" % (self.source[self.i:]))

        if self.i >= len(self.source):
            self.current_reference.start_verse = self.accumulator
            self.end()
            return

        char = self.source[self.i]

        if char.isdigit():
            self.accumulator += char
            self.i += 1
            self.start_verse()
        elif char == ",":
            self.current_reference.start_verse = self.accumulator
            self.references.append(self.current_reference)
            self.accumulator = ""
            self.current_reference = VerseReference()
            self.current_reference.book = self.current_book
            self.current_reference.start_chapter = self.current_chapter
            self.i += 1
            self.verse_or_chapter()
        elif char == "-":
            self.current_reference.start_verse = self.accumulator
            self.accumulator = ""
            self.i += 1
            self.end_verse_or_chapter()
        elif char == ";":
            self.current_reference.start_verse = self.accumulator
            self.accumulator = ""
            self.i += 1
            self.book_or_chapter()
        else:
            print("error in start_verse state. Remaining string: %s" % (self.source[self.i:]))

    # The state where the char at i is part of a number that could be a chapter or verse number
    # e.g. the number following a ','
    def verse_or_chapter(self):
        if self.i >= len(self.source):
            self.current_reference.start_verse = self.accumulator
            self.end()
            return

        char = self.source[self.i]

        if char.isdigit():
            self.accumulator += char
            self.i += 1
            self.verse_or_chapter()
        if char == ":":
            self.current_chapter = self.accumulator
            self.current_reference.start_chapter = self.current_chapter
            self.accumulator = ""
            self.i += 1
            self.start_verse()
        if char == ";":
            self.current_reference.start_verse = self.accumulator
            self.accumulator = ""
            self.i += 1
            self.book_or_chapter()
        else:
            print("error in verse_or_chapter state. Remaining string: %s" % (self.source[self.i:]))


    # The state where the char at i is part of the verse or chapter number that is on the right side of a "-". i.e the "3" in "John 1:2-3"
    def end_verse_or_chapter(self):
        if self.i >= len(self.source):
            self.current_reference.end_verse = self.accumulator
            self.end()
            return

        char = self.source[self.i]

        if char.isdigit():
            self.accumulator += char
            self.i += 1
            self.start_verse()
        elif char == ";":
            self.current_reference.end_verse = self.accumulator
            self.accumulator = ""
            self.i += 1
            self.book_or_chapter()
        elif char == ":":
            self.current_reference.end_chapter = self.accumulator
            self.accumulator = ""
            self.i += 1
            self.end_verse_or_chapter()
        elif char == ",":
            self.current_reference.end_verse = self.accumulator
            self.accumulator = ""
            self.i += 1
            self.start_verse()
        else:
            print("error in end_verse_or_chapter state. Remaining string: %s" % (self.source[self.i:]))

    # The state where the char at i is part of the token following a ';' meaning that we expect it to be the beginning of a book name or chapter number 
    def book_or_chapter(self):
        if self.i >= len(self.source):
            self.current_reference.end_verse = self.accumulator
            self.end()
            return

        char = self.source[self.i]

        if char.isdigit():
            self.accumulator += char
            self.i += 1
            self.book_or_chapter()
        elif char.isalpha():
            self.references.append(self.current_reference)
            self.current_reference = VerseReference()
            self.accumulator += char
            self.i += 1
            self.book_alpha()
        elif char == ":":
            self.current_reference.start_chapter = self.accumulator
            self.accumulator = ""
            self.i += 1
            self.start_verse()
        else:
            print("error in book_or_chapter state. Remaining string: %s" % (self.source[self.i:]))


    #  The state where the end of the source has been reached
    def end(self):
        self.references.append(self.current_reference)
        return


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
