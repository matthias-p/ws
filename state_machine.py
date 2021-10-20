"""This file contains the sm for the cli menu"""
import json
import time
from abc import ABC
from enum import Enum, auto
from typing import Callable, Type, Dict, Union, Tuple
import os

from search_engines.registry import SearchEngineFactory


def clear():
    """Clears the screen on command line"""
    os.system("clear")


class Transitions(Enum):
    """Enumeration for Transitions"""
    NEXT = auto()
    PREVIOUS = auto()
    CURRENT = auto()
    MAIN_MENU = auto()


class State(ABC):
    """ABC of a state in the sm"""

    def __init__(self, callback: Callable):
        """Callback should be called after the state has done its work."""
        self.callback = callback
        clear()
        self.run()

    def run(self):
        """Impl of what the state is doing"""
        raise NotImplementedError

    def main(self):
        """Callback to Main Menu"""
        self.callback(Transitions.MAIN_MENU)


class MainMenu(State):
    """Main State of the DFA"""
    def __init__(self, callback: Callable):
        self.option_mapping = {
            "1": ("Create new config", self.create_new_config),
            "2": ("Print current config", self.print_current_config),
            "3": ("Export current config", self.export_current_config),
            "4": ("Load saved config", self.load_config),
            "quit": ("Exit the program", exit)
        }
        super().__init__(callback=callback)

    def create_new_config(self):
        """Begin process of creation of webscraper config"""
        self.callback(Transitions.NEXT)

    def print_current_config(self):
        """Print the config"""
        print("Current config is: ")
        print(WebscraperDfa.get_config())
        input("Press any key to continue")
        self.callback(Transitions.CURRENT)

    def export_current_config(self):
        """Exports the config as config.json"""
        with open("config.json", "w", encoding="utf-8") as config_file:
            json.dump(WebscraperDfa.get_config(), config_file)
        self.callback(Transitions.CURRENT)

    def load_config(self):
        """Loads config from current directory"""
        with open("config.json", "r", encoding="utf-8") as config_file:
            WebscraperDfa.load_config(json.load(config_file))
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


class PromptForKeywords(State):
    """State to ask for keywords to use in the search"""
    def run(self):
        keywords = set("")

        print("Type the keywords you want to search for.")
        print("When you are done press Enter")
        while True:
            key_word = input("Keyword: ")
            if not key_word:
                break
            if key_word == "main":
                self.main()
            if key_word == "prev":
                self.callback(Transitions.PREVIOUS)
                return
            keywords.add(key_word)
            print(f"Keywords are: {keywords}")

        WebscraperDfa.KEYWORDS = list(keywords)
        self.callback(Transitions.NEXT)


class PromptForTranslation(State):
    """State to ask if keywords should be translated"""
    def run(self):
        print("Should your keywords be translated?")
        print("To get back to the previous screen you can write prev")
        answer = input("(yes | NO | prev): ").lower()
        while answer not in ["yes", "no", "prev", ""]:
            print(f"{answer} is not a valid choice, try again!")
            answer = input("(yes | NO | prev): ").lower()

        if answer == "prev":
            self.callback(Transitions.PREVIOUS)
        if not answer or answer == "no":
            self.callback(Transitions.NEXT)

        # TODO implement translation of keywords


class PromptForNSamples(State):
    """State to get the number of samples to use"""
    def run(self):
        print("How many samples should be downloaded?")
        answer = input("Samples: ")
        while not answer.isdigit():
            print("This has to be an int")
            answer = input("Samples: ")

        WebscraperDfa.N_SAMPLES = int(answer)
        self.callback(Transitions.NEXT)


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
                    WebscraperDfa.SEARCH_ENGINES = list(search_engines_to_use)
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
        print("Press any key to return to the main menu")
        self.callback(Transitions.MAIN_MENU)


class WebscraperDfa:
    """State machine for gathering information from the user"""

    KEYWORDS = None
    TRANSLATIONS = None
    N_SAMPLES = None
    SEARCH_ENGINES = None

    def __init__(self):
        self.initial_state: Type[State] = MainMenu
        self.current_state: Union[Type[State], None] = None

        self.transition_table: Dict[Tuple[Type[State], Transitions], Type[State]] = {
            # State = MainMenu
            (MainMenu, Transitions.NEXT): PromptForKeywords,
            (MainMenu, Transitions.CURRENT): MainMenu,

            # State = PromptForKeywords
            (PromptForKeywords, Transitions.NEXT): PromptForTranslation,
            (PromptForKeywords, Transitions.PREVIOUS): MainMenu,

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
        self.initial_state(callback=self.next)

    def next(self, transition: Transitions):
        """
        This will transition to the next state in the transition table. It is used as the
        callback for the state class
        The default next state is MainMenu because you can return from any menu to main by entering
        main. So this way you don't have to implement the transition in the transition table.
        """
        next_state = self.transition_table.get((self.current_state, transition), MainMenu)
        self.current_state = next_state
        self.current_state(callback=self.next)

    @classmethod
    def get_config(cls) -> dict:
        """Returns the current config as dict"""
        return {
            "keywords": cls.KEYWORDS,
            "translations": cls.TRANSLATIONS,
            "n_samples": cls.N_SAMPLES,
            "search_engines": cls.SEARCH_ENGINES
        }

    @classmethod
    def load_config(cls, config: dict):
        """Loads the current config from a dict"""
        cls.KEYWORDS = config.get("keywords")
        cls.TRANSLATIONS = config.get("translations")
        cls.N_SAMPLES = config.get("n_samples")
        cls.SEARCH_ENGINES = config.get("search_engines")
