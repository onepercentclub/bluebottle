from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

import wcag_contrast_ratio as contrast
from PIL import ImageColor
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

PAGE_BACKGROUND = '#FFFFFF'
WHITE = '#FFFFFF'
BLACK = '#000000'
DARK_NEUTRAL = '#2A2A2A'
PALE_GREY = '#EEEEEE'
DARK_TEXT_RATIO = 7
TINT_STOPS = {
    200: 90,
}


@dataclass(frozen=True)
class PairResult:
    id: str
    label: str
    foreground: str
    background: str
    ratio: float
    passes: bool


def _normalize_hex(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if not value.startswith('#'):
        value = f'#{value}'
    if len(value) == 4:
        value = '#' + ''.join(channel * 2 for channel in value[1:])
    return value.upper()


class Color:
    """A hex colour with the mixing and WCAG contrast helpers we need."""

    def __init__(self, hex_color: str):
        self.hex = hex_color

    @classmethod
    def parse(cls, value: Optional[str]) -> Optional['Color']:
        hex_color = _normalize_hex(value)
        return cls(hex_color) if hex_color else None

    def __str__(self):
        return self.hex

    @property
    def rgb(self):
        return ImageColor.getcolor(self.hex, 'RGB')

    def contrast_with(self, other: 'Color') -> float:
        return contrast.rgb(
            tuple(channel / 255.0 for channel in self.rgb),
            tuple(channel / 255.0 for channel in other.rgb),
        )

    def passes_aa_on(self, other: 'Color', large: bool = False) -> bool:
        return contrast.passes_AA(self.contrast_with(other), large=large)

    def mix(self, other: 'Color', amount: int) -> 'Color':
        """Move `amount` percent of the way towards `other`."""
        weight = amount / 100.0
        channels = [
            max(0, min(255, int(own + (target - own) * weight + 0.5)))
            for own, target in zip(self.rgb, other.rgb)
        ]
        return Color('#{:02X}{:02X}{:02X}'.format(*channels))

    def with_white(self, amount: int) -> 'Color':
        return self.mix(Color(WHITE), amount)

    def with_black(self, amount: int) -> 'Color':
        return self.mix(Color(BLACK), amount)

    def darkened_until(self, is_readable: Callable[['Color'], bool]) -> Optional['Color']:
        """Smallest amount of black that makes this colour pass `is_readable`."""
        low, high, best = 1, 100, None
        while low <= high:
            mid = (low + high) // 2
            candidate = self.with_black(mid)
            if is_readable(candidate):
                best = candidate
                high = mid - 1
            else:
                low = mid + 1
        return best

    def readable_on(self, background: 'Color') -> 'Color':
        if self.passes_aa_on(background):
            return self
        return self.darkened_until(lambda c: c.passes_aa_on(background)) or Color(DARK_NEUTRAL)

    def readable_fill(self) -> 'Color':
        """A fill that white (or very dark) text can be read on."""
        white, dark = Color(WHITE), Color(DARK_NEUTRAL)
        if white.passes_aa_on(self) or dark.contrast_with(self) >= DARK_TEXT_RATIO:
            return self
        return self.darkened_until(lambda c: white.passes_aa_on(c)) or Color(BLACK)

    def on_color(self) -> 'Color':
        """White or dark text, whichever reads best on this colour."""
        white, dark = Color(WHITE), Color(DARK_NEUTRAL)
        ratios = [(white.contrast_with(self), white), (dark.contrast_with(self), dark)]
        passing = [item for item in ratios if contrast.passes_AA(item[0], large=False)]
        return max(passing or ratios, key=lambda item: item[0])[1]


def contrast_ratio(foreground: str, background: str) -> float:
    return Color(_normalize_hex(foreground)).contrast_with(Color(_normalize_hex(background)))


def passes_aa(foreground: str, background: str, large: bool = False) -> bool:
    return contrast.passes_AA(contrast_ratio(foreground, background), large=large)


def mix_with_white(hex_color: Optional[str], amount: int) -> Optional[str]:
    color = Color.parse(hex_color)
    return str(color.with_white(amount)) if color else None


def ensure_contrast(foreground: Optional[str], background: Optional[str]) -> Optional[str]:
    foreground, background = Color.parse(foreground), Color.parse(background)
    if not foreground or not background:
        return None
    try:
        return str(foreground.readable_on(background))
    except ValueError:
        return None


def ensure_contrast_on_surfaces(
    foreground: Optional[str],
    backgrounds: Sequence[str],
) -> Optional[str]:
    result = _normalize_hex(foreground)
    for background in backgrounds:
        result = ensure_contrast(result, background)
    return result


def ensure_readable_fill(fill: Optional[str]) -> Optional[str]:
    color = Color.parse(fill)
    if not color:
        return None
    try:
        return str(color.readable_fill())
    except ValueError:
        return None


def choose_on_color(background: Optional[str]) -> Optional[str]:
    color = Color.parse(background)
    if not color:
        return None
    try:
        return str(color.on_color())
    except ValueError:
        return None


def _apply_brand_patterns(
    settings,
    brand_color,
    text_attr,
    on_background_attr,
    tint_attrs,
    adjusted_attr,
):
    adjusted = ensure_readable_fill(brand_color)
    if adjusted:
        setattr(settings, adjusted_attr, adjusted)

    on_color = choose_on_color(adjusted)
    if on_color:
        setattr(settings, text_attr, on_color)

    on_background = ensure_contrast_on_surfaces(brand_color, [WHITE, PALE_GREY])
    if on_background:
        setattr(settings, on_background_attr, on_background)

    source = adjusted or brand_color
    for stop, amount in TINT_STOPS.items():
        attr = tint_attrs.get(stop)
        if not attr:
            continue
        tint = mix_with_white(source, amount)
        on_tint = ensure_contrast(source, tint) if tint else None
        if on_tint:
            setattr(settings, attr, on_tint)


def _clear_derived_fields(settings, fields) -> None:
    for attr in fields:
        if hasattr(settings, attr):
            setattr(settings, attr, None)


def apply_on_colors(settings) -> None:
    action = getattr(settings, 'action_color', None)
    if action:
        _apply_brand_patterns(
            settings,
            action,
            'action_text_color',
            'alternative_link_color',
            {
                200: 'action_on_tint_color',
            },
            'action_color_adjusted',
        )
    else:
        _clear_derived_fields(
            settings,
            (
                'action_text_color',
                'alternative_link_color',
                'action_on_tint_color',
                'action_color_adjusted',
            ),
        )

    description = getattr(settings, 'description_color', None)
    if description:
        _apply_brand_patterns(
            settings,
            description,
            'description_text_color',
            'description_on_background_color',
            {
                200: 'description_on_tint_color',
            },
            'description_color_adjusted',
        )
    else:
        _clear_derived_fields(
            settings,
            (
                'description_text_color',
                'description_on_background_color',
                'description_on_tint_color',
                'description_color_adjusted',
            ),
        )


def _evaluate_pair(
    pair_id: str,
    label: str,
    foreground: Optional[str],
    background: Optional[str],
) -> Optional[PairResult]:
    foreground = _normalize_hex(foreground)
    background = _normalize_hex(background)
    if not foreground or not background:
        return None
    ratio = contrast_ratio(foreground, background)
    return PairResult(
        id=pair_id,
        label=label,
        foreground=foreground,
        background=background,
        ratio=ratio,
        passes=contrast.passes_AA(ratio, large=False),
    )


def evaluate_platform_colors(settings) -> List[PairResult]:
    pairs = []

    action = _evaluate_pair(
        'action',
        str(_('Action')),
        getattr(settings, 'action_text_color', None),
        getattr(settings, 'action_color_adjusted', None) or getattr(settings, 'action_color', None),
    )
    if action:
        pairs.append(action)

    description = _evaluate_pair(
        'description',
        str(_('Description')),
        getattr(settings, 'description_text_color', None),
        getattr(settings, 'description_color_adjusted', None) or getattr(settings, 'description_color', None),
    )
    if description:
        pairs.append(description)

    footer = _evaluate_pair(
        'footer',
        str(_('Footer')),
        getattr(settings, 'footer_text_color', None),
        getattr(settings, 'footer_color', None),
    )
    if footer:
        pairs.append(footer)

    link_color = getattr(settings, 'alternative_link_color', None) or getattr(settings, 'action_color', None)
    link = _evaluate_pair(
        'link',
        str(_('Link')),
        link_color,
        PAGE_BACKGROUND,
    )
    if link:
        pairs.append(link)

    return pairs


def render_solid_preview(field_id, intro):
    from bluebottle.cms.models import SitePlatformSettings

    return render_to_string(
        'admin/cms/solid_color_contrast_panel.html',
        {
            'field_id': field_id,
            'intro': intro,
            'accessible': SitePlatformSettings.load().accessible_colours,
        },
    )
