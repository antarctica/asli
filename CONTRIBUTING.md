# Contributing
We welcome contributions and improvements to this package!

Please submit bug reports and feature requests as issues [on the GitHub repo](https://github.com/antarctica/asli/issues/new).

## Contributing Guide

When making changes to the source code (including to the docs):

1. Fork this repository on GitHub.
1. Clone the package to your computer: `git clone https://github.com/<your-username>/asli`
1. Inside a virtual environment, install the package as an editable pip install: `pip install -e asli` (where `asli` is the relative path to the cloned repository).
1. Also install the development dependency groups: `pip install --group test --group docs --group dev`.
1. Make your changes and run the tests using pytest: `pytest` and/or test the docs build using `mkdocs build`.
1. Commit and push your changes to GitHub and open a pull request to the main repo.


## Maintainer Guide

These instructions are intended for the maintainers.

### Changelog

+ Ensure that changes are recorded in the changelog under the `[Unreleased]` section with appropriate headings, e.g. "Breaking Changes", "Fixed", "Added", "Removed".

### Testing

+ Tests must be run manually, GitHub actions are not enabled on this repository. Do so with `pytest`

### Release Management

+ In `CHANGELOG.md` create a new heading for all the unreleased changes, with the version and date.
+ Add a new tag, beginning with `v`, following [semantic versioning](https://semver.org/) practices.
+ On GitHub, create a new release. Copy in the changes from the changelog.


### Publishing to PyPI

+ Install the build dependencies `pip install --group build`
+ **With no uncommitted changes and with the correct tag checked out** run `python -m build` - this will build to `dist/`
+ Run `twine check dist/bas_asli-X.Y.Z*` where `X.Y.Z` is the version to publish.
+ Run `twine upload dist/bas_asli-X.Y.Z*` (you will need to authenticate with PyPI).

### Publishing the docs

+ To publish the documentation to GitHub pages, run `mkdocs gh-deploy`.
