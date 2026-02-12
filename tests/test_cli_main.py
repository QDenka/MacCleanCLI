from models.scan_result import FileCategory
from main import parse_categories


def test_parse_categories_none():
    assert parse_categories(None) is None


def test_parse_categories_valid():
    categories = parse_categories("user_cache, log_files,trash")
    assert categories == [
        FileCategory.USER_CACHE,
        FileCategory.LOG_FILES,
        FileCategory.TRASH,
    ]


def test_parse_categories_invalid():
    try:
        parse_categories("foo")
    except ValueError as exc:
        assert "Unknown categories" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown category")
