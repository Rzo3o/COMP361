from core.hexmath import HexMath


def test_hex_pixel_conversion():
    q, r = 2, -1
    px, py = HexMath.hex_to_pixel(q, r)
    rq, rr = HexMath.pixel_to_hex(px, py)

    assert (q, r) == (rq, rr), f"Expected ({q}, {r}), got ({rq}, {rr})"
