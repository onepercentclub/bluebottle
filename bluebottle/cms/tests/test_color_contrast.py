from django.test import SimpleTestCase

from bluebottle.cms.utils.color_contrast import (
    PAGE_BACKGROUND,
    contrast_ratio,
    evaluate_platform_colors,
    passes_aa,
)


class PlatformColorContrastTestCase(SimpleTestCase):

    def test_black_on_white_passes_aa(self):
        self.assertGreaterEqual(contrast_ratio('#000000', '#FFFFFF'), 4.5)
        self.assertTrue(passes_aa('#000000', '#FFFFFF'))

    def test_light_grey_on_white_fails_aa(self):
        self.assertFalse(passes_aa('#CCCCCC', '#FFFFFF'))

    def test_evaluate_skips_incomplete_action_pair(self):
        class Settings:
            action_color = '#3C96DC'
            action_text_color = None
            description_color = None
            description_text_color = None
            footer_color = None
            footer_text_color = None
            alternative_link_color = None

        results = evaluate_platform_colors(Settings())
        self.assertEqual([result.id for result in results], ['link'])
        self.assertEqual(results[0].foreground, '#3C96DC')
        self.assertEqual(results[0].background, PAGE_BACKGROUND)

    def test_evaluate_all_pairs(self):
        class Settings:
            action_color = '#0055AA'
            action_text_color = '#FFFFFF'
            description_color = '#281E50'
            description_text_color = '#FFFFFF'
            footer_color = '#3B3B3B'
            footer_text_color = '#FFFFFF'
            alternative_link_color = None

        results = evaluate_platform_colors(Settings())
        self.assertEqual(
            [result.id for result in results],
            ['action', 'description', 'footer', 'link'],
        )
        self.assertTrue(all(result.passes for result in results))

    def test_link_prefers_alternative_link_color(self):
        class Settings:
            action_color = '#CCCCCC'
            action_text_color = None
            description_color = None
            description_text_color = None
            footer_color = None
            footer_text_color = None
            alternative_link_color = '#0055AA'

        results = evaluate_platform_colors(Settings())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, 'link')
        self.assertEqual(results[0].foreground, '#0055AA')
        self.assertTrue(results[0].passes)

    def test_failing_action_pair(self):
        class Settings:
            action_color = '#FFFFFF'
            action_text_color = '#EEEEEE'
            description_color = None
            description_text_color = None
            footer_color = None
            footer_text_color = None
            alternative_link_color = None

        results = evaluate_platform_colors(Settings())
        action = next(result for result in results if result.id == 'action')
        self.assertFalse(action.passes)
