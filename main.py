"""main script to start scraping"""
import sys

from state_machine import WebscraperStateMachine


def main():
    """Main function"""
    state_machine = WebscraperStateMachine()
    try:
        state_machine.start()
    except KeyboardInterrupt:  # exit gracefully
        sys.exit(0)


if __name__ == '__main__':
    main()
