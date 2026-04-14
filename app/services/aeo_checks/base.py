from abc import ABC, abstractmethod
from app.models.schemas import CheckResult


class BaseCheck(ABC):
    """
    Abstract base class for all AEO checks.
    Every check must implement the run() method.
    """

    @abstractmethod
    def run(self, soup, plain_text: str) -> CheckResult:
        """
        Run the check and return a CheckResult.

        Args:
            soup: BeautifulSoup parsed HTML object
            plain_text: Plain text extracted from content

        Returns:
            CheckResult with score, details, and recommendation
        """
        pass