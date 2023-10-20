# critchecker

Critchecker is a Python 3.11+ tool that fetches all the critique blocks and
critiques posted by Critmas participants, counts the critique length, and
stores the info in a CSV database.

The blocks are sorted by newest, and the critique URL order is preserved.

## Requirements

To run, `critchecker` needs [beautifulsoup4], [tqdm] and [aiohttp].
Install them with:

```bash
python3 -m pip install beautifulsoup4 tqdm aiohttp
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
`critchecker` is run.

## Building

To build `critchecker`, run the following from the project's root directory:

```bash
poetry build
```

This will build both the sdist and the wheel, placing them in the `dist`
subdirectory.

### Build dependencies

To build `critchecker`, you will need [Poetry] to manage project building,
virtual environments and dependencies.

## Contributing

If you want to contribute, feel encouraged to fork the project, move to the
project root and run:

```bash
poetry install
```

This will setup a virtual environment with all the required dependencies,
including [pylint], [pytest] and [hypothesis].
Moreover, it'll make `critchecker` itself be installed inside the virtualenv,
and thus executable with:

```bash
poetry run critchecker
```

Remember to **create a branch for every change** you want to implement or
modify.

### Code style

Use 4-spaces wide indentation, and type annotate every parameter and return
type in function definitions.

Always write a docstring for the functions you create. When in doubt, check the
existing code.

For the love of all that is dear, **avoid inheritance outside of exception
hierarchies**. Likewise, **do not use global variables**, although global
"constants" are fine.

Use the imperative tense in your commit titles, and make sure their length is
50 characters max.

### Linting

Before issuing a PR, **ensure that Pylint does not raise any warning apart from
TODOs**.
If you feel the need to silence a warning, **leave a comment explaining your
reasons**, or mention the rationale in the commit message.

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

This tool wouldn't exist if not for a certain [BeckyKidus] - it's thanks to
this noodle's encouragement and typo-spotting sight if `critchecker` was even
ready for Critmas 2020.
Checking out her art is highly recommended.

A thank you goes to [neurotype] too - as the Critmas 2020 host, she sure had
a say on this tool's database format.

## License

This program is licensed under the terms of the [MIT] license.

Check [LICENSE.txt] for further info.


[beautifulsoup4]:https://www.crummy.com/software/BeautifulSoup/
[tqdm]:https://tqdm.github.io/
[aiohttp]:https://docs.aiohttp.org/
[poetry]:https://python-poetry.org/
[pylint]:https://pylint.readthedocs.io/
[pytest]:https://pytest.org/
[hypothesis]:https://hypothesis.readthedocs.io/
[BeckyKidus]:https://www.deviantart.com/beckykidus
[neurotype]:https://www.deviantart.com/neurotype
[MIT]:https://choosealicense.com/licenses/mit/
[LICENSE.txt]:./LICENSE.txt
