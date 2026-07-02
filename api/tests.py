from django.test import SimpleTestCase

from .cache_utils import build_course_cache_key


class CacheUtilsTests(SimpleTestCase):
    def test_build_course_cache_key_uses_prefix_and_identifier(self):
        key = build_course_cache_key("list", "page:1")

        self.assertEqual(key, "simple_lms:course:list:page:1")
