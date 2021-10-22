"""This file contains the sm for the cli menu"""
import os
import pathlib
from abc import ABC
from enum import Enum, auto
from typing import Callable, Type, Dict, Union, Tuple

from exceptions.state_machine_exceptions import NextCriteriaNotSatisfiedException
from search_engines.registry import SearchEngineFactory
from search_engines.search_engine_interface import SearchEngineInterface
from utils.download_urls import download_urls
from webscraper_config import Config


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

    def __init__(self, config: Config, callback: Callable):
        """Callback should be called after the state has done its work."""
        self.config = config
        self.callback = callback

        self.generic_answers = {
            "main": Transitions.MAIN_MENU,
            "prev": Transitions.PREVIOUS,
            "next": Transitions.NEXT,
        }

        clear()

    def run(self):
        """Impl of what the state is doing"""
        raise NotImplementedError

    def _check_next_criteria(self):
        """
        Use this method to implement checks which have to be passed before continuing.
        """

    def check_for_generic_answer(self, user_input: str) -> bool:
        """Check if user is entering a command like prev, next, main etc..."""
        if (clean_input := user_input.strip(" ").rstrip(" ")) in self.generic_answers:
            transition = self.generic_answers.get(clean_input)
            if transition is Transitions.NEXT:
                self._check_next_criteria()
            self.callback(transition)
            return True
        return False


class MainMenu(State):
    """Main State of the SM"""
    def __init__(self, config: Config, callback: Callable):
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
        self.run()

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
        n_samples = self.config.n_samples
        for search_engine in self.config.search_engines:
            for keyword in self.config.keywords + self.config.translations:
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

    def __init__(self, config: Config, callback: Callable):
        super().__init__(config, callback)
        self.run()

    def run(self):
        print("Enter a path to download your dataset to")
        answer = input("Path: ")
        if self.check_for_generic_answer(answer):
            return

        self.config.dataset_path = answer
        self.callback(Transitions.NEXT)


class PromptForKeywords(State):
    """State to ask for keywords to use in the search"""

    def __init__(self, config: Config, callback: Callable):
        super().__init__(config, callback)
        self.keywords = set("")

        self.run()

    def _check_next_criteria(self):
        if not self.keywords:
            raise NextCriteriaNotSatisfiedException("Enter at least one keyword!")

    def run(self):
        print("Type the keywords you want to search for.")
        print("When you are done press Enter")
        while True:
            key_word = input("Keyword: ")
            try:
                if self.check_for_generic_answer(key_word):
                    return
                if not key_word:
                    self._check_next_criteria()
                    break
            except NextCriteriaNotSatisfiedException as ex:
                print(ex)
                continue

            self.keywords.add(key_word)
            print(f"Keywords are: {self.keywords}")

        self.config.keywords = list(self.keywords)
        self.callback(Transitions.NEXT)


class PromptForTranslation(State):
    """State to ask if keywords should be translated"""

    def __init__(self, config: Config, callback: Callable):
        super().__init__(config, callback)

        self.run()

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

        print("Which languages do you want to translate to?")
        print("For a list of valid options type: languages")
        print("When done press Enter")
        while True:
            answer = input("Language code or country name: ")
            if not answer:
                break
            if answer == "languages":
                for key, value in supported_languages.items():
                    print(f"{key} = {value}")
                continue
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
    """State to get the number of samples to use per keyword"""

    def __init__(self, config: Config, callback: Callable):
        super().__init__(config, callback)
        self.n_samples = None

        self.run()

    def _check_next_criteria(self):
        if self.n_samples is None or not self.n_samples.isdigit() or int(self.n_samples) <= 0:
            raise NextCriteriaNotSatisfiedException("Enter a positive Integer > 0") from None

    def run(self):
        while True:
            print("How many samples (per keyword) should be downloaded?")
            self.n_samples = input("Number of samples: ")

            try:
                if self.check_for_generic_answer(self.n_samples):
                    return
                self._check_next_criteria()
                self.config.n_samples = int(self.n_samples)
                self.callback(Transitions.NEXT)
                break
            except NextCriteriaNotSatisfiedException as ex:
                print(ex)
                continue


class PromptForSearchEngine(State):
    """State to get the Search Engines to use"""

    def __init__(self, config: Config, callback: Callable):
        super().__init__(config, callback)
        self.search_engines_to_use = set("")

        self.run()

    def _check_next_criteria(self):
        if not self.search_engines_to_use:
            raise NextCriteriaNotSatisfiedException("Select at least one search engine") from None

    def run(self):
        valid_options = [str(i) for i in range(0, SearchEngineFactory.get_number_of_ses())]

        while True:
            print("Select the search Engines to use!")
            print("When done press Enter")

            for count, name in enumerate(SearchEngineFactory.get_names()):
                print(f"{'[x]' if name in self.search_engines_to_use else '[ ]'}  {count}. {name}")

            answer = input("Number: ")
            try:
                if self.check_for_generic_answer(answer):
                    return
                if not answer:
                    self._check_next_criteria()
                    break
            except NextCriteriaNotSatisfiedException as ex:
                print(ex)
                continue

            while answer not in valid_options:
                print("Answer is not valid")
                print(f"Options are: {valid_options}")
                answer = input("Number: ")

            # if not answer:
            #     if len(self.search_engines_to_use) < 1:
            #         print("You have to select at least one search engine")
            #     else:
            #         self.config.search_engines = list(self.search_engines_to_use)
            #         self.callback(Transitions.NEXT)
            #         return
            # else:
            search_engine = SearchEngineFactory.get_names()[int(answer)]
            if search_engine not in self.search_engines_to_use:
                self.search_engines_to_use.add(search_engine)
            else:
                self.search_engines_to_use.remove(search_engine)
        self.config.search_engines = list(self.search_engines_to_use)
        self.callback(Transitions.NEXT)


class Done(State):
    """State to Signal that the configuration step is complete"""

    def __init__(self, config: Config, callback: Callable):
        super().__init__(config, callback)

        self.run()

    def run(self):
        print("Configuration is done")
        press_any_key()
        self.callback(Transitions.MAIN_MENU)


class WebscraperStateMachine:
    """State machine for gathering information from the user"""

    def __init__(self):
        self._config = Config()
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
        print(f"Current state: {self.current_state}")
        self.current_state(config=self._config, callback=self.next)
