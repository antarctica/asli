from unittest.mock import patch

from asli.cli import _parse_args, _top_level_parser


def test_get_cli_lsm_args():
    # test -e flag
    with patch("sys.argv", ["_", "download", "-e"]):
        args = _parse_args(_top_level_parser())

        assert args.e is True
        assert args.area_dict is None

    # test area and border parsing
    test_border = 7.0
    with patch(
        "sys.argv",
        ["_", "download", "--area", "1", "2", "3", "4", "--border", str(test_border)],
    ):
        args = _parse_args(_top_level_parser())

        assert args.area_dict == {"north": 1, "west": 2, "south": 3, "east": 4}
        assert args.border == test_border

    # test that -e overrides --area
    with patch("sys.argv", ["_", "download", "--area", "1", "2", "3", "4", "-e"]):
        args = _parse_args(_top_level_parser())

        assert args.e is True
        assert args.area_dict is None
