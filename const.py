import screeninfo


class const:
    try:
        __m = screeninfo.get_monitors()
    except screeninfo.common.ScreenInfoError:
        __m = []

    if __m:
        _mwidth = __m[0].width
        _mheight = __m[0].height

        for monitors in __m:
            _mwidth = max(_mwidth, monitors.width)
            _mheight = max(_mheight, monitors.height)
    else:
        # Fallback values for headless environments such as Nix build checks.
        _mwidth = 1920
        _mheight = 1080

    _entry_height = 21
    _entry_width = 300
    _label_width = 300
    _2exp1div1200 = 2 ** (1 / 1200)

    def _dez2amp(self, dezibel):
        amp = 10 ** (dezibel / 10)
        return amp
