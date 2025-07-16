"""
Centralized Color Printing System for the entire project
This is the single source of truth for all color output across the project.
"""

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    # Fallback - no colors
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = ""
    
    class Style:
        BRIGHT = NORMAL = RESET_ALL = ""

class ColorPrint:
    """
    Centralized color printing class for the entire project.
    Provides consistent color output across all modules.
    """
    
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
        """Basic colored print with optional bold"""
        color_code = ColorPrint.COLORS.get(color.lower(), Fore.WHITE)
        style = Style.BRIGHT if bold else Style.NORMAL
        print(f"{style}{color_code}{text}")

    @staticmethod
    def print_error(text):
        """Print error messages in red"""
        error_color = ColorPrint.COLORS['red']
        print(f"{Style.BRIGHT}{error_color}[ERROR]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_success(text):
        """Print success messages in green"""
        success_color = ColorPrint.COLORS['green']
        print(f"{Style.BRIGHT}{success_color}[SUCCESS]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_warning(text):
        """Print warning messages in yellow"""
        warning_color = ColorPrint.COLORS['yellow']
        print(f"{Style.BRIGHT}{warning_color}[WARNING]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_info(text):
        """Print info messages in blue"""
        info_color = ColorPrint.COLORS['blue']
        print(f"{Style.BRIGHT}{info_color}[INFO]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_debug(text):
        """Print debug messages in magenta"""
        debug_color = ColorPrint.COLORS['magenta']
        print(f"{Style.BRIGHT}{debug_color}[DEBUG]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_step(text, step_number=None):
        """Print step messages in cyan"""
        step_color = ColorPrint.COLORS['cyan']
        if step_number:
            print(f"{Style.BRIGHT}{step_color}[STEP {step_number}]{Style.RESET_ALL} {text}")
        else:
            print(f"{Style.BRIGHT}{step_color}[STEP]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_result(text):
        """Print result messages in cyan"""
        result_color = ColorPrint.COLORS['cyan']
        print(f"{Style.BRIGHT}{result_color}[RESULT]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_cost(text):
        """Print cost information in yellow"""
        cost_color = ColorPrint.COLORS['yellow']
        print(f"{Style.BRIGHT}{cost_color}[COST]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_performance(text):
        """Print performance information in magenta"""
        perf_color = ColorPrint.COLORS['magenta']
        print(f"{Style.BRIGHT}{perf_color}[PERF]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_api(text):
        """Print API information in blue"""
        api_color = ColorPrint.COLORS['blue']
        print(f"{Style.BRIGHT}{api_color}[API]{Style.RESET_ALL} {text}")

    @staticmethod
    def print_header(text):
        """Print header text in bold white"""
        print(f"{Style.BRIGHT}{Fore.WHITE}{'=' * len(text)}")
        print(f"{Style.BRIGHT}{Fore.WHITE}{text}")
        print(f"{Style.BRIGHT}{Fore.WHITE}{'=' * len(text)}")

    @staticmethod
    def print_separator(char='-', length=50):
        """Print a separator line"""
        print(f"{Style.BRIGHT}{Fore.WHITE}{char * length}")

# Convenience alias
cp = ColorPrint

# Specialized logging functions for common use cases
def log_intent_analysis(intent, speciality=None, confidence=None):
    """Log specialized for intent analysis"""
    cp.print_result(f"Intention détectée: {intent}")
    if speciality:
        cp.print_result(f"Spécialité: {speciality}")
    if confidence:
        cp.print_result(f"Confiance: {confidence:.2f}")

def log_document_retrieval(count, total=None):
    """Log specialized for document retrieval"""
    if total:
        cp.print_result(f"Documents récupérés: {count}/{total}")
    else:
        cp.print_result(f"Documents récupérés: {count}")

def log_token_cost(cost_usd, tokens, operations=None):
    """Log specialized for token costs"""
    cp.print_cost(f"Coût total: ${cost_usd:.4f} ({tokens} tokens)")
    if operations:
        for op in operations:
            cp.print_cost(f"  {op.get('operation', 'N/A')}: {op.get('total_tokens', 0)} tokens (${op.get('cost_usd', 0):.4f})")

def log_performance(operation, duration_seconds):
    """Log specialized for performance"""
    cp.print_performance(f"{operation}: {duration_seconds:.2f}s")

def log_api_call(method, endpoint, status_code=None):
    """Log specialized for API calls"""
    if status_code:
        cp.print_api(f"{method} {endpoint} - Status: {status_code}")
    else:
        cp.print_api(f"{method} {endpoint}")

# Export everything
__all__ = [
    'ColorPrint', 'cp', 'COLORAMA_AVAILABLE',
    'log_intent_analysis', 'log_document_retrieval', 
    'log_token_cost', 'log_performance', 'log_api_call'
]
