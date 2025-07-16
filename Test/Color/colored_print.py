from colorama import Fore, Style, init

init(autoreset=True)

class ColorPrint:
    COLORS = {
        'red': Fore.RED,
        'green': Fore.GREEN,
        'yellow': Fore.YELLOW,
        'blue': Fore.BLUE,
        'magenta': Fore.MAGENTA,
        'cyan': Fore.CYAN,
        'white': Fore.WHITE
    }

    @staticmethod
    def print(text, color='white', bold=False):
        color_code = ColorPrint.COLORS.get(color.lower(), Fore.WHITE)
        style = Style.BRIGHT if bold else Style.NORMAL
        print(f"{style}{color_code}{text}")

    @staticmethod
    def print_error(text):
        error_color = ColorPrint.COLORS['red']
        print(f"{Style.BRIGHT}{error_color}[ERROR]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_success(text):
        success_color = ColorPrint.COLORS['green']
        print(f"{Style.BRIGHT}{success_color}[SUCCESS]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_warning(text):
        warning_color = ColorPrint.COLORS['yellow']
        print(f"{Style.BRIGHT}{warning_color}[WARNING]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_info(text):
        info_color = ColorPrint.COLORS['blue']
        print(f"{Style.BRIGHT}{info_color}[INFO]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_debug(text):
        debug_color = ColorPrint.COLORS['magenta']
        print(f"{Style.BRIGHT}{debug_color}[DEBUG]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_step(text, step_number=None):
        """Affiche une étape avec un numéro et une couleur cyan"""
        step_color = ColorPrint.COLORS['cyan']
        if step_number:
            print(f"{Style.BRIGHT}{step_color}[STEP {step_number}]{Style.RESET_ALL} {text}")
        else:
            print(f"{Style.BRIGHT}{step_color}[STEP]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_result(text):
        """Affiche un résultat avec une couleur cyan"""
        result_color = ColorPrint.COLORS['cyan']
        print(f"{Style.BRIGHT}{result_color}[RESULT]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_header(text):
        """Affiche un header avec une couleur blanche en gras"""
        header_color = ColorPrint.COLORS['white']
        print(f"\n{Style.BRIGHT}{header_color}{'='*60}")
        print(f"{Style.BRIGHT}{header_color}{text.center(60)}")
        print(f"{Style.BRIGHT}{header_color}{'='*60}{Style.RESET_ALL}")

    @staticmethod
    def print_separator(char='-', length=60):
        """Affiche un séparateur"""
        separator_color = ColorPrint.COLORS['white']
        print(f"{separator_color}{char*length}{Style.RESET_ALL}")

    @staticmethod
    def print_cost(text):
        """Affiche des informations de coût en jaune"""
        cost_color = ColorPrint.COLORS['yellow']
        print(f"{Style.BRIGHT}{cost_color}[COST]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_performance(text):
        """Affiche des informations de performance en magenta"""
        perf_color = ColorPrint.COLORS['magenta']
        print(f"{Style.BRIGHT}{perf_color}[PERF]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_api(text):
        """Affiche des informations d'API en cyan"""
        api_color = ColorPrint.COLORS['cyan']
        print(f"{Style.BRIGHT}{api_color}[API]{Style.RESET_ALL} {text}")