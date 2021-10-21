"""This file contains the sm for the cli menu"""
import os
import pathlib
import time
from abc import ABC
from enum import Enum, auto
from typing import Callable, Type, Dict, Union, Tuple

from search_engines.registry import SearchEngineFactory
from search_engines.search_engine_interface import SearchEngineInterface
from webscraper_config import Config as WsConfig
from utils.download_urls import download_urls


def clear():
    """Clears the screen on command line"""
    os.system("clear")


def press_any_key():  # pylint: disable=C0116
    input("Press any key to continue")


class Transitions(Enum):
    """Enumeration for Transitions"""
    NEXT = auto()
    PREVIOUS = auto()
    CURRENT = auto()
    MAIN_MENU = auto()


class State(ABC):
    """ABC of a state in the sm"""

    def __init__(self, config: WsConfig, callback: Callable):
        """Callback should be called after the state has done its work."""
        self.config = config
        self.callback = callback

        self.generic_answers = {
            "main": Transitions.MAIN_MENU,
            "prev": Transitions.PREVIOUS,
            "next": Transitions.NEXT,
        }

        clear()
        self.run()

    def run(self):
        """Impl of what the state is doing"""
        raise NotImplementedError

    def check_for_generic_answer(self, user_input: str) -> bool:
        """Check if user is entering a command like prev, next, main etc..."""
        if (clean_input := user_input.strip(" ").rstrip(" ")) in self.generic_answers:
            self.callback(self.generic_answers.get(clean_input))
            return True
        return False


class MainMenu(State):
    """Main State of the DFA"""
    def __init__(self, config: WsConfig, callback: Callable):
        # This State is implemented with a mapping of functions because it makes it easier to read
        # and cleans up the run function quite a bit
        self.option_mapping = {
            "1": ("Create new config", self.create_new_config),
            "2": ("Print current config", self.print_current_config),
            "3": ("Export current config", self.export_current_config),
            "4": ("Load saved config", self.load_config),
            "5": ("Start scraping", self.scrape),
            "quit": ("Exit the program", exit)
        }
        super().__init__(config=config, callback=callback)

    def create_new_config(self):
        """Begin process of creation of webscraper config"""
        self.callback(Transitions.NEXT)

    def print_current_config(self):
        """Print the config"""
        print("Current config is: ")
        print(self.config.to_json())
        press_any_key()
        self.callback(Transitions.CURRENT)

    def export_current_config(self):
        """Exports the config as config.json"""
        self.config.save_config(pathlib.Path("./config.json"))
        self.callback(Transitions.CURRENT)

    def load_config(self):
        """Loads config from current directory"""
        self.config.load_config(pathlib.Path("./config.json"))
        self.callback(Transitions.CURRENT)

    def scrape(self):
        """
        Starts the scraping process by getting the search engine implementation and initializing it
        """
        config = self.config.to_json()
        n_samples = config.get("n_samples")
        for search_engine in config.get("search_engines"):
            for keyword in config.get("keywords"):
                concrete_search_engine: SearchEngineInterface = \
                    SearchEngineFactory.get_se(search_engine, keyword=keyword, n_images=n_samples)
                download_urls(pathlib.Path(self.config.dataset_path),
                              concrete_search_engine.get_img_urls())
        press_any_key()
        self.callback(Transitions.CURRENT)

    def run(self):
        print("Main Menu: ")
        for key, value in self.option_mapping.items():
            print(f"{key}. {value[0]}")

        answer = input("Choice: ")
        while answer not in self.option_mapping.keys():
            print(f"{answer} is not a valid choice")
            answer = input("Choice: ")

        self.option_mapping.get(answer)[1]()


class PromptForDownloadPath(State):
    """State to ask for a path to download the scraped images to"""
    def run(self):
        print("Enter a path to download your dataset to")
        answer = input("Path: ")
        if self.check_for_generic_answer(answer):
            return

        self.config.dataset_path = answer
        self.callback(Transitions.NEXT)


class PromptForKeywords(State):
    """State to ask for keywords to use in the search"""
    def run(self):
        keywords = set("")

        print("Type the keywords you want to search for.")
        print("When you are done press Enter")
        while True:
            key_word = input("Keyword: ")
            if self.check_for_generic_answer(key_word):
                return
            if not key_word:
                break
            keywords.add(key_word)
            print(f"Keywords are: {keywords}")

        self.config.keywords = list(keywords)
        self.callback(Transitions.NEXT)


class PromptForTranslation(State):
    """State to ask if keywords should be translated"""
    def run(self):
        no_answers = ["no", "n", ""]
        yes_answers = ["yes", "y"]

        print("Should your keywords be translated?")
        print("To get back to the previous screen you can write prev")
        answer = input("(yes | NO): ").lower()
        if self.check_for_generic_answer(answer):
            return

        while answer not in yes_answers + no_answers:
            print(f"{answer} is not a valid choice, try again!")
            answer = input("(yes | NO): ").lower()
            if self.check_for_generic_answer(answer):
                return

        if answer in no_answers:
            self.config.translations = None
            self.callback(Transitions.NEXT)
            return

        # Import the translator here because it makes an internet connection which would be rather
        # useless if the user doesn't want to translate at all
        from deep_translator import GoogleTranslator  # pylint: disable=import-outside-toplevel

        supported_languages = GoogleTranslator().get_supported_languages(as_dict=True)
        translate_to = set("")

        print("Which languages do you want to translate to? Enter the language code")
        print("When done press Enter")
        while True:
            answer = input("Language code: ")
            if not answer:
                break
            if answer not in supported_languages and answer not in supported_languages.values():
                print(f"{answer} is not a supported language")
                continue
            translate_to.add(answer)

        if not translate_to or not self.config.keywords:
            # check if the user left one of those empty
            self.config.translations = None
        else:
            translations = []
            for language in translate_to:
                for keyword in self.config.keywords:
                    translations.append(GoogleTranslator(source="auto", target=language).
                                        translate(keyword))
            self.config.translations = translations
        self.callback(Transitions.NEXT)


class PromptForNSamples(State):
    """State to get the number of samples to use"""
    def run(self):
        while True:
            print("How many samples should be downloaded?")
            answer = input("number of samples: ")
            if self.check_for_generic_answer(answer):
                return

            if not answer.isdigit():
                print("This has to be an integer!\n")
            else:
                self.config.n_samples = int(answer)
                self.callback(Transitions.NEXT)
                return


class PromptForSearchEngine(State):
    """State to get the Search Engines to use"""
    def run(self):
        search_engines_to_use = set("")
        valid_options = [str(i) for i in range(0, SearchEngineFactory.get_number_of_ses())]
        valid_options.append("done")
        valid_options.append("")

        while True:
            clear()
            print("Select the search Engines to use")

            for count, name in enumerate(SearchEngineFactory.get_names()):
                print(f"{'[x]' if name in search_engines_to_use else '[ ]'}  {count}. {name}")

            answer = input("Number: ")

            while answer not in valid_options:
                print("Answer is not valid")
                print(f"Options are: {valid_options}")
                answer = input("Number: ")

            if not answer or answer == "done":
                if len(search_engines_to_use) < 1:
                    print("You have to select at least one search engine")
                    time.sleep(1)
                else:
                    self.config.search_engines = list(search_engines_to_use)
                    self.callback(Transitions.NEXT)
                    return
            else:
                search_engine = SearchEngineFactory.get_names()[int(answer)]
                if search_engine not in search_engines_to_use:
                    search_engines_to_use.add(search_engine)
                else:
                    search_engines_to_use.remove(search_engine)


class Done(State):
    """State to Signal that the configuration step is complete"""
    def run(self):
        print("Configuration is done")
        press_any_key()
        self.callback(Transitions.MAIN_MENU)


class WebscraperDfa:
    """State machine for gathering information from the user"""

    def __init__(self):
        self._config = WsConfig()
        self.initial_state: Type[State] = MainMenu
        self.current_state: Union[Type[State], None] = None

        self.transition_table: Dict[Tuple[Type[State], Transitions], Type[State]] = {
            # State = MainMenu
            (MainMenu, Transitions.NEXT): PromptForDownloadPath,
            (MainMenu, Transitions.CURRENT): MainMenu,

            # State = PromptForDownloadPath
            (PromptForDownloadPath, Transitions.NEXT): PromptForKeywords,
            (PromptForDownloadPath, Transitions.PREVIOUS): MainMenu,

            # State = PromptForKeywords
            (PromptForKeywords, Transitions.NEXT): PromptForTranslation,
            (PromptForKeywords, Transitions.PREVIOUS): PromptForDownloadPath,

            # State = PromptForTranslation
            (PromptForTranslation, Transitions.NEXT): PromptForNSamples,
            (PromptForTranslation, Transitions.PREVIOUS): PromptForKeywords,

            # State = PromptForNSamples
            (PromptForNSamples, Transitions.NEXT): PromptForSearchEngine,
            (PromptForNSamples, Transitions.PREVIOUS): PromptForTranslation,

            # State = PromptForSearchEngine
            (PromptForSearchEngine, Transitions.NEXT): Done,
            (PromptForSearchEngine, Transitions.PREVIOUS): PromptForNSamples,
        }

    def start(self):
        """Starts the sm. First state is the initial state"""
        self.current_state = self.initial_state
        self.initial_state(config=self._config, callback=self.next)

    def next(self, transition: Transitions):
        """
        This will transition to the next state in the transition table. It is used as the
        callback for the state class
        The default next state is MainMenu because you can return from any menu to main by entering
        main. So this way you don't have to implement the transition in the transition table.
        """
        next_state = self.transition_table.get((self.current_state, transition), MainMenu)
        self.current_state = next_state
        self.current_state(config=self._config, callback=self.next)
