from selenium import webdriver
from gensim.models import KeyedVectors
import sys
import time, math, random
import numpy as np
from bot_reddit import send_message_to_reddit, test_reddit_creds

class Cemantix_Solver:
    def __init__(self, vector_model:KeyedVectors,no_ui:bool, cemantle:bool, browser:str, threshold:float):
        self.model = vector_model
        self.no_ui = no_ui
        self.cemantle = cemantle
        self.browser = browser
        self.threshold = threshold
        self.website_name = "cemantix" if not self.cemantle else "cemantle"
        self.driver = self.setup_driver()
        self.input = self.driver.find_element('id', self.website_name + '-guess')
        self.minimal_temp = self.get_minimal_temp()
        self.highest_score = -10000
        self.closest_dist = -1
        self.TEMPERATURE_FACTOR_THRESHOLD = 10_000
        self.NO_TEMP = -100
        self.ENDGAME_TEMP = 965
        self.ENDGAME_THRESHOLD = 40
        self.ONLY_1000s_THRESHOLD = 300
        self.highest_words = {}
        self.idx_in_file = 0
        self.tested_words = []
        self.submitted_words = []
        self.words_file = self.read_file("pedantix-principaux.txt")
    def get_temperature_threshold(self):
        if self.closest_dist < 0:
            return 0
        return self.TEMPERATURE_FACTOR_THRESHOLD // pow(self.closest_dist,0.7)
    def get_minimal_temp(self):
        minimal_temp = self.driver.find_element('id', self.website_name + "-summary")
        minimal_temp = minimal_temp.text.splitlines(keepends=False)
        minimal_temp = [m for m in minimal_temp if m.startswith("1 ")][0]
        return float(minimal_temp.split(" ")[2].replace(",", "."))
    def read_file(self, filename:str):
        with open(filename, "r", encoding="utf-8") as words:
            word_list = [w.strip() for w in words.readlines()]
        return word_list
    def compute_highest_words(self,all_words: list[str]) -> dict[float, (str,int)]:
        print("[LOG] Computing best words...")
        highests_dict = {}
        threshold = self.get_temperature_threshold()
        print(f"[LOG] Threshold : {threshold}")
        for entry in all_words:
            word_tested = entry.split(" ")
            if len(word_tested) < 3:
                continue
            score = float(word_tested[2].replace(",", ".") if not word_tested[2] == '' else "-1")
            temperature = int(word_tested[4] if (len(word_tested) >= 5 and word_tested[4] != '') else str(self.NO_TEMP))
            if self.closest_dist >= self.ENDGAME_TEMP:
                if math.fabs(self.closest_dist - temperature) < self.ENDGAME_THRESHOLD:
                    highests_dict[score] = (word_tested[1], temperature)
            elif self.closest_dist >= self.ONLY_1000s_THRESHOLD:
                if temperature != self.NO_TEMP:
                    highests_dict[score] = (word_tested[1], temperature)
            elif (self.closest_dist >= 0 and self.closest_dist - temperature < 200) or \
                    (self.highest_score - score < self.threshold * self.highest_score):
                highests_dict[score] = (word_tested[1], temperature)
        # highests = [value for key, value in sorted(highests_dict.items(), reverse=True)]
        print("[LOG] The best word(s) : ", highests_dict)
        return highests_dict



    def randomize_vector(self, vector: np.ndarray, impact:int) -> np.ndarray:
        for i in range(vector.shape[0] * impact // 100):
            vector[random.randint(0, vector.shape[0] - 1)] *= 1 + random.randint(-impact,impact)/ 10
        return vector

    def new_random_word(self,last_vector: np.ndarray, all_words: str):
        last_vector_copy = last_vector.copy()
        sim_word = self.model.most_similar(last_vector)[0][0]
        i = 0
        while abs(self.model.similarity(self.model.most_similar(last_vector_copy)[0][0], sim_word)) > 0.08 \
                or abs(self.model.similarity(all_words, sim_word)) > 0.08 \
                or self.model.most_similar(last_vector, topn=1)[0][0].strip() in self.tested_words:
            last_vector[random.randint(0, last_vector.shape[0] - 1)] += 0.5
            last_vector[random.randint(0, last_vector.shape[0] - 1)] -= 0.5
            last_vector *= -1
            sim_word = self.model.most_similar(last_vector)[0][0]
            print(f"done {i}")
            i += 1
        return self.model.most_similar(last_vector)[0][0]
    def next_word_midgame(self, score_temperature_word: list[(float,int,str)], topn:int) -> str:
        words = [i[2] for i in score_temperature_word]
        temps = [i[1] for i in score_temperature_word]
        if self.NO_TEMP in temps:
            weights = [i[0] for i in score_temperature_word]
        else:
            weights = [i[1]**2 for i in score_temperature_word]
        vector = vector_model.get_mean_vector(words, weights=weights)
        if random.randint(0, 4) == 0:
            vector = self.randomize_vector(vector, impact=random.randint(1, 5))
        new_words = self.model.most_similar(positive=vector, topn=topn)
        best_shot = ""
        for word, score in new_words:
            if word in self.tested_words:
                continue
            best_shot = word
            break
        return best_shot
    def is_good_word(self, score_temperature_word, sim_words) -> bool:
        for stw in score_temperature_word:
            if stw[2] in sim_words:
                return True
        return False
    def next_word_endgame(self, score_temperature_word: list[(float,int,str)], topn:int) -> str:
        new_words = self.model.most_similar(positive=[i[2] for i in score_temperature_word], topn=topn)
        best_shot = ""
        for word, score in new_words:
            if word in self.tested_words:
                continue
            if self.closest_dist > 975:
                new_topn = (1000 - self.closest_dist) * 2
            else:
                new_topn = 20
            sim_words = [w[0] for w in self.model.most_similar(word, topn=new_topn)]
            if self.is_good_word(score_temperature_word, sim_words):
                best_shot = word
                break
        return best_shot

    def next_words(self, last_random_vector: np.ndarray,topn: int = 30) -> str:
        if self.highest_score > self.minimal_temp-5:
            score_temperature_word = [(k, v[1], v[0]) for k, v in self.highest_words.items()]
            if self.closest_dist < self.ENDGAME_TEMP:
                best_shot = self.next_word_midgame(score_temperature_word, topn=topn)
            else:
                best_shot = self.next_word_endgame(score_temperature_word, topn=topn)
            if best_shot != "":
                return best_shot
            if self.closest_dist > 700 or self.idx_in_file == len(self.words_file):
                return self.next_words(last_random_vector, topn=int(topn * 1.5))
        if self.idx_in_file != len(self.words_file):
            word = self.words_file[self.idx_in_file]
            self.idx_in_file += 1
            return word
        if len(self.submitted_words) > 2:
            mean_word = self.model.most_similar(self.model.get_mean_vector(self.submitted_words))[0][0]
        else:
            mean_word = np.zeros(last_random_vector.shape)
            mean_word[random.randint(0, last_random_vector.shape[0] - 1)] = 1.
            mean_word = self.model.most_similar(mean_word)[0][0]
        return self.new_random_word(last_random_vector, mean_word)


    def setup_driver(self):
        if self.browser == "firefox":
            if self.no_ui:
                opt = webdriver.FirefoxOptions()
                opt.add_argument('-headless')
                driver = webdriver.Firefox(options=opt)
            else:
                driver = webdriver.Firefox()
        elif self.browser == "edge":
            if self.no_ui:
                opt = webdriver.EdgeOptions()
                opt.add_argument('--headless')
                driver = webdriver.Edge(options=opt)
            else:
                driver = webdriver.Edge()
        elif self.browser == "safari":
            if self.no_ui:
                print("ERROR : Safari can't be run without UI, sorry :(")
                sys.exit(0)
            else:
                driver = webdriver.Safari()
        elif self.browser == "chrome":
            if self.no_ui:
                opt = webdriver.ChromeOptions()
                opt.add_argument('--headless')
                driver = webdriver.Chrome(options=opt)
            else:
                driver = webdriver.Chrome()
        else:
            print("Error : unrecognized browser...")
            sys.exit(0)
        driver.get('https://' + self.website_name + '.certitudes.org')
        driver.find_element('id', 'dialog-close').click()
        return driver


    def solve(self):
        won = False
        while not won:
            ran_vector = np.zeros(self.model.vector_size)
            ran_vector[random.randint(0, ran_vector.shape[0] - 1)] = random.randrange(-1, 1)
            ran_vector[random.randint(0, ran_vector.shape[0] - 1)] = random.randrange(-1, 1)
            word = self.next_words(ran_vector)
            self.tested_words.append(word)
            self.input.send_keys(word)
            self.input.send_keys(webdriver.Keys.ENTER)
            print("[LOG] Trying a new word : ", word)
            time.sleep(0.3)
            if self.driver.find_element('id', self.website_name + '-error').text != "":
                print(f"[WARNING] Word not found")
                continue
            self.submitted_words.append(word)
            last_guess = self.driver.find_element('id', self.website_name + "-guessed")
            table = self.driver.find_element('id', self.website_name + "-guesses")
            splitted = last_guess.text.split(" ")
            if len(splitted) >= 2:
                while splitted[2] == '':
                    time.sleep(0.2)
                    last_guess = self.driver.find_element('id', self.website_name + "-guessed")
                    splitted = last_guess.text.split(" ")
                if len(splitted) > 4 and splitted[4] != '' and int(splitted[4]) > self.closest_dist:
                    self.closest_dist = int(splitted[4])
                if self.closest_dist == 1000:
                    won = True
                last_guess_score = float(splitted[2].replace(",", "."))
                print("[LOG] Last Guess : " + last_guess.text, " , Score : ", last_guess_score)
                if last_guess_score > self.highest_score:
                    print("[LOG] Found a better word !! ")
                    self.highest_score = last_guess_score
                words_to_compute = table.text.split("\n")
                words_to_compute.append(last_guess.text)
                self.highest_words = self.compute_highest_words(words_to_compute)
        time.sleep(0.5)
        self.driver.find_element('id', self.website_name + '-see').click()
        time.sleep(1)
        all_words = [element.split(" ")[1] if element.split(" ")[0].isdigit() else element.split(" ")[0] for element in
                     self.driver.find_element('id', self.website_name + '-guesses').text.split("\n")]
        # driver.quit()
        return all_words


if __name__ == '__main__':
    possible_args = ["--help", "--reddit", "--no-ui", "--vector-file", "--cemantle", "--browser"]
    args_with_postfix = [possible_args[3], possible_args[5]]
    browser_args = ["firefox", "safari", "chrome", "edge"]
    arguments = sys.argv[1:]
    for i, a in enumerate(arguments):
        if a not in possible_args and i != 0 and arguments[i - 1] not in args_with_postfix:
            print("ERROR : Unrecognized argument :", a)
            sys.exit(0)
    if possible_args[0] in arguments:
        print(
            """HELP : This script lets you automatically find the word of the day from the game cémantix or cemantle: 
            https://cemantix.certitudes.org
            https://cemantle.certitudes.org
ARGUMENTS :
--help : shows you this page
--reddit : Sends some hints to the daily reddit page (please do not spam it!)
--no-ui : Launches the browser without graphical interface
--browser : Chooses the browser to use (default is firefox) (possibilities : firefox, chrome, edge, safari)
--cemantle : Uses cemantle instead of cemantix (be careful to use an english word2vec file)
--vector-file : Select the name of the pretrained word2vec file you want to use (default is frWac_no_postag_no_phrase_700_skip_cut50.bin)""")
        sys.exit(0)
    if possible_args[3] in arguments:
        idx = arguments.index(possible_args[3])
        if idx == len(arguments):
            print(
                "ERROR : You need to give the name of the word2vec file if you want to use another one than the default")
            sys.exit(0)
        filename = arguments[idx + 1]
    else:
        filename = "frWac_no_postag_no_phrase_700_skip_cut50.bin"
    if possible_args[5] in arguments:
        if (idx := arguments.index(possible_args[5])) == len(arguments):
            print(
                "ERROR : You need to specify the browser name if you specify the --browser argument"
            )
            sys.exit(0)
        if (browser := arguments[idx + 1]) not in browser_args:
            print(
                "ERROR : Unrecognized browser : " + browser + "  (expected " + str(browser) + ")"
            )
            sys.exit(0)
    else:
        browser = "chrome"
    vector_model = KeyedVectors.load_word2vec_format(filename, binary=True, unicode_errors="ignore")
    if possible_args[1] in arguments:
        test_reddit_creds()
    solver = Cemantix_Solver(vector_model=vector_model, no_ui=possible_args[2] in arguments, threshold=0.03,
                 cemantle=possible_args[4] in arguments, browser=browser)
    words = solver.solve()
    if possible_args[1] in arguments:
        send_message_to_reddit(words)
