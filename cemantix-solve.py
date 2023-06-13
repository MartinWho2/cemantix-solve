from selenium import webdriver
from gensim.models import KeyedVectors
import sys
import time, math
from bot_reddit import send_message_to_reddit, test_reddit_creds

def compute_highest_words(words: list[str], highest_score: float, threshold: float) -> list[str]:
    print("[LOG] Computing best words...")
    highests_dict = {}
    highest_score_root = math.sqrt(highest_score)
    for entry in words:
        word_tested = entry.split(" ")
        if len(word_tested) < 3:
            continue
        if word_tested[2] == "":
            print(words)
        score = float(word_tested[2].replace(",", "."))
        if (score > 0) and (highest_score_root - math.sqrt(score)) < threshold * highest_score_root:
            highests_dict[score] = word_tested[1]
    highests = [value for key, value in sorted(highests_dict.items(), reverse=True)]
    print("[LOG] The best word(s) : ", highests)
    return highests


def next_words(highest_words: list, highest_score: int, model: KeyedVectors, idx_next_word_in_file: int,
               words_file: list[str], words: list[str], closest_dist: int, topn: int = 20) -> [str, int]:
    if highest_score > 10:
        new_words = model.most_similar(positive=highest_words, topn=topn)
        i = 0
        found_one = True
        while new_words[i][0] in words:
            i += 1
            if i == len(new_words):
                found_one = False
                break
        if found_one:
            return [new_words[i][0], idx_next_word_in_file]
        if closest_dist > 700 or idx_next_word_in_file == len(words_file):
            return next_words(highest_words, highest_score, model, idx_next_word_in_file, words_file, words,
                              closest_dist, topn=int(topn * 1.5))
    word = words_file[idx_next_word_in_file]
    idx_next_word_in_file += 1
    return [word, idx_next_word_in_file]


def setup_driver(no_ui):
    if no_ui:
        opt = webdriver.FirefoxOptions()
        opt.add_argument('-headless')
        driver = webdriver.Firefox(options=opt)
    else:
        driver = webdriver.Firefox()
    driver.get('https://cemantix.certitudes.org')
    driver.find_element('id', 'dialog-close').click()
    return driver


def main(model: KeyedVectors, no_ui: bool, threshold: float = 0.06):
    driver = setup_driver(no_ui)
    a = driver.find_element('id', 'cemantix-guess')
    highest_score = -10000
    closest_distance = -1
    highest_words = []
    idx_in_file = 0
    tested_words = []
    number_guesses = 0
    with open("pedantix-principaux.txt", "r", encoding="utf-8") as words:
        word_list = [w.strip() for w in words.readlines()]
    won = False
    while not won:
        word, idx_in_file = next_words(highest_words.copy(), highest_score, model, idx_in_file, word_list, tested_words,
                                       closest_distance)
        tested_words.append(word)
        a.send_keys(word)
        a.send_keys(webdriver.Keys.ENTER)
        print("[LOG] Trying a new word : ", word)
        time.sleep(0.3)
        if driver.find_element('id', 'cemantix-error').text != "" :
            print(f"[WARNING] Word not found")
            continue

        last_guess = driver.find_element('id', "cemantix-guessed")
        table = driver.find_element('id', "cemantix-guesses")
        splitted = last_guess.text.split(" ")
        if len(splitted) >= 2:
            while splitted[2] == '':
                time.sleep(0.5)
                last_guess = driver.find_element('id', "cemantix-guessed")
                splitted = last_guess.text.split(" ")
            if len(splitted) > 4 and splitted[4] != '' and int(splitted[4]) > closest_distance:
                closest_distance = int(splitted[4])
            if closest_distance == 1000:
                won = True
                word_victory = word
                number_guesses = int(splitted[0])
            last_guess_score = float(splitted[2].replace(",", "."))
            print("[LOG] Last Guess : " + last_guess.text, " , Score : ", last_guess_score)
            if last_guess_score > highest_score:
                print("[LOG] Found a better word !! ")
                highest_score = last_guess_score
            words_to_compute = table.text.split("\n")
            words_to_compute.append(last_guess.text)
            highest_words = compute_highest_words(words_to_compute, highest_score,threshold)
    time.sleep(0.5)
    driver.find_element('id', 'cemantix-see').click()
    time.sleep(1)
    all_words = [element.split(" ")[1] if element.split(" ")[0].isdigit() else element.split(" ")[0] for element in
                 driver.find_element('id', 'cemantix-guesses').text.split("\n")]
    driver.quit()
    return all_words


if __name__ == '__main__':
    possible_args = ["--help","--reddit", "--no-ui","--vector-file"]
    arguments = sys.argv[1:]
    if possible_args[0] in arguments:
        print(
            """HELP : This script lets you automatically find the word of the day from the game cémantix : https://cemantix.certitudes.org              
ARGUMENTS :
--help : shows you this page
--reddit : Sends some hints to the daily reddit page (please do not spam it!)
--no-ui : Launches the browser without graphical interface
--vector-file : Select the name of the pretrained word2vec file you want to use (default is frWac_no_postag_no_phrase_700_skip_cut50.bin)""")
        quit()
    if possible_args[3] in arguments:
        idx = arguments.index(possible_args[3])
        if idx == len(arguments):
            print("ERROR : You need to give the name of the word2vec file if you want to use another one than the default")
            quit()
        filename = arguments[idx+1]
    else:
        filename = "frWac_no_postag_no_phrase_700_skip_cut50.bin"
    vector_model = KeyedVectors.load_word2vec_format(filename, binary=True, unicode_errors="ignore")
    if possible_args[1] in arguments:
        test_reddit_creds()
    words = main(model=vector_model, no_ui=possible_args[2] in arguments)
    if possible_args[1] in arguments:
        send_message_to_reddit(words)
