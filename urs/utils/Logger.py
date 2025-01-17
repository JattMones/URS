"""
Log decorators
==============
Decorators that log what is happening behind the scenes to `urs.log`.
"""


import logging
import time

from colorama import (
    init, 
    Fore, 
    Style
)
from prawcore import PrawcoreException

from urs.utils.DirInit import InitializeDirectory
from urs.utils.Global import (
    categories,
    convert_time,
    date,
    short_cat
)
from urs.utils.Titles import Errors

### Automate sending reset sequences to turn off color changes at the end of 
### every print.
init(autoreset = True)

class LogMain():
    """
    Decorator for logging URS runtime. Also handles KeyboardInterrupt and adds the
    event to the log if applicable.
    """

    ### Makes directory in which the log and scraped files will be stored.
    InitializeDirectory.make_directory()

    ### Set directory path and log format.
    DIR_PATH = "../scrapes/%s" % date
    LOG_FORMAT = "[%(asctime)s] [%(levelname)s]: %(message)s"

    ### Configure logging settings.
    logging.basicConfig(
        filename = DIR_PATH + "/urs.log", 
        format = LOG_FORMAT, 
        level = logging.INFO
    )
    
    @staticmethod
    def master_timer(function):
        """
        Wrapper for logging the amount of time it took to execute main(). Handle
        KeyboardInterrupt if user cancels URS.

        Parameters
        ----------
        function: function()
            Run method within the wrapper

        Exceptions
        ----------
        KeyboardInterrupt:
            Raised if user cancels URS

        Returns
        -------
        wrapper: function()
            Return the wrapper method that runs the method passed into the
            decorator
        """

        def wrapper(*args):
            logging.info("INITIALIZING URS.")
            logging.info("")

            start = time.time()
            
            try:
                function(*args)
            except KeyboardInterrupt:
                print(Style.BRIGHT + Fore.RED + "\n\nURS ABORTED BY USER.\n")
                logging.warning("")
                logging.warning("URS ABORTED BY USER.\n")
                quit()

            logging.info("URS COMPLETED IN %.2f SECONDS.\n" % (time.time() - start))

        return wrapper

class LogError():
    """
    Decorator for logging args, PRAW, or rate limit errors.
    """

    @staticmethod
    def log_no_args(function):
        """
        Wrapper for logging if the help message was printed/if no arguments were
        given.

        Parameters
        ----------
        function: function()
            Run method within the wrapper

        Exceptions
        ----------
        SystemExit:
            Raised if no, invalid, or example args were entered 

        Returns
        -------
        wrapper: function()
            Return the wrapper method that runs the method passed into the
            decorator
        """

        def wrapper(self):
            try:
                args, parser = function(self)
                return args, parser
            except SystemExit:
                logging.info("HELP WAS DISPLAYED.\n")
                quit()
        
        return wrapper

    @staticmethod
    def log_args(error):
        """
        Wrapper for logging individual (specific) arg errors.

        Parameters
        ----------
        error: str
            String denoting the specific error that was raised when processing args

        Returns
        -------
        wrapper: function()
            Return the wrapper method that runs the method passed into the
            decorator
        """

        def decorator(function):
            def wrapper(*args):
                try:
                    function(*args)
                except ValueError:
                    Errors.e_title("INVALID %s." % error)
                    logging.critical("RECEIVED INVALID %s." % error)
                    logging.critical("ABORTING URS.\n")
                    quit()

            return wrapper
        return decorator

    @staticmethod
    def log_rate_limit(function):
        """
        Wrapper for logging rate limit and errors.

        Parameters
        ----------
        function: function()
            Run method within the wrapper

        Returns
        -------
        wrapper: function()
            Return the wrapper method that runs the method passed into the
            decorator
        """

        def wrapper(reddit):
            user_limits = function(reddit)

            logging.info("RATE LIMIT DISPLAYED.")
            logging.info("Remaining requests: %s" % int(user_limits["remaining"]))
            logging.info("Used requests: %s" % user_limits["used"])
            logging.info("")

            if int(user_limits["remaining"]) == 0:
                Errors.l_title(convert_time(user_limits["reset_timestamp"]))
                logging.critical("RATE LIMIT REACHED. RATE LIMIT WILL RESET AT %s." % convert_time(user_limits["reset_timestamp"]))
                logging.critical("ABORTING URS.\n")
                quit()
            
            return user_limits
        return wrapper

class LogPRAWScraper():
    """
    Decorator for logging scraper runtimes and events.
    """

    @staticmethod
    def _format_subreddit_log(settings_dict):
        """
        Format Subreddit log message.

        Parameters
        ----------
        settings_dict: dict
            Dictionary containing Subreddit scraping settings

        Returns
        -------
        None
        """

        time_filters = [ 
            "day", 
            "hour", 
            "month", 
            "week", 
            "year"
        ]

        for subreddit_name, settings in settings_dict.items():
            for each_setting in settings:
                if each_setting[2] in time_filters:
                    logging.info("Getting posts from the past %s for %s results." % (each_setting[2], categories[short_cat.index(each_setting[0].upper())]))
                if each_setting[0].lower() != "s":
                    logging.info("Scraping r/%s for %s %s results..." % (subreddit_name, each_setting[1], categories[short_cat.index(each_setting[0].upper())]))
                elif each_setting[0].lower() == "s":
                    logging.info("Searching and scraping r/%s for posts containing '%s'..." % (subreddit_name, each_setting[1]))

                logging.info("")

    @staticmethod
    def _format_two_arg_log(scraper_type, settings_dict):
        """
        Format Redditor or submission comments log message. Both only take two
        arguments, which is why only one method is needed to format the messages.

        Parameters
        ----------
        scraper_type: str
            String denoting the scraper type (Redditors or submission comments)
        settings_dict: dict
            Dictionary containing Redditor scraping settings

        Returns
        -------
        None
        """

        for reddit_object, n_results in settings_dict.items():
            plurality = "results" \
                if int(n_results) > 1 \
                else "result"
            
            if scraper_type == "redditor":
                logging.info("Scraping %s %s for u/%s..." % (n_results, plurality, reddit_object))
            elif scraper_type == "comments":
                logging.info("Processing all comments from Reddit post %s..." % reddit_object) \
                    if int(n_results) == 0 \
                    else logging.info("Processing %s %s from Reddit post %s..." % (n_results, plurality, reddit_object))            

            logging.info("")

    @staticmethod
    def _format_scraper_log(scraper, settings_dict):
        """
        Format log depending on raw or structured export. Calls previously
        defined private methods:

            LogPRAWScraper._format_subreddit_log()
            LogPRAWScraper._format_two_arg_log()

        Parameters
        ----------
        scraper: str
            String denoting the scraper that was run
        settings_dict: dict
            Dictionary containing scrape settings

        Returns
        -------
        None
        """

        if scraper == "subreddit":
            LogPRAWScraper._format_subreddit_log(settings_dict)
        elif scraper == "redditor":
            LogPRAWScraper._format_two_arg_log("redditor", settings_dict)
        elif scraper == "comments":
            LogPRAWScraper._format_two_arg_log("comments", settings_dict)

    @staticmethod
    def scraper_timer(scraper):
        """
        Wrapper for logging the amount of time it took to execute a scraper.

        Parameters
        ----------
        scraper: str
            String denoting the scraper that is run

        Returns
        -------
        decorator: function()
            Return the decorator function that runs the method passed into this
            method
        """

        def decorator(function):
            def wrapper(*args):
                start = time.time()

                logging.info("RUNNING %s SCRAPER." % scraper.upper())
                logging.info("")

                settings_dict = function(*args)

                LogPRAWScraper._format_scraper_log(scraper, settings_dict)

                logging.info("%s SCRAPER FINISHED IN %.2f SECONDS." % (scraper.upper(), time.time() - start))
                logging.info("")

            return wrapper
        return decorator

    @staticmethod
    def log_cancel(function):
        """
        Wrapper for logging if the user cancelled Subreddit scraping at the
        confirmation page.

        Parameters
        ----------
        function: function()
            Run method within the wrapper

        Returns
        -------
        wrapper: function()
            Return the wrapper method that runs the method passed into the
            decorator
        """

        def wrapper(*args):
            try:
                function(*args)
            except KeyboardInterrupt:
                print(Fore.RED + Style.BRIGHT + "\n\nCancelling.\n")
                logging.info("")
                logging.info("SUBREDDIT SCRAPING CANCELLED BY USER.\n")
                quit()
            
        return wrapper

class LogAnalyticsErrors():
    """
    Decorator for logging errors while exporting analytical data.
    """

    @staticmethod
    def log_invalid_top_dir(function):
        """
        Log invalid top directory when running analytical tools.

        Parameters
        ----------
        function: function()
            Run method within the wrapper

        Exceptions
        ----------
        ValueError:
            Raised if the file is not located within the scrapes directory

        Returns
        -------
        wrapper: function()
            Return the wrapper method that runs the method passed into the
            decorator
        """

        def wrapper(*args):
            try:
                return function(*args)
            except ValueError:
                Errors.i_title("Scrape data is not located within the `scrapes` directory.")
                logging.critical("AN ERROR HAS OCCURRED WHILE PROCESSING SCRAPE DATA.")
                logging.critical("Scrape data is not located within the `scrapes` directory.")
                logging.critical("ABORTING URS.\n")
                quit()
            except TypeError:
                Errors.i_title("Invalid file format. Try again with a valid JSON file.")
                logging.critical("AN ERROR HAS OCCURRED WHILE PROCESSING SCRAPE DATA.")
                logging.critical("Invalid file format.")
                logging.critical("ABORTING URS.\n")
                quit()

        return wrapper

class LogAnalytics():
    """
    Decorator for logging analytical tools.
    """

    @staticmethod
    def _get_args_switch(args, tool):
        """
        Get tool type for logging.

        Parameters
        ----------
        args: Namespace
            Namespace object containing all arguments used in the CLI
        tool: str
            Tool type which denotes a key in the dictionary

        Returns
        -------
        scraper_args: list
            List of arguments returned from args
        """

        tools = {
            "frequencies": [arg_set for arg_set in args.frequencies] \
                if args.frequencies \
                else None,
            "wordcloud": [arg_set for arg_set in args.wordcloud] \
                if args.wordcloud \
                else None
        }

        return tools.get(tool)

    @staticmethod
    def log_save(tool):
        """
        Wrapper for logging if the result was saved.

        Parameters
        ----------
        tool: str
            String denoting the tool that is run

        Returns
        -------
        decorator: function()
            Return the decorator function that runs the method passed into this
            method
        """

        def decorator(function):
            def wrapper(*args):
                filename = function(*args)
                
                logging.info("Saved %s to %s." % (tool, filename))
                logging.info("")
                
            return wrapper
        return decorator

    @staticmethod
    def log_show(tool):
        """
        Wrapper for logging if the result was displayed.

        Parameters
        ----------
        tool: str
            String denoting the tool that is run

        Returns
        -------
        decorator: function()
            Return the decorator method that runs the method passed into this
            method
        """

        def decorator(function):
            def wrapper(*args):
                function(*args)
                
                logging.info("Displayed %s." % tool)
                logging.info("")
                
            return wrapper
        return decorator

    @staticmethod
    def _get_export_switch(f_type):
        """
        Get export type for logging.

        Parameters
        ----------
        f_type: str
            String denoting the file type

        Returns
        -------
        export_message: str
            String denoting export option
        """

        export_options = {
            0: "Exporting to JSON.",
            1: "Exporting to CSV."
        }

        if f_type == "csv":
            return export_options.get(1)

        return export_options.get(0)

    @staticmethod
    def log_export(function):
        """
        Log the export format for the frequencies generator.

        Parameters
        ----------
        function: function()
            Run method within the wrapper

        Returns
        -------
        wrapper: function()
            Return the wrapper method that runs the method passed into the
            decorator
        """

        def wrapper(*args):
            try:
                function(*args)

                logging.info(LogAnalytics._get_export_switch(args[1]))
                logging.info("")
            except Exception as e:
                Errors.ex_title(e)
                logging.critical("AN ERROR HAS OCCURRED WHILE EXPORTING SCRAPED DATA.")
                logging.critical("%s" % e)
                logging.critical("ABORTING URS.\n")
                quit()

        return wrapper

    @staticmethod
    def _log_tool(args, tool):
        """
        Log the analytical tool that was used.

        Parameters
        ----------
        args: Namespace
            Namespace object containing all arguments used in the CLI
        tool: str
            String denoting the analytical tool

        Returns
        -------
        None
        """

        args_list = LogAnalytics._get_args_switch(args, tool)

        for file in args_list:
            logging.info("Generating %s for file %s..." % (tool, file[0]))
            logging.info("")

    @staticmethod
    def generator_timer(tool):
        """
        Wrapper for logging the amount of time it took to execute a tool.

        Parameters
        ----------
        tool: str
            String denoting the tool that is run

        Returns
        -------
        decorator: function()
            Return the decorator method that runs the method passed into this
            method
        """

        def decorator(function):
            def wrapper(*args):
                start = time.time()

                logging.info("RUNNING %s GENERATOR." % tool.upper())
                logging.info("")

                LogAnalytics._log_tool(args[0], tool)
                
                function(*args)

                logging.info("%s GENERATOR FINISHED IN %.2f SECONDS." % (tool.upper(), time.time() - start))
                logging.info("")

            return wrapper
        return decorator

class LogExport():
    """
    Decorator for logging exporting files.
    """

    @staticmethod
    def _get_export_switch(args):
        """
        Get export type for logging.

        Parameters
        ----------
        args: Namespace
            Namespace object containing all arguments used in the CLI

        Returns
        -------
        export_message: str
            String denoting export option
        """

        export_options = {
            0: "Exporting to JSON.",
            1: "Exporting to CSV."
        }

        if args.csv:
            return export_options.get(1)

        return export_options.get(0)

    @staticmethod
    def log_export(function):
        """
        Wrapper for logging the export option.

        Parameters
        ----------
        function: function()
            Run method within the wrapper

        Returns
        -------
        wrapper: function()
            Return the wrapper method that runs the method passed into the
            decorator
        """

        def wrapper(*args):
            try:
                function(*args)

                logging.info(LogExport._get_export_switch(args[0]))
                logging.info("")
            except Exception as e:
                Errors.ex_title(e)
                logging.critical("AN ERROR HAS OCCURRED WHILE EXPORTING SCRAPED DATA.")
                logging.critical("%s" % e)
                logging.critical("ABORTING URS.\n")
                quit()

        return wrapper
