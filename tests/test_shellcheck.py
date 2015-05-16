import os
from nose.tools import *
from nose.plugins.attrib import attr
from mock import MagicMock as Mock
from reviewbotshellcheck.shellcheck import *

test_data_path = os.path.join(os.path.dirname(__file__), "testdata")


class TestViolation(object):

    def setup(self):
        self.violation = Violation(
            line=2,
            text='Double quote to prevent globbing and word splitting.',
            rule='SC2086')


    def test_url(self):
        assert_equals(
            self.violation.url,
            'https://github.com/koalaman/shellcheck/wiki/SC2086')

    def test_repr(self):
        assert_equals(self.violation, eval(repr(self.violation)))


class TestResult(object):

    def test_result_from_xml_no_errors(self):
        result_path = os.path.join(test_data_path, "no_errors.xml")
        with open(result_path, 'r') as f:
            result = Result.from_xml(f.read(), "test.sh")
            assert_equals(result.source_file_path, "test.sh")
            assert_equals(len(result.violations), 0)

    def test_result_from_xml_with_errors(self):
        result_path = os.path.join(test_data_path, "errors.xml")
        with open(result_path, 'r') as f:
            result = Result.from_xml(f.read(), "test.sh")
            expected_violations = [
                Violation(
                    line=2,
                    text='Double quote to prevent globbing '
                         'and word splitting.',
                    rule='SC2086'),
                Violation(
                    line=17,
                    text='The double quotes around this do nothing. '
                         'Remove or escape them.',
                    rule='SC2140')
            ]
            assert_items_equal(expected_violations, result.violations)


class TestShellCheckTool(object):

    def setup(self):
        self.shellcheck = ShellCheckTool()
        default_settings = {
            'markdown': False,
        }
        self.shellcheck.settings = default_settings
        self.test_violations = [
            Violation(
                line=2,
                text='Double quote to prevent globbing '
                     'and word splitting.',
                rule='SC2086'),
            Violation(
                line=17,
                text='The double quotes around this do nothing. '
                     'Remove or escape them.',
                rule='SC2140')
        ]

    @attr('slow')
    def test_run_shellcheck_creates_valid_shellcheck_result(self):
        valid_source_path = os.path.join(test_data_path, "testscript.sh")
        result = self.shellcheck.run_shellcheck(valid_source_path)
        expected_violation = Violation(
            line=1,
            text="Double quote to prevent globbing and word splitting.",
            rule="SC2086")
        assert_equals(result.source_file_path, valid_source_path)
        assert_items_equal(result.violations, [expected_violation])

    def test_run_shellcheck_with_invalid_source_file(self):
        invalid_source_path = os.path.join(test_data_path, "doesntexist.sh")
        with assert_raises(ShellCheckError):
            self.shellcheck.run_shellcheck(invalid_source_path)

    def test_handle_file_non_shell_file(self):
        self.shellcheck.is_shell_or_bash_script = Mock(return_value=False)
        reviewed_file = Mock()
        assert_false(self.shellcheck.handle_file(reviewed_file))

    def test_handle_file_shell_file(self):
        self.shellcheck.is_shell_or_bash_script = Mock(return_value=True)
        shellcheck_result = Mock()
        self.shellcheck.run_shellcheck = Mock(return_value=shellcheck_result)
        self.shellcheck.post_comments = Mock()
        self.shellcheck.settings = {'markdown': True}
        reviewed_file = Mock()
        assert_true(self.shellcheck.handle_file(reviewed_file))
        self.shellcheck.post_comments.assert_called_with(
            shellcheck_result.violations,
            reviewed_file,
            use_markdown=True)

    def test_is_shell_or_bash_script_file_with_extension(self):
        assert_true(self.shellcheck.is_shell_or_bash_script("test.sh"))

    def test_is_shell_or_bash_script_file_with_sh_shebang(self):
        file_with_shebang_path = os.path.join(
            test_data_path, "bash_shebang")
        assert_true(
            self.shellcheck.is_shell_or_bash_script(file_with_shebang_path))

    def test_is_shell_or_bash_script_file_with_bash_shebang(self):
        file_with_shebang_path = os.path.join(
            test_data_path, "shell_shebang")
        assert_true(
            self.shellcheck.is_shell_or_bash_script(file_with_shebang_path))

    def test_is_shell_or_bash_script_other_file(self):
        empty_file_path = os.path.join(
            test_data_path, "emptyfile")
        assert_false(
            self.shellcheck.is_shell_or_bash_script(empty_file_path))

    def test_is_shell_or_bash_script_invalid_file(self):
        empty_file_path = os.path.join(
            test_data_path, "doesntexist")
        assert_false(
            self.shellcheck.is_shell_or_bash_script(empty_file_path))

    def test_post_comments_comment_plain_text(self):
        reviewed_file = Mock()
        violation = Mock()
        self.shellcheck.post_comments(
            [violation], reviewed_file, use_markdown=False)
        reviewed_file.comment.assert_called_with(
            "%s: %s\n\nMore info: %s" %
            (violation.rule, violation.text, violation.url),
            violation.line,
            1,
            issue=False)

    def test_post_comments_comment_markdown(self):
        reviewed_file = Mock()
        violation = Mock()
        self.shellcheck.post_comments(
            [violation], reviewed_file, use_markdown=True)
        reviewed_file.comment.assert_called_with(
            "[%s](%s): %s" %
            (violation.rule, violation.url, violation.text),
            violation.line,
            1,
            issue=False)

