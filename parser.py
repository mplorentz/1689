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

