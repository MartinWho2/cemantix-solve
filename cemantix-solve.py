from selenium import webdriver
from gensim.models import KeyedVectors
import sys
import time, math, random
import numpy as np
from bot_reddit import send_message_to_reddit, test_reddit_creds


def compute_highest_words(all_words: list[str], highest_score: float, threshold: float) -> dict[float, str]:
    print("[LOG] Computing best words...")
    highests_dict = {}
    highest_score_root = math.sqrt(max(highest_score, 0))
    for entry in all_words:
        word_tested = entry.split(" ")
        if len(word_tested) < 3:
            continue
        if word_tested[2] == "":
            print(all_words)
        score = float(word_tested[2].replace(",", ".") if not word_tested[2] == '' else "-1111.0")
        if (score > 0) and (highest_score_root - math.sqrt(score)) < threshold * highest_score_root:
            highests_dict[score] = word_tested[1]
    # highests = [value for key, value in sorted(highests_dict.items(), reverse=True)]
    print("[LOG] The best word(s) : ", highests_dict)
    return highests_dict


def compute_weighted_mean(vectors: list[numpy.ndarray], scores: list[float]) -> numpy.ndarray:
    vector = numpy.zeros(vectors[0].shape)
    s = sum([a for a in scores])
    weights = [score / s for score in scores]
    for i, v in enumerate(vectors):
        vector += weights[i] * v
    if random.randint(0, 10) == 0:
        vector[random.randint(0, vector.shape[0] - 1)] += 0.2
    return vector


def new_random_word(last_vector: np.ndarray, all_words: str, model: KeyedVectors):
    last_vector_copy = last_vector.copy()
    sim_word = model.most_similar(last_vector)[0][0]
    i= 0
    while abs(model.similarity(model.most_similar(last_vector_copy)[0][0],sim_word)) > 0.08 and abs(model.similarity(all_words,sim_word)) > 0.08 :
        last_vector[random.randint(0, last_vector.shape[0] - 1)] += 0.5
        last_vector[random.randint(0, last_vector.shape[0] - 1)] -= 0.5
        last_vector *= -1
        sim_word = model.most_similar(last_vector)[0][0]
        print(f"done {i}")
        i+=1
    return model.most_similar(last_vector)[0][0]


def next_words(highest_words: dict[float, str], highest_score: int, model: KeyedVectors, idx_next_word_in_file: int,
               words_file: list[str], tested_words: list[str], closest_dist: int, last_random_vector: numpy.ndarray,
               submitted_words:list[str] ,topn: int = 20) -> [str, int]:
    if highest_score > 10:
        new_words = model.most_similar(positive=highest_words, topn=topn)
        i = 0
        found_one = True
        while new_words[i][0] in tested_words:
            i += 1
            if i == len(new_words):
                found_one = False
                break
        if found_one:
            return [new_words[i][0], idx_next_word_in_file]
        if closest_dist > 700 or idx_next_word_in_file == len(words_file):
            return next_words(highest_words, highest_score, model, idx_next_word_in_file, words_file, tested_words,
                              closest_dist, last_random_vector,submitted_words, topn=int(topn * 1.5))
    # word = words_file[idx_next_word_in_file]
    # idx_next_word_in_file += 1
    # return [word, idx_next_word_in_file]
    if len(submitted_words) > 2:
        mean_word = model.most_similar(model.get_mean_vector(submitted_words))[0][0]
    else:
        mean_word = np.zeros(last_random_vector.shape)
        mean_word[random.randint(0,last_random_vector.shape[0]-1)] = 1.
        mean_word = model.most_similar(mean_word)[0][0]
    return [new_random_word(last_random_vector, mean_word, model), idx_next_word_in_file]


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
    highest_words = {}
    idx_in_file = 0
    tested_words = []
    submitted_words = []
    number_guesses = 0
    with open("pedantix-principaux.txt", "r", encoding="utf-8") as words:
        word_list = [w.strip() for w in words.readlines()]
    won = False
    while not won:
        vec = model.get_vector("saucisse")
        ran_vector = np.zeros(vec.shape)
        ran_vector[random.randint(0, ran_vector.shape[0] - 1)] = random.randrange(-1, 1)
        ran_vector[random.randint(0, ran_vector.shape[0] - 1)] = random.randrange(-1, 1)
        word, idx_in_file = next_words(highest_words.copy(), highest_score, model, idx_in_file, word_list, tested_words,
                                       closest_distance, ran_vector, submitted_words)
        tested_words.append(word)
        a.send_keys(word)
        a.send_keys(webdriver.Keys.ENTER)
        print("[LOG] Trying a new word : ", word)
        time.sleep(0.3)
        if driver.find_element('id', 'cemantix-error').text != "":
            print(f"[WARNING] Word not found")
            continue

        last_guess = driver.find_element('id', "cemantix-guessed")
        table = driver.find_element('id', "cemantix-guesses")
        splitted = last_guess.text.split(" ")
        if len(splitted) >= 2:
            while splitted[2] == '':
                time.sleep(0.2)
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
            highest_words = compute_highest_words(words_to_compute, highest_score, threshold)
    time.sleep(0.5)
    driver.find_element('id', 'cemantix-see').click()
    time.sleep(1)
    all_words = [element.split(" ")[1] if element.split(" ")[0].isdigit() else element.split(" ")[0] for element in
                 driver.find_element('id', 'cemantix-guesses').text.split("\n")]
    # driver.quit()
    return all_words


if __name__ == '__main__':
    possible_args = ["--help", "--reddit", "--no-ui", "--vector-file"]
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
            print(
                "ERROR : You need to give the name of the word2vec file if you want to use another one than the default")
            quit()
        filename = arguments[idx + 1]
    else:
        filename = "frWac_no_postag_no_phrase_700_skip_cut50.bin"
    vector_model = KeyedVectors.load_word2vec_format(filename, binary=True, unicode_errors="ignore")
    if possible_args[1] in arguments:
        test_reddit_creds()
    words = main(model=vector_model, no_ui=possible_args[2] in arguments, threshold=0.06)
    if possible_args[1] in arguments:
        send_message_to_reddit(words)
