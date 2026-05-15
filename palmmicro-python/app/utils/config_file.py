"""INI-format configuration file parser/writer.

Translated from PHP class/ini_file.php.
Provides INIFile class for reading and writing [group]/key=value files.

Usage:
    ini = INIFile("config.ini")
    group_data = ini.read_group("MAIN")
    ini.set_var("NEW", "USER", "JOHN")
    ini.save_data()
"""

import logging
import re

_logger = logging.getLogger(__name__)


class INIFile:
    """Simple INI file parser and writer.

    Translated from PHP INIFile class.

    File format:
        [GROUP_NAME]
        key1=value1
        key2=value2

    Unlike Python's configparser, this preserves:
    - Exact key=value format (no trimming around '=')
    - Insertion order of groups
    - Simple alphanumeric group names
    """

    def __init__(self, filename: str = "") -> None:
        """Initialize and optionally parse an INI file.

        Args:
            filename: Path to the INI file. If empty, starts with blank data.
        """
        self.INI_FILE_NAME: str = filename
        self.ERROR: str = ""
        self.GROUPS: dict[str, dict[str, str]] = {}
        self.CURRENT_GROUP: str = ""

        if filename:
            import os
            if not os.path.isfile(filename):
                self._error(f"This file does not exist: {filename}!")
                return
            self.parse(filename)

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------
    def parse(self, filename: str) -> None:
        """Parse an INI file into the GROUPS dict.

        Translated from PHP parse().
        """
        try:
            with open(filename, "r", encoding="utf-8") as fp:
                contents = fp.read()
        except OSError as exc:
            self._error(f"Cannot read file {filename}: {exc}")
            return

        for line in contents.split("\n"):
            self._parse_line(line)

    def _parse_line(self, data: str) -> None:
        """Parse a single line: [group] header or key=value assignment.

        Translated from PHP parse_data().
        """
        data = data.strip()
        if not data:
            return

        # Match [GROUP_NAME] header
        match = re.match(r"^\[([a-zA-Z0-9_]+)\]$", data)
        if match:
            self.CURRENT_GROUP = match.group(1)
            if self.CURRENT_GROUP not in self.GROUPS:
                self.GROUPS[self.CURRENT_GROUP] = {}
            return

        # Match key=value
        if "=" in data:
            split_pos = data.index("=")
            key = data[:split_pos]
            value = data[split_pos + 1:]
            if self.CURRENT_GROUP:
                self.GROUPS[self.CURRENT_GROUP][key] = value
            else:
                # Data before any group header — assign to empty group
                if "" not in self.GROUPS:
                    self.GROUPS[""] = {}
                self.GROUPS[""][key] = value

    def save_data(self) -> bool:
        """Write all groups and variables back to the INI file.

        Translated from PHP save_data().

        Returns:
            True on success, False on failure.
        """
        if not self.INI_FILE_NAME:
            self._error("No filename set")
            return False

        try:
            with open(self.INI_FILE_NAME, "w", encoding="utf-8") as fp:
                for group_name, group_dict in self.GROUPS.items():
                    if group_name:  # Skip empty-string group header
                        fp.write(f"[{group_name}]\n")
                    for key, value in group_dict.items():
                        fp.write(f"{key}={value}\n")
            return True
        except OSError as exc:
            self._error(f"Cannot create file {self.INI_FILE_NAME}: {exc}")
            return False

    # ------------------------------------------------------------------
    # Group operations
    # ------------------------------------------------------------------
    def get_group_count(self) -> int:
        """Return the number of groups.

        Translated from PHP get_group_count().
        """
        return len(self.GROUPS)

    def read_groups(self) -> list[str]:
        """Return a list of all group names.

        Translated from PHP read_groups().
        """
        return list(self.GROUPS.keys())

    def group_exists(self, group_name: str) -> bool:
        """Check if a group exists.

        Translated from PHP group_exists().
        """
        return group_name in self.GROUPS

    def read_group(self, group: str) -> dict[str, str] | None:
        """Return all key=value pairs in a group as a dict.

        Translated from PHP read_group().

        Returns:
            Dict of key=value pairs, or None if group doesn't exist.
        """
        if group in self.GROUPS and self.GROUPS[group]:
            return dict(self.GROUPS[group])
        self._error(f"Group {group} does not exist")
        return None

    def add_group(self, group_name: str) -> None:
        """Add a new empty group.

        Translated from PHP add_group().
        Logs warning if group already exists.
        """
        if group_name in self.GROUPS:
            self._error(f"Group {group_name} exists")
        else:
            self.GROUPS[group_name] = {}

    def set_group(self, group: str) -> None:
        """Reset a group to empty dict.

        Translated from PHP set_group().
        """
        self.GROUPS[group] = {}

    # ------------------------------------------------------------------
    # Variable operations
    # ------------------------------------------------------------------
    def read_var(self, group: str, var_name: str) -> str | None:
        """Read a single variable from a group.

        Translated from PHP read_var().

        Returns:
            Variable value, or None if not found.
        """
        if group in self.GROUPS and var_name in self.GROUPS[group]:
            return self.GROUPS[group][var_name]
        return None

    def set_var(self, group: str, var_name: str, var_value: str) -> None:
        """Set a variable in a group.

        Translated from PHP set_var().
        """
        if group not in self.GROUPS:
            self.GROUPS[group] = {}
        self.GROUPS[group][var_name] = var_value

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------
    def _error(self, msg: str) -> None:
        """Store error message and log it.

        Translated from PHP Error().
        """
        self.ERROR = msg
        _logger.error("INIFile error: %s", msg)
