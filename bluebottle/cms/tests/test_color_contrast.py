from django.test import SimpleTestCase

from bluebottle.cms.utils.color_contrast import (
    DARK_NEUTRAL,
    PAGE_BACKGROUND,
    PALE_GREY,
    WHITE,
    apply_on_colors,
    choose_on_color,
    contrast_ratio,
    ensure_contrast,
    ensure_contrast_on_surfaces,
    evaluate_platform_colors,
    mix_with_white,
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


class ChooseOnColorTestCase(SimpleTestCase):

    def test_dark_fill_uses_white(self):
        self.assertEqual(choose_on_color('#000000'), WHITE)

    def test_pale_fill_uses_dark_neutral(self):
        self.assertEqual(choose_on_color('#FFFF00'), DARK_NEUTRAL)

    def test_both_pass_uses_higher_contrast(self):
        self.assertEqual(choose_on_color('#0055AA'), WHITE)
        self.assertGreater(
            contrast_ratio(WHITE, '#0055AA'),
            contrast_ratio(DARK_NEUTRAL, '#0055AA'),
        )

    def test_mid_blue_uses_dark_neutral(self):
        self.assertEqual(choose_on_color('#3C96DC'), DARK_NEUTRAL)
        self.assertTrue(passes_aa(DARK_NEUTRAL, '#3C96DC'))
        self.assertFalse(passes_aa(WHITE, '#3C96DC'))

    def test_neither_passes_uses_higher_contrast(self):
        self.assertEqual(choose_on_color('#777777'), WHITE)
        self.assertFalse(passes_aa(WHITE, '#777777'))
        self.assertFalse(passes_aa(DARK_NEUTRAL, '#777777'))
        self.assertGreater(
            contrast_ratio(WHITE, '#777777'),
            contrast_ratio(DARK_NEUTRAL, '#777777'),
        )

    def test_missing_fill_returns_none(self):
        self.assertIsNone(choose_on_color(None))
        self.assertIsNone(choose_on_color(''))

    def test_accepts_hex_without_hash(self):
        self.assertEqual(choose_on_color('FFFF00'), DARK_NEUTRAL)

    def test_invalid_hex_returns_none(self):
        self.assertIsNone(choose_on_color('not-a-color'))


class ApplyOnColorsTestCase(SimpleTestCase):

    def test_sets_action_and_description_text_colors(self):
        class Settings:
            action_color = '#FFFF00'
            action_text_color = '#FFFFFF'
            description_color = '#281E50'
            description_text_color = None

        settings = Settings()
        apply_on_colors(settings)

        self.assertEqual(settings.action_text_color, DARK_NEUTRAL)
        self.assertEqual(settings.description_text_color, WHITE)

    def test_clears_derived_colours_when_fill_is_missing(self):
        class Settings:
            action_color = None
            action_text_color = '#EEEEEE'
            alternative_link_color = '#112233'
            action_on_tint_color = '#445566'
            description_color = ''
            description_text_color = '#123456'
            description_on_background_color = '#654321'
            description_on_tint_color = '#ABCDEF'

        settings = Settings()
        apply_on_colors(settings)

        self.assertIsNone(settings.action_text_color)
        self.assertIsNone(settings.alternative_link_color)
        self.assertIsNone(settings.action_on_tint_color)
        self.assertIsNone(settings.description_text_color)
        self.assertIsNone(settings.description_on_background_color)
        self.assertIsNone(settings.description_on_tint_color)


class EnsureContrastTestCase(SimpleTestCase):

    def test_readable_colour_is_kept(self):
        self.assertEqual(ensure_contrast('#0055AA', WHITE), '#0055AA')

    def test_yellow_on_white_is_darkened_until_it_passes(self):
        result = ensure_contrast('#FFFF00', WHITE)
        self.assertNotEqual(result, '#FFFF00')
        self.assertTrue(passes_aa(result, WHITE))

    def test_passes_on_white_and_pale_grey(self):
        result = ensure_contrast_on_surfaces('#FFFF00', [WHITE, PALE_GREY])
        self.assertTrue(passes_aa(result, WHITE))
        self.assertTrue(passes_aa(result, PALE_GREY))

    def test_missing_values_return_none(self):
        self.assertIsNone(ensure_contrast(None, WHITE))
        self.assertIsNone(ensure_contrast('#FFFF00', None))


class TintTestCase(SimpleTestCase):

    def test_tint_stops_match_tinycolor_mix(self):
        self.assertEqual(mix_with_white('#3C96DC', 95), '#F5FAFD')
        self.assertEqual(mix_with_white('#3C96DC', 90), '#ECF5FC')
        self.assertEqual(mix_with_white('#3C96DC', 80), '#D8EAF8')

    def test_tint_white_stays_white(self):
        self.assertEqual(mix_with_white('#FFFFFF', 90), '#FFFFFF')


class ApplyPatternColorsTestCase(SimpleTestCase):

    def test_sets_pattern_two_and_three_for_action_and_description(self):
        class Settings:
            action_color = '#FFFF00'
            action_text_color = None
            alternative_link_color = None
            action_on_tint_color = None
            description_color = '#281E50'
            description_text_color = None
            description_on_background_color = None
            description_on_tint_color = None

        settings = Settings()
        apply_on_colors(settings)

        self.assertEqual(settings.action_text_color, DARK_NEUTRAL)
        self.assertTrue(passes_aa(settings.alternative_link_color, WHITE))
        self.assertTrue(passes_aa(settings.alternative_link_color, PALE_GREY))
        self.assertTrue(
            passes_aa(settings.action_on_tint_100_color, mix_with_white('#FFFF00', 95))
        )
        self.assertTrue(
            passes_aa(settings.action_on_tint_color, mix_with_white('#FFFF00', 90))
        )
        self.assertTrue(
            passes_aa(settings.action_on_tint_300_color, mix_with_white('#FFFF00', 80))
        )

        self.assertEqual(settings.description_text_color, WHITE)
        self.assertEqual(settings.description_on_background_color, '#281E50')
        self.assertEqual(settings.description_on_tint_100_color, '#281E50')
        self.assertEqual(settings.description_on_tint_color, '#281E50')
        self.assertEqual(settings.description_on_tint_300_color, '#281E50')

    def test_pale_action_blue_is_darkened_for_text_and_tint(self):
        class Settings:
            action_color = '#3C96DC'
            action_text_color = None
            alternative_link_color = None
            action_on_tint_color = None
            description_color = None
            description_text_color = None

        settings = Settings()
        apply_on_colors(settings)

        self.assertEqual(settings.action_text_color, WHITE)
        self.assertNotEqual(settings.alternative_link_color, '#3C96DC')
        self.assertTrue(passes_aa(settings.alternative_link_color, WHITE))
        self.assertTrue(passes_aa(settings.alternative_link_color, PALE_GREY))
        self.assertTrue(
            passes_aa(settings.action_on_tint_100_color, mix_with_white('#3C96DC', 95))
        )
        self.assertTrue(
            passes_aa(settings.action_on_tint_color, mix_with_white('#3C96DC', 90))
        )
        self.assertTrue(
            passes_aa(settings.action_on_tint_300_color, mix_with_white('#3C96DC', 80))
        )
