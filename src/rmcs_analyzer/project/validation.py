from dataclasses import dataclass
from datetime import datetime


@dataclass
class ValidationResult:
    """
    Result of validating a single metadata field.
    """

    valid: bool
    value: object = None
    message: str = ""


class MetadataValidator:
    """
    Validates editable motor-test metadata.

    This class performs no UI work. It converts user-entered
    text into typed values suitable for TestModel.
    """

    # =============================================================
    # TEXT
    # =============================================================

    @staticmethod
    def text(
        value: str,
    ) -> ValidationResult:
        """
        Validate a general optional text field.

        Empty text is valid and is stored as an empty string.
        """

        return ValidationResult(
            valid=True,
            value=value.strip(),
        )

    # =============================================================
    # TEST NUMBER
    # =============================================================

    @staticmethod
    def test_number(
        value: str,
    ) -> ValidationResult:
        """
        Validate a test number.

        Test numbers are stored as text so values such as
        '010' retain their leading zeros.
        """

        value = value.strip()

        return ValidationResult(
            valid=True,
            value=value,
        )

    # =============================================================
    # DATE
    # =============================================================

    @staticmethod
    def test_date(
        value: str,
    ) -> ValidationResult:
        """
        Validate an optional test date.

        The user-facing format is:

            M-D-YYYY

        Both one-digit and two-digit months/days are accepted.

        Examples:

            1-26-2026
            01-26-2026
            12-5-2026
            12-05-2026

        Empty input is valid and becomes an empty string.
        """

        value = value.strip()

        if not value:
            return ValidationResult(
                valid=True,
                value="",
            )

        # Require exactly three hyphen-separated components.
        parts = value.split("-")

        if len(parts) != 3:
            return ValidationResult(
                valid=False,
                value=None,
                message=(
                    "Date must use M-D-YYYY format."
                ),
            )

        month_text, day_text, year_text = parts

        # Month and day may be one or two digits.
        if not (
            month_text.isdigit()
            and 1 <= len(month_text) <= 2
        ):
            return ValidationResult(
                valid=False,
                value=None,
                message=(
                    "Date must use M-D-YYYY format."
                ),
            )

        if not (
            day_text.isdigit()
            and 1 <= len(day_text) <= 2
        ):
            return ValidationResult(
                valid=False,
                value=None,
                message=(
                    "Date must use M-D-YYYY format."
                ),
            )

        # Year must be exactly four digits.
        if not (
            year_text.isdigit()
            and len(year_text) == 4
        ):
            return ValidationResult(
                valid=False,
                value=None,
                message=(
                    "Date must use M-D-YYYY format."
                ),
            )

        try:
            parsed_date = datetime.strptime(
                f"{int(month_text):02d}-"
                f"{int(day_text):02d}-"
                f"{year_text}",
                "%m-%d-%Y",
            )

        except ValueError:
            return ValidationResult(
                valid=False,
                value=None,
                message=(
                    "Enter a valid calendar date."
                ),
            )

        # Preserve the user's preferred M-D-YYYY style
        # while normalizing away unnecessary leading zeros.
        normalized_value = (
            f"{parsed_date.month}-"
            f"{parsed_date.day}-"
            f"{parsed_date.year}"
        )

        return ValidationResult(
            valid=True,
            value=normalized_value,
        )

    # =============================================================
    # POSITIVE NUMBER
    # =============================================================

    @staticmethod
    def positive_number(
        value: str,
        field_name: str,
        allow_zero: bool = False,
    ) -> ValidationResult:
        """
        Validate an optional positive numeric field.

        Empty input is valid and becomes None.

        Parameters
        ----------
        value:
            User-entered text.

        field_name:
            Human-readable field name used in error messages.

        allow_zero:
            Whether zero is considered a valid value.
        """

        value = value.strip()

        if not value:
            return ValidationResult(
                valid=True,
                value=None,
            )

        try:
            number = float(value)

        except ValueError:
            return ValidationResult(
                valid=False,
                value=None,
                message=(
                    f"{field_name} must be a number."
                ),
            )

        if allow_zero:
            if number < 0:
                return ValidationResult(
                    valid=False,
                    value=None,
                    message=(
                        f"{field_name} cannot be negative."
                    ),
                )

        else:
            if number <= 0:
                return ValidationResult(
                    valid=False,
                    value=None,
                    message=(
                        f"{field_name} must be greater than zero."
                    ),
                )

        return ValidationResult(
            valid=True,
            value=number,
        )

    # =============================================================
    # MOTOR DIMENSIONS
    # =============================================================

    @classmethod
    def motor_diameter(
        cls,
        value: str,
    ) -> ValidationResult:
        return cls.positive_number(
            value,
            "Motor diameter",
        )

    @classmethod
    def motor_length(
        cls,
        value: str,
    ) -> ValidationResult:
        return cls.positive_number(
            value,
            "Motor length",
        )

    # =============================================================
    # MASSES
    # =============================================================

    @classmethod
    def initial_mass(
        cls,
        value: str,
    ) -> ValidationResult:
        return cls.positive_number(
            value,
            "Initial mass",
        )

    @classmethod
    def propellant_mass(
        cls,
        value: str,
    ) -> ValidationResult:
        return cls.positive_number(
            value,
            "Propellant mass",
        )