from selenium import webdriver
from gensim.models import KeyedVectors
import matplotlib.pyplot as plt
import time, math


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


def setup_driver():
    #opt = webdriver.FirefoxOptions()
    #opt.add_argument('-headless')
    driver = webdriver.Firefox()
    driver.get('https://cemantix.certitudes.org')
    driver.find_element('id', 'dialog-close').click()
    return driver


def main(model: KeyedVectors, threshold: float = 0.06):
    driver = setup_driver()
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
        #while driver.find_element('id', 'cemantix-error').text == "" and \
        #        driver.find_element("id","cemantix-guessed").text == last_guess.text:
        #    time.sleep(0.1)
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
    print(all_words)
    driver.quit()
    return number_guesses

if __name__ == '__main__':
    vector_model = KeyedVectors.load_word2vec_format("frWac_no_postag_no_phrase_700_skip_cut50.bin", binary=True,
                                              unicode_errors="ignore")
    """tests = [0.075,0.1,0.125,0.15,0.175,0.2,0.225,0.25]
    tests2 = [0.06,0.065,0.07,0.075,0.08,0.085,0.09,0.095,0.1]
    tests3 = [0.04,0.045,0.05,0.055,0.06]
    results = []
    for i in tests3:
        results.append(main(vector_model, i))
    print(results)
    plt.plot(tests3,results)
    plt.ylabel("Nombre de coups")
    plt.xlabel("Tolérance de détection")
    plt.show()"""
    main(model=vector_model)
