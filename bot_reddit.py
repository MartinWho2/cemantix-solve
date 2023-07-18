import json

import praw
import dotenv
import random
from datetime import date


def test_reddit_creds() -> praw.Reddit:
    env_vars = dotenv.main.dotenv_values(".env",)
    if env_vars.get("CLIENT_ID") is None or env_vars.get("SECRET") is None or env_vars.get("PASSWORD") is None or env_vars.get(
            "USERNAME") is None:
        print(
            "ERROR : You are attempting to use the reddit bot functionnality without having configured the .env file first.")
        print("        If you didn't create an account for the bot, please follow the instructions here :"
              "https://medium.com/geekculture/creating-a-reddit-bot-with-python-and-praw-185387248a22")
        print("        If you already have one, just create a `.env` file and put your account data in it.")
        raise EnvironmentError
    return  praw.Reddit(
        client_id=env_vars["CLIENT_ID"],
        client_secret=env_vars["SECRET"],
        password=env_vars["PASSWORD"],
        user_agent="cemantix-solver",
        username=env_vars["USERNAME"]
    )


class RedditBot:
    def __init__(self, cemantle:bool, abs_path: str):
        self.reddit = test_reddit_creds()
        self.cemantix_day_0 = date(2022,3,2)
        self.cemantle_day_0 = date(2022,4,4)
        self.cemantle = cemantle
        self.language = "french" if not cemantle else "english"
        self.string_name = ["cémantix", "cemantix"] if not cemantle else ["cemantle"]
        self.title = "Cémantix" if not cemantle else "Cemantle"
        self.abs_path = abs_path
        self.language_messages = self.get_long_texts()


    def send_message_to_reddit(self,best_words: list[str]):
        print(self.reddit.user.me())
        message = self.language_messages["intro_text"]
        best_words = best_words[::-1]
        for i in range(9):
            index = random.randint(1, 100)
            message += str(100 * i + index) + "  >!" + best_words[i * 100 + index - 1] + "!< \n\n"
        for i in range(5):
            index = random.randint(1, 20)
            message += str(900 + 20 * i + index) + "  >!" + best_words[900 + i * 20 + index - 1] + "!< \n\n"
        message += self.language_messages["disclaimer"]
        subreddit = self.reddit.subreddit("cemantix")
        submission = self.find_correct_thread(subreddit)
        if submission is not None:
            submission.reply(message)
        else:
            print("Thread not created yet : creating one...")
            submission = subreddit.submit(title=self.title+" "+ self.transform_current_date_to_number(),
                                          selftext=self.language_messages["title"] + self.language_messages["sitename"])
            submission.reply(message)

    def get_long_texts(self):
        with open(self.abs_path+"bot_messages.json", "r",encoding="utf-8") as f:
            dic = json.load(f)[self.language]
        return dic
    def find_correct_thread(self,subreddit) -> praw.Reddit.submission:
        correct_date = self.transform_current_date_to_number()
        thread = None
        for submission in subreddit.hot(limit=10):
            title = submission.title
            title :str
            title = title.lower()
            if correct_date in title:
                correct_title = False
                for s in self.string_name:
                    if s in title:
                        correct_title = True
                if correct_title:
                    thread = submission
                    break
        return thread
    def transform_current_date_to_number(self) -> str:
        now = date.today()
        if self.cemantle:
            return str((now-self.cemantle_day_0).days)
        return str((now-self.cemantix_day_0).days)