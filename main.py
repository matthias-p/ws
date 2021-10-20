"""main script to start scraping"""

from state_machine import WebscraperDfa


def main():
    """Main function"""
    sm = WebscraperDfa()
    sm.start()


if __name__ == '__main__':
    main()
