import pytest
from lib import filter_json


json_input = [
    {
        "name": "foo",
        "num": 20,
        "data": [
            {
                "key": "asd",
                "val": 23
            },
            {
                "key": "dsa",
                "val": 44
            }
        ]
    },
    {
        "name": "bar",
        "num": 32,
        "data": [
            {
                "key": "asd",
                "val": 123
            },
            {
                "key": "dsa",
                "val": 13
            }
        ]
    },
    {
        "name": "foobar",
        "num": 11,
        "data": [
            {
                "key": "qwe",
                "val": 94
            },
            {
                "key": "ewq",
                "val": 44
            }
        ]
    },
    {
        "name": "baz",
        "num": 0,
        "data": [
            {
                "key": "qwe",
                "val": 23
            },
            {
                "key": "ewq",
                "val": 67
            }
        ]
    },
    {
        "name": "foobarbaz",
        "num": 50,
        "data": [
            {
                "key": "asd",
                "val": 69
            },
            {
                "key": "asd",
                "val": 96
            }
        ]
    }
]


def test_compare_single_item():
    assert filter_json.compare({"num": 20}, json_input[0])
    assert filter_json.compare({"num": "20"}, json_input[0])
    assert filter_json.compare(">-1", 0)
    assert filter_json.compare({"num": 0}, json_input[3])
    assert filter_json.compare({"name": "foo"}, json_input[0])
    assert filter_json.compare({"num": 0}, json_input[0]) is False
    assert filter_json.compare({"data": {"val": 23}}, json_input[0])
    assert filter_json.compare({"data": {"val": 44}}, json_input[0])


def test_filter_array():
    assert filter_json.filter_array({"num": 20}, json_input) == [json_input[0]]
    assert len(filter_json.filter_array(
        {"num": [">-1", "<33"]},
        json_input)) == 4
    assert filter_json.filter_array(
        {"name": "foo"},
        json_input) == [json_input[0], json_input[2], json_input[4]]
    assert filter_json.filter_array(
        {"num": [">11", "<33"], "data": {"val": ">90"}},
        json_input) == [json_input[1]]
    assert filter_json.filter_array(
        [{"num": [">11", "<33"], "data": {"val": ">90"}}, {"name": "foo"}],
        json_input) \
        == [json_input[1], json_input[0], json_input[2], json_input[4]]
