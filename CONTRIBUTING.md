# Contributing
We welcome contributions and improvements to this package!

Please submit bug reports and feature requests as issues [on the GitHub repo](https://github.com/scotthosking/amundsen-sea-low-index/issues/new).

## Developer Guide

When making changes to the source code (including to the docs):

1. Fork this repository on GitHub,
1. Clone the package to your computer: `git clone https://github.com/<your-username>/amundsen-sea-low-index`
1. Inside a virtual environment, install the package as an editable pip install: `pip install -e amundsen-sea-low-index` (where `amundsen-sea-low-index` is the relative path to the cloned repository),
1. Also install the development dependency groups: `pip install --group test --group docs --group dev`
1. Make your changes and run the tests using pytest: `pytest` and/or test the docs build using `jupyter-book build docs/`
1. Commit and push your changes to GitHub and open a pull request to the main repo.
