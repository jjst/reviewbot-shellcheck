import logging
import subprocess
import os
import magic
import xml.etree.ElementTree as ElementTree

from reviewbot.tools import Tool
from reviewbot.utils import is_exe_in_path
import reviewbot.processing.review as review

from rbtools.api.request import APIError

wiki_url = 'https://github.com/koalaman/shellcheck/wiki/'


class FileWithMarkdownSupport(review.File):
    def _comment(self, text, first_line, num_lines, issue):
        """Add a comment to the list of comments."""
        data = {
            'filediff_id': self.id,
            'first_line': first_line,
            'num_lines': num_lines,
            'text': text,
            'issue_opened': issue,
            'text_type': 'markdown'
        }
        self.review.comments.append(data)

# Monkey-patch File to add markdown support
review.File = FileWithMarkdownSupport


class ShellCheckError(Exception):
    pass


class ShellCheckTool(Tool):
    name = 'ShellCheck'
    version = '0.1.0'
    description = ("A Review Bot tool that runs ShellCheck, "
                   "a static analysis tool for bash/shell scripts")
    options = [
        {
            'name': 'markdown',
            'field_type': 'django.forms.BooleanField',
            'default': False,
            'field_options': {
                'label': 'Enable Markdown',
                'help_text': 'Allow ReviewBot to use Markdown in the '
                             'review body and for comments.',
                'required': False,
            },
        }
    ]

    def check_dependencies(self):
        # We need java installed to run PMD
        return is_exe_in_path('shellcheck')

    def is_shell_or_bash_script(self, file_path):
        _, ext = os.path.splitext(file_path)
        if ext == '.sh':
            return True
        try:
            mime_type = magic.from_file(file_path, mime=True)
        except IOError:
            return False
        return mime_type == 'text/x-shellscript'

    def handle_file(self, reviewed_file):
        if not self.is_shell_or_bash_script(reviewed_file.dest_file):
            # Ignore the file.
            return False

        logging.debug('ShellCheck will start analyzing file %s' %
                      reviewed_file.dest_file)
        # Careful: get_patched_file_path() returns a different result each
        # time it's called, so we need to cache this value.
        try:
            temp_source_file_path = reviewed_file.get_patched_file_path()
        except APIError:
            logging.warn("Failed to get patched file for %s - ignoring file" %
                         reviewed_file.source_file)
            return False
        if not temp_source_file_path:
            return False

        try:
            result = self.run_shellcheck(temp_source_file_path)
        except (ShellCheckError, ValueError) as e:
            logging.error(e)
            return False
        logging.info('ShellCheck detected %s violations in file %s' %
                     (len(result.violations), reviewed_file.dest_file))
        self.post_comments(
            result.violations, reviewed_file, use_markdown=self.settings['markdown'])
        return True

    def run_shellcheck(self, source_file_path):
        args = (
            'shellcheck',
            source_file_path,
            '-f', 'checkstyle',
        )
        process = subprocess.Popen(args,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if stderr:
            raise ShellCheckError(
                "Error running shellcheck command line tool, "
                "command output:\n" + stderr)
        return Result.from_xml(stdout, source_file_path)

    def post_comments(self, violations, reviewed_file, use_markdown=False):
        for v in violations:
            if use_markdown:
                comment = "[%s](%s): %s" % (v.rule, v.url, v.text)
            else:
                comment = "%s: %s\n\nMore info: %s" % (v.rule, v.text, v.url)
            reviewed_file.comment(comment, v.line, 1, issue=False)


class Violation(object):

    def __init__(self, line, text, rule):
        self.line = line
        self.text = text
        self.rule = rule
        self.url = wiki_url + self.rule

    def __key(self):
        return (self.line, self.text, self.rule)

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

    def __repr__(self):
        return "Violation(line=%i, text='%s', rule='%s')" % \
               (self.line, self.text, self.rule)


class Result(object):

    def __init__(self, source_file_path, violations=None):
        self.source_file_path = source_file_path
        self.violations = set(violations or [])

    @staticmethod
    def from_xml(xml_result, source_file_path):
        root = ElementTree.fromstring(xml_result)
        files = root.findall('file')
        if len(files) > 1:
            raise ValueError("Result should contain results "
                             "for one and only one file")
        file_elem = files.pop()
        file_name = file_elem.attrib['name']
        if file_name != source_file_path:
            raise ValueError("Result does not contain results for file %s"
                             % source_file_path)
        result = Result(source_file_path=file_name)
        errors = file_elem.findall('error')
        for error in errors:
            line = int(error.attrib['line'])
            message = error.attrib['message']
            _, rule = error.attrib['source'].split('.')
            result.violations.add(Violation(line, message, rule))
        return result
