import sys
from src.logger import logger


def error_message_detail(error, error_detail: sys) -> str:
    """
    Extracts filename, line number, and error message from sys traceback.
    """
    _, _, exc_tb = error_detail.exc_info()
    if exc_tb is not None:
        file_name = exc_tb.tb_frame.f_code.co_filename
        line_number = exc_tb.tb_lineno
        error_message = (
            f"Error occurred in script [{file_name}] "
            f"at line [{line_number}]: {str(error)}"
        )
    else:
        error_message = str(error)
    return error_message


class MedicalBotException(Exception):
    """
    Custom exception class for Medical Chatbot application.
    """
    def __init__(self, error_message, error_detail: sys):
        super().__init__(str(error_message))
        self.error_message = error_message_detail(error_message, error_detail=error_detail)
        logger.error(self.error_message)

    def __str__(self):
        return self.error_message
