"""This file contains the sm for the cli menu"""
import os
import pathlib
from abc import ABC
from enum import Enum, auto
from typing import Type, Dict, Union, Tuple

from exceptions.sm_exceptions import NextTransitionException
from search_engines.registry import SearchEngineFactory
from search_engines.search_engine_interface import SearchEngineInterface
from utils.download_urls import download_urls
from webscraper_config import Config


def clear():
    """Clears the screen on command line"""
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def press_any_key():  # pylint: disable=C0116
    input("Press any key to continue")


class Transitions(Enum):
    """Enumeration for Transitions"""
    NEXT = auto()
    PREVIOUS = auto()
    CURRENT = auto()
    MAIN_MENU = auto()
    END = auto()


class State(ABC):
    """ABC of a state in the sm"""

    def __init__(self, config: Config):
        """Callback should be called after the state has done its work."""
        self.config = config

        self.generic_answers = {
            "main": Transitions.MAIN_MENU,
            "prev": Transitions.PREVIOUS,
            "next": Transitions.NEXT,
        }

        clear()

    def run(self) -> Transitions:
        """Impl of what the state is doing"""
        raise NotImplementedError

    def _check_next_criteria(self):
        pass

    def check_for_generic_answer(self, user_input: str) -> Transitions | None:
        """Check if user is entering a command like prev, next, main etc..."""
        if (clean_input := user_input.strip(" ").rstrip(" ")) in self.generic_answers:
            transition = self.generic_answers.get(clean_input)
            if transition is Transitions.NEXT:
                self._check_next_criteria()
            return transition
        return None


class MainMenu(State):
    """Main State of the SM"""
    def __init__(self, config: Config):
        # This State is implemented with a mapping of functions because it makes it easier to read
        # and cleans up the run function quite a bit
        super().__init__(config=config)

        self.option_mapping = {
            "1": ("Create new config", self.create_new_config),
            "2": ("Print current config", self.print_current_config),
            "3": ("Export current config", self.export_current_config),
            "4": ("Load saved config", self.load_config),
            "5": ("Start scraping", self.scrape),
            "quit": ("Exit the program", self.quit)
        }

    @staticmethod
    def create_new_config():
        """Begin process of creation of webscraper config"""
        return Transitions.NEXT

    def print_current_config(self):
        """Print the config"""
        print("Current config is: ")
        print(self.config.to_json())
        press_any_key()
        return Transitions.CURRENT

    def export_current_config(self):
        """Exports the config as config.json"""
        self.config.save_config(pathlib.Path("./config.json"))
        return Transitions.CURRENT

    def load_config(self):
        """Loads config from current directory"""
        self.config.load_config(pathlib.Path("./config.json"))
        return Transitions.CURRENT

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
        return Transitions.CURRENT

    @staticmethod
    def quit():
        """Transition to final state"""
        return Transitions.END

    def run(self):
        print("Main Menu: ")
        for key, value in self.option_mapping.items():
            print(f"{key}. {value[0]}")

        answer = input("Choice: ")
        while answer not in self.option_mapping.keys():
            print(f"{answer} is not a valid choice")
            answer = input("Choice: ")

        return self.option_mapping.get(answer)[1]()


class PromptForDownloadPath(State):
    """State to ask for a path to download the scraped images to"""

    def run(self) -> Transitions:
        print("Enter a path to download your dataset to")
        path = input("Path: ")
        if (transition := self.check_for_generic_answer(path)) is not None:
            return transition

        self.config.dataset_path = path
        return Transitions.NEXT


class PromptForKeywords(State):
    """State to ask for keywords to use in the search"""

    def __init__(self, config: Config):
        super().__init__(config)

        self.generic_answers[""] = Transitions.NEXT  # empty string can be treated as generic answer
        self.keywords = set("")

    def _check_next_criteria(self):
        if not self.keywords:
            raise NextTransitionException("Enter at least one keyword")
        self.config.keywords = list(self.keywords)

    def run(self) -> Transitions:
        print("Type the keywords you want to search for.")
        print("When you are done press Enter")
        while True:
            _keyword = input("Keyword: ")
            try:
                if (transition := self.check_for_generic_answer(_keyword)) is not None:
                    return transition
            except NextTransitionException as ex:
                print(ex)
                continue
            self.keywords.add(_keyword)


class PromptForTranslation(State):
    """State to ask if keywords should be translated"""

    def run(self) -> Transitions:
        no_answers = ["no", "n", "NO", ""]
        yes_answers = ["yes", "y"]

        while True:
            print("Should your keywords be translated?")
            answer = input("yes | NO")
            if (transition := self.check_for_generic_answer(answer)) is not None:
                return transition

            if answer in no_answers:  # answer is no
                self.config.translations = None
                return Transitions.NEXT
            if answer not in yes_answers:  # answer is not yes so it has to be invalid
                print("Answer is not a valid choice!")
                continue
            return self._translate()

    def _translate(self) -> Transitions:
        # Import the translator here because it makes an internet connection which would be rather
        # useless if the user doesn't want to translate at all
        from deep_translator import GoogleTranslator  # pylint: disable=import-outside-toplevel

        supported_languages = GoogleTranslator().get_supported_languages(as_dict=True)
        translate_to = set("")

        print("Which languages do you want to translate to?")
        print("For a list of valid options type: languages")
        print("When done press Enter")
        while True:
            answer = input("Language code or Country name: ")

            if (transition := self.check_for_generic_answer(answer)) is not None:
                return transition

            if not answer:
                if not translate_to:
                    return Transitions.NEXT
                break
            if answer == "languages":
                for key, value in supported_languages.items():
                    print(f"{key} = {value}")
                continue
            if answer not in supported_languages and answer not in supported_languages.values():
                print(f"{answer} is not a supported language")
                continue
            translate_to.add(answer)

        translations = []
        for language in translate_to:
            for keyword in self.config.keywords:
                translations.append(GoogleTranslator(source="auto", target=language).
                                    translate(keyword))
        self.config.translations = translations
        return Transitions.NEXT


class PromptForNSamples(State):
    """State to get the number of samples to use per keyword"""

    def __init__(self, config: Config):
        super().__init__(config)
        self.n_samples = None

    def _check_next_criteria(self):
        if self.n_samples is None or not self.n_samples.isdigit() or int(self.n_samples) <= 0:
            raise NextTransitionException("Enter a valid number of samples!")
        self.config.n_samples = int(self.n_samples)

    def run(self) -> Transitions:
        while True:
            print("How many samples (per keyword) should be downloaded?")
            self.n_samples = input("Number of samples: ")

            try:
                if (transition := self.check_for_generic_answer(self.n_samples)) is not None:
                    return transition
                self._check_next_criteria()
                return Transitions.NEXT
            except NextTransitionException as ex:
                print(ex)
                continue


class PromptForSearchEngine(State):
    """State to get the Search Engines to use"""

    def __init__(self, config: Config):
        super().__init__(config)

        self.generic_answers[""] = Transitions.NEXT  # empty string can be treated as generic answer
        self.search_engines_to_use = set("")

    def _check_next_criteria(self):
        if not self.search_engines_to_use:
            raise NextTransitionException("Select at least one search engine!")
        self.config.search_engines = list(self.search_engines_to_use)

    def run(self) -> Transitions:
        valid_options = [str(i) for i in range(0, SearchEngineFactory.get_number_of_ses())]
        valid_options.append("")

        while True:
            print("Select the search Engines to use")
            print("When done press Enter")

            for count, name in enumerate(SearchEngineFactory.get_names()):
                print(f"{'[x]' if name in self.search_engines_to_use else '[ ]'}  {count}. {name}")

            answer = input("Number: ")
            try:
                if (transition := self.check_for_generic_answer(answer)) is not None:
                    return transition
            except NextTransitionException as ex:
                print(ex)
                continue

            if answer not in valid_options:
                print("Answer is not valid")
                print(f"Options are: {valid_options}")
                continue

            search_engine = SearchEngineFactory.get_names()[int(answer)]
            if search_engine not in self.search_engines_to_use:
                self.search_engines_to_use.add(search_engine)
            else:
                self.search_engines_to_use.remove(search_engine)


class Done(State):
    """State to Signal that the configuration step is complete"""
    def run(self) -> Transitions:
        print("Configuration is done")
        self.config.pretty_print()
        press_any_key()
        return Transitions.MAIN_MENU


class WebscraperStateMachine:  # pylint: disable=too-few-public-methods
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
        transition = None
        while transition is not Transitions.END:
            transition = self.current_state(config=self._config).run()
            self._next(transition=transition)

    def _next(self, transition: Transitions):
        """
        This will transition to the next state in the transition table. It is used as the
        callback for the state class
        The default next state is MainMenu because you can return from any menu to main by entering
        main. So this way you don't have to implement the transition in the transition table.
        """
        next_state = self.transition_table.get((self.current_state, transition), MainMenu)
        self.current_state = next_state
