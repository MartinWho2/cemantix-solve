import praw
import dotenv
import random

def test_reddit_creds():
    env_vars = dotenv.main.dotenv_values(".env",)
    if env_vars.get("CLIENT_ID") is None or env_vars.get("SECRET") is None or env_vars.get("PASSWORD") is None or env_vars.get(
            "USERNAME") is None:
        print(
            "ERROR : You are attempting to use the reddit bot functionnality without having configured the .env file first.")
        print("        If you didn't create an account for the bot, please follow the instructions here :"
              "https://medium.com/geekculture/creating-a-reddit-bot-with-python-and-praw-185387248a22")
        print("        If you already have one, just create a `.env` file and put your account data in it.")
        quit()
def send_message_to_reddit(best_words: list[str]):
    env_vars = dotenv.main.dotenv_values(".env")
    reddit = praw.Reddit(
        client_id=env_vars["CLIENT_ID"],
        client_secret=env_vars["SECRET"],
        password=env_vars["PASSWORD"],
        user_agent="cemantix-solver",
        username=env_vars["USERNAME"]
    )
    print(reddit.user.me())
    message = "Voici les indices du jour !\n\n"
    best_words = best_words[::-1]
    for i in range(9):
        index = random.randint(1, 100)
        message += str(100 * i + index) + "  >!" + best_words[i * 100 + index - 1] + "!< \n\n"
    for i in range(5):
        index = random.randint(1, 20)
        message += str(900 + 20 * i + index) + "  >!" + best_words[900 + i * 20 + index - 1] + "!< \n\n"
    message += """Disclaimer : Je suis un bot dont le but est d'empêcher les gens de rester bloqués trop longtemps au jeu et d'être trop frustré. Si vous jugez que ça va contre l'esprit du jeu, répondez au commentaire et j'enlèverai le bot. """
    print(message)

    submission = reddit.submission(url="https://www.reddit.com/r/cemantix/comments/14877xg/c%C3%A9mantix_468/")
    submission.reply(message)
