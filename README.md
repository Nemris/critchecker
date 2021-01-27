# critchecker

Critchecker is a Python 3.9+ tool that fetches all the critique blocks and
critiques posted by Critmas participants, counts the critique length, and
stores the info in a CSV database.

The blocks are sorted by newest, and the critique URL order is preserved.

## Requirements

To run `critchecker`, you'll need [bs4][1] and [aiohttp][2].
Install them with:

```bash
python3 -m pip install bs4 aiohttp
```

Installing the dependencies manually is not required if you install
`critchecker` via the .whl file.

## Installation

To install `critchecker`, use `pip` and install the distributed .whl file with
the following command:

```bash
python3 -m pip install critchecker-X.Y.Z-py3-none-any.whl
```

The tool will then be available as `critchecker` or `critchecker.exe`,
depending on your OS of choice.

## Usage

It's possible to display a brief usage message by running:

```bash
critchecker -h
```

The only required parameter is the URL of the Critmas launch journal. As such,
an example invocation will be:

```bash
critchecker "https://www.deviantart.com/neurotype/journal/Critmas-2020-HERE-WE-GO-864966965"
```

**At present, `critchecker` is very slow - the cause has been identified and
will be fixed in the next major release.**

### The CSV file path

It's possible to force a specific path to be used in place of the default one
for the CSV file.
For example, to save the critique database in a file called `report.csv` in the
local directory, use:

```bash
critchecker -r "./report.csv" <url>
```

As usual, replace `<url>` with the actual Critmas launch journal URL.

The default location for the CSV file will be either `$HOME/critmas.csv` or
`C:\Users\<username>\critmas.csv`, depending on your OS of choice.

Note that **the target file will be overwritten** if already present when
`critchecker` is ran.

## Building

To build `critchecker`, run the following from the project's root directory:

```bash
poetry build
```

This will build both the sdist and the wheel, placing them in the `dist`
subdirectory.

### Build dependencies

To build `critchecker`, you will need [poetry][3] to manage project building,
virtual environments and dependencies.

## Contributing

If you want to contribute, feel encouraged to fork the project, move to the
project root and run:

```bash
poetry install
```

This will setup a virtual environment with all the required dependencies,
including [pylint][4], [pytest][5] and [hypothesis][6].
Moreover, it'll make `critchecker` itself be installed inside the virtualenv,
and thus executable with:

```bash
poetry run critchecker
```

Remember to **create a branch for every change** you want to implement or
modify. For examples, use the following command to check the commit log:

```bash
git log --graph
```

### Code style

Use 4-spaces wide indentation, and type annotate every parameter and return
type in function definitions.

Always write a docstring for the functions you create. When in doubt, check the
existing code.

For the love of all that is dear, **avoid classes**. Use dataclasses if
representing a complex object, but resort to functions for the actual logic.
Functional programming-like functions with as little side-effects as possible
make testing and importing modules easier.

Use the imperative tense in your commit titles, and make sure their length is
50 characters max.

### Linting

Before issuing a PR, **ensure that Pylint does not raise any warning apart from
TODOs**.
If you feel the need to silence a warning, **leave a comment explaining your
reasons**.

To lint a file, use:

```bash
poetry run pylint <file>
```

Remember - Pylint is our friend, not our enemy.

### Unit testing

While not mandatory, I'd appreciate it if you **added a Hypothesis-based unit
test for every function you write**, save for those dealing with the network.
In case property-based testing isn't your cup of tea, ping me and I'll write
the unit test.

To run the tests, use:

```bash
poetry run pytest
```

If you also want statistics on how Hypothesis spends time, use:

```bash
poetry run pytest --hypothesis-show-statistics
```

## Credits

This tool wouldn't exist if not for a certain [BeckyKidus][7] - it's thanks
to this noodle's encouragement and typo-spotting sight if `critchecker` was
even ready for Critmas 2020.
Checking out her art is highly recommended.

A thank you goes to [neurotype][8] too - as the Critmas 2020 host, she sure had
a say on this tool's database format.

## License

This program is licensed under the terms of the [MIT][9] license.

Check [LICENSE.txt][10] for further info.


[1]:https://www.crummy.com/software/BeautifulSoup/bs4/doc/
[2]:https://docs.aiohttp.org/
[3]:https://python-poetry.org/
[4]:https://www.pylint.org/
[5]:https://pytest.org/
[6]:https://hypothesis.readthedocs.io/
[7]:https://www.deviantart.com/beckykidus
[8]:https://www.deviantart.com/neurotype
[9]:https://choosealicense.com/licenses/mit/
[10]:./LICENSE.txt
