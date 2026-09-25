from dataclasses import dataclass
from typing import List, Optional, Sequence

import wcag_contrast_ratio as contrast
from PIL import ImageColor
from django.utils.translation import gettext_lazy as _

PAGE_BACKGROUND = '#FFFFFF'
WHITE = '#FFFFFF'
DARK_NEUTRAL = '#2A2A2A'
PALE_GREY = '#EEEEEE'
TINT_STOPS = {
    100: 95,
    200: 90,
    300: 80,
}


@dataclass(frozen=True)
class PairResult:
    id: str
    label: str
    foreground: str
    background: str
    ratio: float
    passes: bool


def hex_to_rgb(hex_color: str):
    rgb = ImageColor.getcolor(hex_color, 'RGB')
    return tuple(channel / 255.0 for channel in rgb)


def contrast_ratio(foreground: str, background: str) -> float:
    return contrast.rgb(hex_to_rgb(foreground), hex_to_rgb(background))


def passes_aa(foreground: str, background: str, large: bool = False) -> bool:
    return contrast.passes_AA(contrast_ratio(foreground, background), large=large)


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


def _round_channel(value: float) -> int:
    return max(0, min(255, int(value + 0.5)))


def _hex_from_rgb(red: int, green: int, blue: int) -> str:
    return f'#{red:02X}{green:02X}{blue:02X}'


def mix_with_white(hex_color: Optional[str], amount: int) -> Optional[str]:
    hex_color = _normalize_hex(hex_color)
    if not hex_color:
        return None
    red, green, blue = ImageColor.getcolor(hex_color, 'RGB')
    weight = amount / 100.0
    return _hex_from_rgb(
        _round_channel((255 - red) * weight + red),
        _round_channel((255 - green) * weight + green),
        _round_channel((255 - blue) * weight + blue),
    )


def mix_with_black(hex_color: Optional[str], amount: int) -> Optional[str]:
    hex_color = _normalize_hex(hex_color)
    if not hex_color:
        return None
    red, green, blue = ImageColor.getcolor(hex_color, 'RGB')
    keep = 1 - (amount / 100.0)
    return _hex_from_rgb(
        _round_channel(red * keep),
        _round_channel(green * keep),
        _round_channel(blue * keep),
    )


def ensure_contrast(foreground: Optional[str], background: Optional[str]) -> Optional[str]:
    foreground = _normalize_hex(foreground)
    background = _normalize_hex(background)
    if not foreground or not background:
        return None

    try:
        if contrast.passes_AA(contrast_ratio(foreground, background), large=False):
            return foreground
    except ValueError:
        return None

    low = 1
    high = 100
    best = None
    while low <= high:
        mid = (low + high) // 2
        candidate = mix_with_black(foreground, mid)
        if contrast.passes_AA(contrast_ratio(candidate, background), large=False):
            best = candidate
            high = mid - 1
        else:
            low = mid + 1

    return best or DARK_NEUTRAL


def ensure_contrast_on_surfaces(
    foreground: Optional[str],
    backgrounds: Sequence[str],
) -> Optional[str]:
    result = _normalize_hex(foreground)
    if not result:
        return None
    for background in backgrounds:
        result = ensure_contrast(result, background)
        if not result:
            return None
    return result


def choose_on_color(background: Optional[str]) -> Optional[str]:
    background = _normalize_hex(background)
    if not background:
        return None

    try:
        white_ratio = contrast_ratio(WHITE, background)
        dark_ratio = contrast_ratio(DARK_NEUTRAL, background)
    except ValueError:
        return None
    passing = []
    if contrast.passes_AA(white_ratio, large=False):
        passing.append((white_ratio, WHITE))
    if contrast.passes_AA(dark_ratio, large=False):
        passing.append((dark_ratio, DARK_NEUTRAL))

    candidates = passing or [(white_ratio, WHITE), (dark_ratio, DARK_NEUTRAL)]
    return max(candidates, key=lambda item: item[0])[1]


def _apply_brand_patterns(settings, brand_color, text_attr, on_background_attr, tint_attrs):
    on_color = choose_on_color(brand_color)
    if on_color:
        setattr(settings, text_attr, on_color)

    on_background = ensure_contrast_on_surfaces(brand_color, [WHITE, PALE_GREY])
    if on_background:
        setattr(settings, on_background_attr, on_background)

    for stop, amount in TINT_STOPS.items():
        attr = tint_attrs.get(stop)
        if not attr:
            continue
        tint = mix_with_white(brand_color, amount)
        on_tint = ensure_contrast(brand_color, tint) if tint else None
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
                100: 'action_on_tint_100_color',
                200: 'action_on_tint_color',
                300: 'action_on_tint_300_color',
            },
        )
    else:
        _clear_derived_fields(
            settings,
            (
                'action_text_color',
                'alternative_link_color',
                'action_on_tint_100_color',
                'action_on_tint_color',
                'action_on_tint_300_color',
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
                100: 'description_on_tint_100_color',
                200: 'description_on_tint_color',
                300: 'description_on_tint_300_color',
            },
        )
    else:
        _clear_derived_fields(
            settings,
            (
                'description_text_color',
                'description_on_background_color',
                'description_on_tint_100_color',
                'description_on_tint_color',
                'description_on_tint_300_color',
            ),
        )


def _evaluate_pair(pair_id: str, label: str, foreground: Optional[str], background: Optional[str]) -> Optional[PairResult]:
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
        getattr(settings, 'action_color', None),
    )
    if action:
        pairs.append(action)

    description = _evaluate_pair(
        'description',
        str(_('Description')),
        getattr(settings, 'description_text_color', None),
        getattr(settings, 'description_color', None),
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
