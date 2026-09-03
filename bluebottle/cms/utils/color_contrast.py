from dataclasses import dataclass
from typing import List, Optional

import wcag_contrast_ratio as contrast
from PIL import ImageColor
from django.utils.translation import gettext_lazy as _

PAGE_BACKGROUND = '#FFFFFF'


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
    return value


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
