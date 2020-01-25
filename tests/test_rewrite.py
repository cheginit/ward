import ast

from tests.test_suite import testable_test
from ward import test, fixture, raises
from ward.expect import TestFailure, assert_equal, assert_not_equal
from ward.rewrite import rewrite_assertions_in_tests, RewriteAssert
from ward.testing import Test, each


@testable_test
def passing_fn():
    assert 1 == 1


@testable_test
def failing_fn():
    assert 1 == 2


@fixture
def passing():
    yield Test(
        fn=passing_fn, module_name="m", id="id-pass",
    )


@fixture
def failing():
    yield Test(
        fn=failing_fn, module_name="m", id="id-fail",
    )


@test("{func.__name__}({lhs}, {rhs}) is None")
def _(
    func=each(assert_equal, assert_not_equal),
    lhs=each(1, 1),
    rhs=each(1, 2),
):
    assert func(lhs, rhs, "") is None


@test("{func.__name__}({lhs}, {rhs}) raises TestFailure")
def _(
    func=each(assert_equal, assert_not_equal),
    lhs=each(1, 1),
    rhs=each(2, 1),
):
    with raises(TestFailure):
        func(lhs, rhs, "")


@test("rewrite_assertions_in_tests returns all tests, keeping metadata")
def _(p=passing, f=failing):
    in_tests = [p, f]
    out_tests = rewrite_assertions_in_tests(in_tests)

    def meta(test):
        return (test.description, test.id, test.module_name, test.fn.ward_meta)

    assert [meta(test) for test in in_tests] == [meta(test) for test in out_tests]


@test("RewriteAssert.visit_Assert doesn't transform `{src}`")
def _(
    src=each(
        "assert x",
        "assert x is y",
        "assert f(x)",
        "assert x + y + z",
        "assert 2 > 1",
        "assert 1 < 2 < 3",
        "assert 1 == 1 == 3",
        "print(x)",
        "yield",
    )
):
    in_tree = ast.parse(src).body[0]
    out_tree = RewriteAssert().visit(in_tree)
    assert in_tree == out_tree


@test("RewriteAssert.visit_Assert transforms `{src}` correctly")
def _(
    src=each("assert x == y", "assert x != y", "assert x in y"),
    fn=each("assert_equal", "assert_not_equal", "assert_in"),
):
    in_tree = ast.parse(src).body[0]
    out_tree = RewriteAssert().visit(in_tree)

    assert out_tree.lineno == in_tree.lineno
    assert out_tree.col_offset == in_tree.col_offset
    assert out_tree.value.lineno == in_tree.lineno
    assert out_tree.value.col_offset == in_tree.col_offset
    assert out_tree.value.func.id == fn
    assert out_tree.value.args[0].id == "x"
    assert out_tree.value.args[1].id == "y"
    assert out_tree.value.args[2].s == ""


@test("RewriteAssert.visit_Assert transforms `{src}`")
def _(src="assert 1 == 2, 'msg'"):
    in_tree = ast.parse(src).body[0]
    out_tree = RewriteAssert().visit(in_tree)
    assert out_tree.value.args[2].s == "msg"
