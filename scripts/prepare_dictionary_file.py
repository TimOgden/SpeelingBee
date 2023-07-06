import os
import sys
import pathlib


def remove_short_words(words: list[str]) -> list[str]:
    return [word for word in words if len(word) > 3]


def remove_punctuation_words(words: list[str]) -> list[str]:
    return [word for word in words if word.isalpha()]


def primary_words(words: list[str]) -> list[str]:
    return [word for word in words if len(set(word)) == 7]


def create_files(path: pathlib.Path) -> None:
    with open(path, 'r') as f:
        words = [d.replace('\n', '') for d in f.readlines()]
    words = remove_short_words(words)
    words = remove_punctuation_words(words)

    primary = primary_words(words)
    with open(os.path.join(os.path.dirname(path), os.path.splitext(path.name)[0] + '_words.txt'), 'w') as f:
        f.write(','.join(words))
    with open(os.path.join(os.path.dirname(path), os.path.splitext(path.name)[0] + '_primary.txt'), 'w') as f:
        f.write(','.join(primary))


def main():
    filename = pathlib.Path(sys.argv[1])
    create_files(filename)


if __name__ == '__main__':
    main()
