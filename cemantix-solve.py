from selenium import webdriver
from gensim.models import KeyedVectors
import time


def compute_highest_words(words: list[str], highest_score: float, threshold: float = 10.0) -> list[str]:
    print("[LOG] Computing best words...")
    highests = []
    MAX_WORDS = 8
    for entry in words:
        word = entry.split(" ")
        if len(word) < 3:
            continue
        print("[LOG]     Testing word : ", word,end=". ")
        print("[LOG]     Distance is : ",highest_score - float(word[2].replace(",", ".")), " , threshold : ",threshold)
        if (highest_score - float(word[2].replace(",", "."))) < threshold:
            highests.append(word[1])
    if len(highests) > MAX_WORDS:
        return compute_highest_words(words, highest_score, threshold * 0.8)
    print("[LOG] The best word(s) : ", highests)
    return highests


def next_words(highest_words: list, highest_score: int, model: KeyedVectors, idx_next_word_in_file: int,
               words_file: list[str], words: list[str]):
    TOPN = 10
    if highest_score > 15:
        new_words = model.most_similar(positive=highest_words,topn=TOPN)
        i = 0
        found_one = True
        while new_words[i][0] in words:
            i += 1
            if i == len(new_words):
                found_one = False
                break
        if found_one:
            return [new_words[i][0],idx_next_word_in_file]

    word = words_file[idx_next_word_in_file]
    idx_next_word_in_file += 1
    return [word[:word.find(" ")] , idx_next_word_in_file]

opt = webdriver.FirefoxOptions()
opt.add_argument('-headless')
driver = webdriver.Firefox(options=opt)
driver.get('https://cemantix.certitudes.org')
driver.find_element('id', 'dialog-close').click()
a = driver.find_element('id', 'cemantix-guess')
model = KeyedVectors.load_word2vec_format("frWac_no_postag_no_phrase_700_skip_cut50.bin", binary=True,
                                          unicode_errors="ignore")
highest_score = -10000
highest_words = []
idx_in_file = 0
tested_words = []
with open("pedantix-principaux.txt", "r") as words:
    word_list = words.readlines()

for i in range(20):
    word, idx_in_file = next_words(highest_words,highest_score,model,idx_in_file,word_list,tested_words)
    tested_words.append(word)
    a.send_keys(word)
    a.send_keys(webdriver.Keys.ENTER)
    print("[LOG] Trying a new word : ",word)
    print(driver.find_element('id','cemantix-error').text)
    if driver.find_element('id','cemantix-error').text != "":
        print(f"[WARNING] Word not found")
        continue
    time.sleep(0.4)
    last_guess = driver.find_element('id', "cemantix-guessed")
    table = driver.find_element('id', "cemantix-guesses")
    last_guess_score = float(last_guess.text.split(" ")[2].replace(",", "."))
    print("[LOG] Last Guess : " + last_guess.text, " , Score : ", last_guess_score)
    if last_guess_score > highest_score:
        print("[LOG] Found a better word !! ")
        highest_score = last_guess_score
        words_to_compute = table.text.split("\n")
        words_to_compute.append(last_guess.text)
        highest_words = compute_highest_words(words_to_compute, highest_score)