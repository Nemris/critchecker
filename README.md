# critchecker

Critchecker is a Python 3.12+ tool that fetches all the critique batches and critiques posted by
Critmas participants, counts the critiques' length, and stores the info in a CSV database.

## Requirements

To run, `critchecker` needs [tqdm] and [sundown]. Installing the .whl file will take care of this
for you.

## Installation

To install `critchecker`, use `pip` and install the distributed .whl file as follows:

```bash
python -m pip install critchecker-X.Y.Z-py3-none-any.whl
```

The tool will then be available as `critchecker` or `critchecker.exe`, depending on your OS.

To avoid polluting your OS, you may opt to install `critchecker` to a virtual environment.
Refer to your system's documentation to create one, then activate it and run the above command from
within the venv.

## Usage

You can view a brief usage message by running:

```bash
critchecker -h
```

The required parameters are the URL of the Critmas launch journal and the Critmas launch date, in
the YYYY-MM-DD format. As such, an example invocation will be:

```bash
critchecker https://www.deviantart.com/beckykidus/journal/Critmas-2023-We-re-off-1005330829 2023-12-26
```

### The CSV file path

You can force a specific path to be used in place of the default one for the CSV file.
For example, to save the critique database in a file called `report.csv` in the current working
directory, use:

```bash
critchecker -r "./report.csv" <url> <startdate>
```

The default location for the CSV file will be either `$HOME/critmas.csv` or
`C:\Users\<username>\critmas.csv`, depending on your OS.

Note that **the target file will be overwritten** if already present when `critchecker` is run.

### Scanning comment text for critique URLs

Compared to previous versions of `critchecker`, current and future versions utilize DeviantArt data
to obtain critique URLs.

To restore the old text-searching behavior _in addition_ to the new one, you can pass the `-s`
flag.

## Building

To build a .whl file for `critchecker`, run the following from the project's root directory:

```bash
poetry build -f wheel
```

The wheel will be placed in the `dist` subdirectory.

### Dev dependencies

To build `critchecker`, you will need [Poetry] to manage project building, virtual environments
and dependencies.

The required dev dependencies are [pylint], [pytest], [hypothesis] and [black].

## Contributing

If you want to contribute, feel encouraged to fork the project, move to the project root and run:

```bash
poetry install
```

This will setup a virtual environment with all the required dependencies.

Moreover, it'll install `critchecker` itself inside the virtualenv, and you'll be able to execute
it with:

```bash
poetry run critchecker
```

Remember to **create a branch for every feature** you want to implement or modify.

**PRs produced as a result of "vibe coding" will be rejected.**

### Code style

This project follows the Black code style, so it's sufficient to run the formatter on your code
prior to contributing it.

Sometimes, it might make sense to have Black avoid cramming multiple lines in one for the sake of
clarity. If your gut says that code would look better on multiple lines, append a trailing comma to
the last line as per the [docs].

Type-annotate both the parameters and return values of your functions and methods, and always add
docstrings to public code.

For the love of all that is dear, **avoid inheritance outside of exception hierarchies or abstract
base classes**.
Likewise, **do not use global variables**, although global "constants" are fine.

Preferably, use the imperative tense in your commit titles, and make sure their length is 50 chars
max. Use the body if you feel more details ought to be saved for context.

### Linting

Before issuing a PR, **ensure that Pylint does not raise any warning apart from TODOs**.

If you feel the need to silence a warning, **leave a comment explaining your reasons**, or mention
the rationale in the commit message.

To lint a file, use:

```bash
poetry run pylint <file>
```

### Unit testing

While not mandatory, I'd appreciate it if you **added a Hypothesis-based unit test for every
function you write**. Subscribing to test-driven development isn't mandatory, though, and writing
tests a posteriori is still better than having none at all.

In case property-based testing isn't your cup of tea, ping me and I'll write the unit test.

To run the tests, use:

```bash
poetry run pytest
```

If you also want statistics on how Hypothesis spends time, use:

```bash
poetry run pytest --hypothesis-show-statistics
```

## Credits

This tool wouldn't exist if not for a certain [BeckyKidus] - it's thanks to this noodle's
encouragement and typo-spotting sight if `critchecker` was even ready for Critmas 2020.
Checking out their art is highly recommended.

A thank you goes to [neurotype] too - as the Critmas 2020 host, she sure had a say on this tool's
database format.

## License

This program is licensed under the terms of the [MIT] license.

Check [LICENSE.txt] for further info.


[tqdm]:https://tqdm.github.io/
[sundown]:https://github.com/Nemris/sundown

[poetry]:https://python-poetry.org/
[pylint]:https://pylint.readthedocs.io/
[pytest]:https://pytest.org/
[hypothesis]:https://hypothesis.readthedocs.io/
[black]:https://black.readthedocs.io/

[docs]:https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html#the-magic-trailing-comma

[BeckyKidus]:https://www.deviantart.com/beckykidus
[neurotype]:https://www.deviantart.com/neurotype

[MIT]:https://choosealicense.com/licenses/mit/
[LICENSE.txt]:./LICENSE.txt
