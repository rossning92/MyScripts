import random

from utils.menu import Menu

lorem_words = [
    # fmt: off
    "Lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit", "sed", "do",
    "eiusmod", "tempor", "incididunt", "ut", "labore", "et", "dolore", "magna", "aliqua", "Ut", "enim",
    "ad", "minim", "veniam", "quis", "nostrud", "exercitation", "ullamco", "laboris", "nisi", "ut", "aliquip",
    "ex", "ea", "commodo", "consequat", "Duis", "aute", "irure", "dolor", "in", "reprehenderit", "in",
    "voluptate", "velit", "esse", "cillum", "dolore", "eu", "fugiat", "nulla", "pariatur", "Excepteur", "sint",
    "occaecat", "cupidatat", "non", "proident", "sunt", "in", "culpa", "qui", "officia", "deserunt", "mollit",
    "anim", "id", "est", "laborum"
    # fmt: on
]


def generate_lorem_text(
    num_paragraphs=100,
    min_sentences=1,
    max_sentences=3,
    min_words_per_sentence=5,
    max_words_per_sentence=10,
):
    lorem_paragraphs = []
    for _ in range(num_paragraphs):
        num_sentences = random.randint(min_sentences, max_sentences)
        sentences = []
        for _ in range(num_sentences):
            num_words = random.randint(min_words_per_sentence, max_words_per_sentence)
            sentence = " ".join(random.sample(lorem_words, num_words))
            sentences.append(sentence)
        paragraph = " ".join(sentences)
        lorem_paragraphs.append(paragraph)
    return lorem_paragraphs


if __name__ == "__main__":
    menu = Menu(
        items=generate_lorem_text(), prompt="$", debug=True, search_on_enter=True
    )
    menu.exec()
