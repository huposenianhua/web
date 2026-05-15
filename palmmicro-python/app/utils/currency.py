"""Multi-currency conversion utility.

Translated from PHP class/multi_currency.php.
Handles CNY/HKD/USD conversions for cross-market stock analysis.
"""


class MultiCurrency:
    """Hold amounts in CNY, HKD, USD and convert between them."""

    def __init__(self) -> None:
        self.cny: float = 0.0
        self.hkd: float = 0.0
        self.usd: float = 0.0

        self.convert_cny: float = 0.0
        self.convert_hkd: float = 0.0
        self.convert_usd: float = 0.0

    def convert(self, usd_cny: float | None = None, hkd_cny: float | None = None) -> None:
        """Convert all amounts to CNY, then derive USD and HKD equivalents.

        Args:
            usd_cny: USD to CNY exchange rate
            hkd_cny: HKD to CNY exchange rate
        """
        self.convert_cny = self.cny
        if usd_cny is not None:
            self.convert_cny += self.usd * float(usd_cny)
        if hkd_cny is not None:
            self.convert_cny += self.hkd * float(hkd_cny)

        self.convert_usd = self.convert_cny / float(usd_cny) if usd_cny else 0.0
        self.convert_hkd = self.convert_cny / float(hkd_cny) if hkd_cny else 0.0
