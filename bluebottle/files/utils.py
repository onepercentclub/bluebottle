def get_default_cropbox(image, ratio=16 / 9, border=0.0):
    try:
        current_ratio = image.width / image.height
    except TypeError:
        return ''

    if current_ratio > ratio:
        new_width = image.height * ratio

        left = int((image.width / 2) - (new_width / 2))
        right = int((image.width / 2) + (new_width / 2))
        top = 0
        bottom = image.height
    else:
        new_height = image.width / ratio

        left = 0
        right = image.width

        top = int((image.height / 2) - (new_height / 2))
        bottom = int((image.height / 2) + (new_height / 2))

    if border:
        new_width = right - left
        new_height = top - bottom

        left = left + border
        right = right - border
        top = top + border
        bottom = bottom - border

    return f'{left},{top},{right},{bottom}'
