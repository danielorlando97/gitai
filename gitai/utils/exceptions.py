"""Custom exceptions for GitClassifier."""


class GitClassifierError(Exception):
    """Base exception for GitClassifier."""

    pass


class ProviderError(GitClassifierError):
    """Exception for provider-related errors."""

    pass


class ClassifierError(GitClassifierError):
    """Exception for classifier-related errors."""

    pass


class ExecutorError(GitClassifierError):
    """Exception for executor-related errors."""

    pass


class StorageError(GitClassifierError):
    """Exception for storage-related errors."""

    pass
