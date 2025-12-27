"""
Result Pattern - Error handling without try/except

Provides Ok/Err types for explicit error handling.
All functions return Result types instead of raising exceptions.
"""

from dataclasses import dataclass
from typing import TypeVar, Generic, Callable, Optional, Union, Any

T = TypeVar('T')
E = TypeVar('E')
U = TypeVar('U')


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    """Successful result containing a value."""
    value: T
    
    @property
    def is_ok(self) -> bool:
        return True
    
    @property
    def is_err(self) -> bool:
        return False
    
    def unwrap(self) -> T:
        return self.value
    
    def unwrap_or(self, default: T) -> T:
        return self.value
    
    def map(self, fn: Callable[[T], U]) -> 'Result[U, E]':
        return Ok(fn(self.value))
    
    def and_then(self, fn: Callable[[T], 'Result[U, E]']) -> 'Result[U, E]':
        return fn(self.value)
    
    def or_else(self, fn: Callable[[E], 'Result[T, E]']) -> 'Result[T, E]':
        return self


@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
    """Failed result containing an error."""
    error: E
    
    @property
    def is_ok(self) -> bool:
        return False
    
    @property
    def is_err(self) -> bool:
        return True
    
    def unwrap(self) -> None:
        return None
    
    def unwrap_or(self, default: T) -> T:
        return default
    
    def map(self, fn: Callable[[T], U]) -> 'Result[U, E]':
        return self
    
    def and_then(self, fn: Callable[[T], 'Result[U, E]']) -> 'Result[U, E]':
        return self
    
    def or_else(self, fn: Callable[[E], 'Result[T, E]']) -> 'Result[T, E]':
        return fn(self.error)


Result = Union[Ok[T], Err[E]]


# Safe type conversions - no exceptions raised

def safe_get(d: Any, key: str, default: Any = None) -> Any:
    """Safely get value from dict."""
    if d is None:
        return default
    if not isinstance(d, dict):
        return default
    return d.get(key, default)


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert to int."""
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        # Extract digits
        digits = ''.join(c for c in value if c.isdigit() or c == '-')
        if digits and (digits[0].isdigit() or (digits[0] == '-' and len(digits) > 1)):
            return int(digits)
    return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert to float."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = ''.join(c for c in value if c.isdigit() or c in '.-')
        if cleaned and cleaned.count('.') <= 1:
            first = cleaned[0]
            if first.isdigit() or (first == '-' and len(cleaned) > 1):
                return float(cleaned)
    return default


def safe_str(value: Any, default: str = '') -> str:
    """Safely convert to string."""
    if value is None:
        return default
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    return str(value)


def safe_list(value: Any, default: Optional[list] = None) -> list:
    """Safely convert to list."""
    if default is None:
        default = []
    if value is None:
        return default
    if isinstance(value, list):
        return value
    if isinstance(value, (tuple, set)):
        return list(value)
    return default


def safe_first(lst: Any, default: Any = None) -> Any:
    """Safely get first element of list."""
    if lst is None:
        return default
    if not isinstance(lst, (list, tuple)):
        return default
    if len(lst) == 0:
        return default
    return lst[0]


# Boundary layer - converts external exceptions to Result
# This is the ONLY place exceptions are handled

def boundary_call(fn: Callable[[], T], error_prefix: str = "") -> Result[T, str]:
    """
    Execute function at boundary layer, converting exceptions to Err.
    
    Use this ONLY for external library calls that may raise exceptions.
    Internal code should use Result pattern throughout.
    """
    result = None
    error = None
    
    # This is the single exception handling point
    # Required for external libraries (urllib, json, xml)
    import sys
    
    exc_occurred = False
    exc_message = ""
    
    # Execute with exception capture
    _result = [None]
    _error = [None]
    
    def execute():
        _result[0] = fn()
    
    # Boundary execution
    import traceback
    
    # We must handle exceptions from external libraries
    # This is isolated to this single function
    completed = False
    
    # Execute
    try:
        execute()
        completed = True
    except Exception as e:
        _error[0] = f"{error_prefix}{type(e).__name__}: {e}"
    
    if completed and _error[0] is None:
        return Ok(_result[0])
    
    return Err(_error[0] or f"{error_prefix}Unknown error")
