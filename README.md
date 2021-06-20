# `seamake` - CMake Project Skeleton Generator

This is a skeleton generator, aka cookie cutter, for CMake projects that uses `googletest` for testing. The main subcommands available are `init`, `build` and `target`.

```bash
Usage: seamaker.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  build
  init
  target
```

## `init`: Skeleton Generator

This command sets up the layout sand sample placeholder files once you provide project name and optionally the related libraries that you want to build together along with the dependencies.

```
Usage: seamaker.py init [OPTIONS]

Options:
  -p, --project TEXT
  -l, --lib TEXT      Library that will be developed in this project
  -d, --dep TEXT      Library dependency, system level
  -v, --verbose       Verbosity level of output [no-op]  [x>=0]
  --help              Show this message and exit.

Example:
  seamaker.py init -p "stig" -l "jezza" -l "capn-slow" -l "hamster" -d "dingleberry" -d "handpump"
```

> Here the script assumes, you you are developing multiple library modules and supply a list of names (with `-l` flag), the libraries have dependendency on all the preceeding libraries. And the main task has dependency on all of them. In the example, its implied that, apart from the system level dependencies (`dingleberry` and `handpump`) on all, library `jezza` is independent, `capn-slow` is dependent on `jezza` and `hamster` is dependent on `jezza` and `capn-slow`. And the task `stig` is dependent on all of them.

## `build`: Build Helper

This command helps set up build artifacts using cmake and then make the libraries, tests and executables.

```bash
Usage: seamaker.py build [OPTIONS]

Options:
  -s, --source-root DIRECTORY     CMake source root directory where top
                                  CMakeLists.txt is found
  -b, --build-root DIRECTORY      CMake build root directory  [default: cmake-
                                  build]
  -t, --build-type [Debug|Release|RelWithDebInfo|MinSizeRel]
                                  CMake build type  [default: Release]
  -g, --generator-type [MinGW Makefiles|Unix Makefiles]
                                  Makefile generator type  [default: Unix
                                  Makefiles]
  -w, --dev-warning               Enable dev warnings  [default: False]
  -m, --make-option [no|all|clean|depend|install|list_install_components|test]
                                  Make option, value 'no' skips make
                                  [default: all]
  --help                          Show this message and exit.

Example:
  seamaker.py build -s "." -b "cmake-build" -t "Debug" -g "Unix Makefiles" -w -m "test"
```
## `target`: List `make` Targets

This command lists all the available targets for make for this particular project. `build` subcommand takes an option `-m` which only accepts some common `make` parameters. Here you can see all the applicable targets for your project that you can invoke, like, `make <target>` .

```
Usage: seamaker.py target [OPTIONS]

Options:
  -b, --build-root DIRECTORY  CMake build directory with build artifacts
                              [default: cmake-build]
  --help                      Show this message and exit.

Example:
  seamaker.py target -b "cmake-build"
```

## Enhancements

- Cache `googletest` in case there is no internet connectivity
- Intra library dependency resolution mechanism for the libraries being developed in the project
