"""Tests for git_weekly.i18n."""

from git_weekly.i18n import get_category_label, get_lang, set_lang, t


class TestI18n:
    def setup_method(self):
        set_lang("zh")

    def test_default_lang_is_zh(self):
        set_lang("zh")
        assert get_lang() == "zh"

    def test_set_lang_en(self):
        set_lang("en")
        assert get_lang() == "en"

    def test_invalid_lang_falls_back_to_zh(self):
        set_lang("fr")
        assert get_lang() == "zh"

    def test_translate_zh(self):
        set_lang("zh")
        assert "周报" in t("report.title")

    def test_translate_en(self):
        set_lang("en")
        assert "Weekly Report" in t("report.title")

    def test_translate_with_kwargs(self):
        result = t("warn.not_git_repo", path="/tmp/foo")
        assert "/tmp/foo" in result

    def test_unknown_key_returns_key(self):
        assert t("nonexistent.key") == "nonexistent.key"

    def test_category_label_zh(self):
        set_lang("zh")
        label = get_category_label("feat")
        assert "新功能" in label

    def test_category_label_en(self):
        set_lang("en")
        label = get_category_label("feat")
        assert "Features" in label

    def test_category_label_unknown_falls_back(self):
        label = get_category_label("unknown_cat")
        assert label  # should return "other" label, not crash
