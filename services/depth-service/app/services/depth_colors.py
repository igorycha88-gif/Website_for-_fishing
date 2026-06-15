DEPTH_COLOR_RAMP_NAVIONICS = [
    (0, 2, "#B3E5FC"),
    (2, 5, "#4FC3F7"),
    (5, 10, "#0288D1"),
    (10, 20, "#01579B"),
    (20, 50, "#1A237E"),
    (50, 99999, "#000C2E"),
]

DEPTH_COLOR_RAMP_CONTRAST = [
    (0, 2, "#80DEEA"),
    (2, 5, "#26C6DA"),
    (5, 10, "#00ACC1"),
    (10, 20, "#00838F"),
    (20, 50, "#006064"),
    (50, 99999, "#00363A"),
]

DEPTH_COLOR_RAMP_SPORT = [
    (0, 2, "#A5D6A7"),
    (2, 5, "#66BB6A"),
    (5, 10, "#43A047"),
    (10, 20, "#2E7D32"),
    (20, 50, "#1B5E20"),
    (50, 99999, "#0D3811"),
]

COLOR_SCHEMES = {
    "navionics": DEPTH_COLOR_RAMP_NAVIONICS,
    "contrast": DEPTH_COLOR_RAMP_CONTRAST,
    "sport": DEPTH_COLOR_RAMP_SPORT,
}

DEFAULT_SCHEME = "navionics"


def get_color_ramp(scheme: str = DEFAULT_SCHEME):
    return COLOR_SCHEMES.get(scheme, COLOR_SCHEMES[DEFAULT_SCHEME])


def depth_to_color(depth: float, scheme: str = DEFAULT_SCHEME) -> str:
    ramp = get_color_ramp(scheme)
    for min_d, max_d, color in ramp:
        if min_d <= depth < max_d:
            return color
    return ramp[-1][2]


def depth_category_label(depth: float) -> str:
    if depth < 2:
        return "0-2\u043c"
    elif depth < 5:
        return "2-5\u043c"
    elif depth < 10:
        return "5-10\u043c"
    elif depth < 20:
        return "10-20\u043c"
    elif depth < 50:
        return "20-50\u043c"
    else:
        return ">50\u043c"


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
