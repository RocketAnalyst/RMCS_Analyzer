from typing import List, Optional

from .test_model import TestModel


class TestSession:
    """
    Manages the collection of tests currently loaded into
    RMCS Analyzer.

    A session can contain multiple tests, while only one test
    is designated as the active test at any given time.
    """

    def __init__(self):
        self._tests: List[TestModel] = []
        self._active_test: Optional[TestModel] = None

        # Persisted project-level Campaign Analysis selection.
        # None means the project predates Campaign selection persistence
        # and should use the Campaign panel's normal default (all tests).
        # An empty set is a valid saved state meaning no tests were selected.
        self.campaign_selected_sources: Optional[set[str]] = None

    # =============================================================
    # TEST COLLECTION
    # =============================================================

    @property
    def tests(self) -> List[TestModel]:
        """
        Return the currently loaded tests.

        A copy of the list is returned so callers cannot
        accidentally modify the internal collection.
        """

        return list(self._tests)

    @property
    def test_count(self) -> int:
        """
        Return the number of loaded tests.
        """

        return len(self._tests)

    # =============================================================
    # ACTIVE TEST
    # =============================================================

    @property
    def active_test(self) -> Optional[TestModel]:
        """
        Return the currently active test.
        """

        return self._active_test

    # =============================================================
    # ADD TEST
    # =============================================================

    def add_test(
        self,
        test: TestModel,
    ) -> bool:
        """
        Add a test to the session.

        Returns:
            True if the test was added.
            False if the test was already loaded.

        The first test added automatically becomes the
        active test.
        """

        existing = self.get_test_by_source(
            test.source_file
        )

        if existing is not None:
            return False

        self._tests.append(
            test
        )

        if self._active_test is None:
            self._active_test = test

        return True

    # =============================================================
    # REMOVE TEST
    # =============================================================

    def remove_test(
        self,
        test: TestModel,
    ) -> bool:
        """
        Remove a test from the session.

        Returns:
            True if the test was removed.
            False if the test was not loaded.

        If the active test is removed, another loaded test
        becomes active when available.
        """

        index = self._find_test_index(
            test
        )

        if index is None:
            return False

        was_active = (
            self._active_test is test
        )

        self._tests.pop(
            index
        )

        if was_active:
            if self._tests:
                self._active_test = (
                    self._tests[0]
                )
            else:
                self._active_test = None

        return True

    # =============================================================
    # SELECT TEST
    # =============================================================

    def select_test(
        self,
        test: TestModel,
    ) -> bool:
        """
        Make a loaded test the active test.

        Tests are compared by object identity rather than
        dataclass equality because TestModel contains NumPy
        arrays that cannot be compared safely using normal
        equality operations.

        Returns:
            True if the test was selected.
            False if the test is not part of the session.
        """

        if self._find_test_index(test) is None:
            return False

        self._active_test = test

        return True

    # =============================================================
    # FIND TEST INDEX
    # =============================================================

    def _find_test_index(
        self,
        test: TestModel,
    ) -> Optional[int]:
        """
        Find a test by object identity.

        Returns:
            The list index if found, otherwise None.
        """

        for index, loaded_test in enumerate(
            self._tests
        ):
            if loaded_test is test:
                return index

        return None

    # =============================================================
    # FIND TEST BY SOURCE
    # =============================================================

    def get_test_by_source(
        self,
        source_file: str,
    ) -> Optional[TestModel]:
        """
        Find a loaded test by its source filename/path.

        Source paths are normalized for slash direction
        and case before comparison.

        Returns:
            The matching TestModel, or None if not found.
        """

        normalized_source = (
            source_file
            .replace("\\", "/")
            .lower()
        )

        for test in self._tests:
            existing_source = (
                test.source_file
                .replace("\\", "/")
                .lower()
            )

            if existing_source == normalized_source:
                return test

        return None

    # =============================================================
    # CLEAR SESSION
    # =============================================================

    def clear(self):
        """
        Remove all loaded tests and clear the active test.
        """

        self._tests.clear()

        self._active_test = None

    # =============================================================
    # MODIFICATION STATE
    # =============================================================

    @property
    def has_modified_tests(self) -> bool:
        """
        Return True if any loaded test contains unsaved changes.
        """

        return any(
            test.modified
            for test in self._tests
        )