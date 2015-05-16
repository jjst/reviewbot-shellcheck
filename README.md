ShellCheck plugin for ReviewBot
========================

reviewbot-shellcheck is a plugin for [ReviewBot](https://github.com/reviewboard/ReviewBot) to automatically run
ShellCheck on bash scripts submitted for review to a [Review Board](https://www.reviewboard.org/) instance.

[ShellCheck](http://www.shellcheck.net/) is an automatic shell script analysis tool.

Installation
============

This plugin requires an up-and-running ReviewBoard instance, with the ReviewBot extension enabled and the ReviewBot
worker running. See the [ReviewBot installation instructions](https://github.com/reviewboard/ReviewBot#installation)
for more information.

You will also need ShellCheck. See the [official ShellCheck website](http://www.shellcheck.net/about.html) for
installation instructions.

To install the plugin, run the following commands:

```bash
git clone git://github.com/jjst/reviewbot-shellcheck.git
cd reviewbot-shellcheck
python setup.py install
```

Now that the tool has been installed, it must be registered with the Review Bot extension. To do so, follow these
instructions:

1.  Go to the extension list in the Review Board admin panel.
2.  Click the **Database** button for the Review Bot extension.
3.  Click the **Review bot tools** link.
4.  Click **Refresh installed tools** in the upper right of the page.

The **ShellCheck** tool should now be listed in the Review Bot available tools list.

Configuration
=============

You can access reviewbot-shellcheck's configuration options by clicking on the tool name under the **Review bot tools**
page. The following configuration options are available:

* **Enable Markdown**: if enabled then PMD will post its comments using [rich
  text](https://www.reviewboard.org/docs/manual/2.0/users/markdown/). Note that this is an experimental feature that
  needs a [custom version of ReviewBot](https://github.com/jjst/ReviewBot/tree/markdown-support) with Markdown support.
