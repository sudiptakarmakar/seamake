import click
import collections
import os
import shlex
import subprocess


CMAKE_LISTS = "CMakeLists.txt"
ROOT_DIR = "."
SRC_DIR = f"{ROOT_DIR}/src"
APP_DIR = f"{ROOT_DIR}/src/app"
LIBS_DIR = f"{ROOT_DIR}/src/libs"
EXT_LIBS_DIR = "src/extlibs"
ROOT_CMAKELIST = f"{ROOT_DIR}/{CMAKE_LISTS}"
SRC_CMAKELIST = f"{SRC_DIR}/{CMAKE_LISTS}"
APP_CMAKELIST = f"{APP_DIR}/{CMAKE_LISTS}"
LIBS_CMAKELIST = f"{LIBS_DIR}/{CMAKE_LISTS}"
EXT_LIBS_CMAKELIST = f"{EXT_LIBS_DIR}/{CMAKE_LISTS}"
LIB_SUFFIX = "module"


def execute(cmds, silent=False):
    if not silent:
        print("$", " | ".join(cmds))
    proc = subprocess.Popen(shlex.split(cmds[0]), stdout=subprocess.PIPE)
    for cmd in cmds[1:]:
        proc = subprocess.Popen(
            shlex.split(cmd), stdin=proc.stdout, stdout=subprocess.PIPE
        )
    try:
        pass
    except subprocess.CalledProcessError as e:
        pass


def silent_execute(cmds):
    collections.deque(execute(cmds), maxlen=0)


def is_file_empty(path):
    cmd = f"touch {path}"
    os.system(cmd)
    return os.stat(path).st_size == 0


def create_root_dir_cmakelist(
    project, file_path=ROOT_CMAKELIST, version=1.0, cpp=14, cmake_version="3.12"
):
    template = f"""cmake_minimum_required(VERSION {cmake_version})

project({project} VERSION {version})

# specify the C++ standard
set(CMAKE_CXX_STANDARD {cpp})
set(CMAKE_CXX_STANDARD_REQUIRED True)

enable_testing()

include(ExternalProject)
include(CMakeDependentOption)
include(GoogleTest)

add_subdirectory(src)
"""
    if not is_file_empty(file_path):
        print(f"File '{file_path}' already exists, not touched")
        return
    with open(file_path, "a") as fd:
        fd.write(template)


def create_src_dir_cmakelist(project, file_path=SRC_CMAKELIST, version=1.0, cpp=14):
    src_dir_subdirs = (EXT_LIBS_DIR, LIBS_DIR, APP_DIR)
    template = "".join(
        f"add_subdirectory({d.rsplit('/', maxsplit=1)[-1]})\n" for d in src_dir_subdirs
    )
    if not is_file_empty(file_path):
        print(f"File '{file_path}' already exists, not touched")
        return
    with open(file_path, "a") as fd:
        fd.write(template)


def create_libs_dir_cmakelist(project, libs, file_path=LIBS_CMAKELIST):
    template = [f"add_subdirectory({lib})\n" for lib in libs]
    if not is_file_empty(file_path):
        print(f"File '{file_path}' already exists, not touched")
        return
    with open(file_path, "a") as fd:
        fd.writelines(template)


def create_individual_lib_cmakelist(lib, deps, public_deps, file_path):
    private_deps = " ".join(deps)
    public_deps = " ".join(public_deps)

    link_deps = ""
    # public dependencies go first
    if len(public_deps) > 0:
        link_deps += f"\ntarget_link_libraries(${{LIB_NAME}} PUBLIC {public_deps})"
    if len(private_deps) > 0:
        link_deps += f"\ntarget_link_libraries(${{LIB_NAME}} PRIVATE {private_deps})"

    template = f"""set(LIB_NAME {lib})
set(LIB_TEST_NAME ${{LIB_NAME}}.tests)

file(GLOB_RECURSE LIB_SRC_FILES
    *.h
    *.cpp
)
list(FILTER LIB_SRC_FILES EXCLUDE REGEX ".t.cpp$")
add_library(${{LIB_NAME}} ${{LIB_SRC_FILES}})
{link_deps}
target_include_directories(${{LIB_NAME}} PUBLIC ${{CMAKE_CURRENT_SOURCE_DIR}})

file(GLOB_RECURSE LIB_TEST_FILES
    *.t.cpp
)
add_executable(${{LIB_TEST_NAME}} ${{LIB_TEST_FILES}})
target_link_libraries(${{LIB_TEST_NAME}} PUBLIC gtest gtest_main gmock gmock_main)
target_link_libraries(${{LIB_TEST_NAME}} PRIVATE ${{LIB_NAME}})
gtest_discover_tests(${{LIB_TEST_NAME}})
"""
    if not is_file_empty(file_path):
        print(f"File '{file_path}' already exists, not touched")
        return
    with open(file_path, "a") as fd:
        fd.writelines(template)


def create_all_lib_cmakelists(proj, libs, public_deps):
    for i in range(len(libs)):
        lib = libs[i]
        deps = libs[:i]
        file_path = f"{LIBS_DIR}/{lib}/{CMAKE_LISTS}"
        create_individual_lib_cmakelist(lib, deps, public_deps, file_path)


def create_ext_libs_dir_cmakelist(proj, ext_libs, file_path=EXT_LIBS_CMAKELIST):
    template = [f"add_subdirectory({lib})\n" for lib in ext_libs]
    if not is_file_empty(file_path):
        print(f"File '{file_path}' already exists, not touched")
        return
    with open(file_path, "a") as fd:
        fd.writelines(template)


def create_googletest_submodule(ext_lib_path=EXT_LIBS_DIR, version="1.11.0"):
    """This only works if the directory has git initialized"""
    googletest = "git@github.com:google/googletest.git"
    target = f"{ext_lib_path}/googletest"
    submodule_add = "git submodule add"
    submodule_cmd = f"{submodule_add} {googletest} {target}"
    silent_execute((submodule_cmd,))
    submodule_update = "git submodule update --init --recursive"
    silent_execute((submodule_update,))


def copy_googletest_ext_lib(lib_path=EXT_LIBS_DIR, version="1.11.0"):
    """In case the link to the googletest turns out to be not reliable or
    the default version is deprecated, deleted, you can always use this
    "https://github.com/google/googletest/archive/refs/heads/master.zip"
    This will keep you always in the bleeding edge. Downside is you may
    get cuts buy the sharp edges.
    """
    target = "googletest"
    repository = "https://github.com/google/googletest"
    release = f"release-{version}.zip"
    url = f"{repository}/archive/refs/tags/{release}"
    target_dir = f"{lib_path}/{target}"
    dl_zip = f"{target_dir}.zip"
    dl_cmd = f"wget -q -c {url} -O {dl_zip}"
    os.system(dl_cmd)

    uz_cmd = f"unzip -qq {dl_zip} -d {lib_path}"
    rm_cmd = f"rm {dl_zip}"
    mv_cmd = f"mv {target_dir}-* {target_dir}"
    os.system(f"{uz_cmd} && {rm_cmd} && {mv_cmd}")


def dummy_copy_googletest_ext_lib(lib_path=EXT_LIBS_DIR, version="1.11.0"):
    cmd = f"cp -r googletest {lib_path}"
    os.system(cmd)


def create_ext_lib_modules(proj, ext_libs, ext_lib_path=EXT_LIBS_DIR):
    ext_libs_creator_map = {
        "googletest": copy_googletest_ext_lib,
    }
    for lib in ext_libs:
        ext_libs_creator_map.get(
            lib,
            lambda *a, **kw: print(
                f"Error: unknown external library - '{lib}', not created in {ext_lib_path}"
            ),
        )(ext_lib_path)


def create_task_cmakelist(project, libs, file_path=APP_CMAKELIST):
    dependencies = " ".join(libs)
    template = f"""set(TASK_NAME {project}.${{CMAKE_HOST_SYSTEM_PROCESSOR}}.tsk)
add_executable(${{TASK_NAME}} {project}.m.cpp)
target_link_libraries(${{TASK_NAME}} PRIVATE {dependencies})
"""
    if not is_file_empty(file_path):
        print(f"File '{file_path}' already exists, not touched")
        return
    with open(file_path, "a") as fd:
        fd.write(template)


def create_cmakelist_structure(
    proj, libs=(), ext_libs=(), common_dirs=(APP_DIR, LIBS_DIR, EXT_LIBS_DIR)
):
    def create_directories(dirs):
        for d in dirs:
            os.system(f"mkdir -p {d}")

    def create_cmakelists(dirs):
        for d in dirs:
            os.system(f"touch {d}/{CMAKE_LISTS}")

    dirs = list(common_dirs)
    for lib in libs:
        dirs.append(f"{LIBS_DIR}/{lib}")
    # The external libraries are cleated separately
    # for lib in ext_libs:
    #     dirs.append(f"{EXT_LIBS_DIR}/{lib}")
    create_directories(dirs)
    cmakelist_locations = [ROOT_DIR, SRC_DIR] + dirs
    create_cmakelists(cmakelist_locations)
    return [f"{d}/{CMAKE_LISTS}" for d in cmakelist_locations]


def fill_in_cmakelists(proj, libs, public_deps, ext_libs):
    create_root_dir_cmakelist(proj)
    create_src_dir_cmakelist(proj)
    create_libs_dir_cmakelist(proj, libs)
    create_all_lib_cmakelists(proj, libs, public_deps)
    create_ext_libs_dir_cmakelist(proj, ext_libs)
    create_ext_lib_modules(proj, ext_libs)
    create_task_cmakelist(proj, libs)


def create_single_lib_h(lib, suffix=LIB_SUFFIX, directory=LIBS_DIR):
    file_name = f"{lib}_{suffix}.h"
    file_path = f"{directory}/{lib}/{file_name}"
    header_guard = f"included_{lib}_{suffix}_h".upper()

    template = f"""
#ifndef {header_guard}
#define {header_guard}

int add_from_{lib}(int a, int b);

#endif
"""
    if not is_file_empty(file_path):
        print(f"File '{file_path}' already exists, not touched")
        return
    with open(file_path, "a") as fd:
        fd.write(template)


def create_single_lib_cpp(lib, suffix=LIB_SUFFIX, directory=LIBS_DIR):
    include_header = f"{lib}_{suffix}.h"
    file_name = f"{lib}_{suffix}.cpp"
    file_path = f"{directory}/{lib}/{file_name}"

    template = f"""#include <{include_header}>

int add_from_{lib}(int a, int b)
{{
    return a + b;
}}
"""
    if not is_file_empty(file_path):
        print(f"File '{file_path}' already exists, not touched")
        return
    with open(file_path, "a") as fd:
        fd.write(template)


def create_single_lib_cpp_test(lib, suffix=LIB_SUFFIX, directory=LIBS_DIR):
    include_header = f"{lib}_{suffix}.h"
    file_name = f"{lib}_{suffix}.t.cpp"
    file_path = f"{directory}/{lib}/{file_name}"
    template = f"""#include <gtest/gtest.h>
#include <{include_header}>

TEST({lib.capitalize()}{suffix.capitalize()}, DummyTest) {{
    EXPECT_EQ(9, add_from_{lib}(4, 5));
}}
"""
    if not is_file_empty(file_path):
        print(f"File '{file_path}' already exists, not touched")
        return
    with open(file_path, "a") as fd:
        fd.write(template)


def create_cpp_main(proj, libs, suffix=LIB_SUFFIX, directory=APP_DIR):
    headers = ""
    code = ""
    for i, lib in enumerate(libs):
        header = f"{lib}_{suffix}.h"
        headers = f"{headers}#include <{header}>\n"
        a = i + 2
        b = i + 4
        eqn = f"add_from_{lib}({a}, {b})"
        txt = f'"{a} + {b} using {lib}_{suffix}.h = "'
        line = f"std::cout << {txt} << {eqn} << std::endl;"
        code = f"{code}    {line}\n"

    template = f"""#include <iostream>
{headers}

int main(int argc, char** argv)
{{
    std::cout << "Hello, world!" << std::endl;
{code}
    return 0;
}}
"""
    file_path = f"{directory}/{proj}.m.cpp"
    if not is_file_empty(file_path):
        print(f"File '{file_path}' already exists, not touched")
        return
    with open(file_path, "a") as fd:
        fd.write(template)


def create_single_lib(lib):
    create_single_lib_h(lib)
    create_single_lib_cpp(lib)
    create_single_lib_cpp_test(lib)


def create_lib_programs(libs):
    for lib in libs:
        create_single_lib(lib)


def create_program_files(proj, libs):
    create_lib_programs(libs)
    create_cpp_main(proj, libs)


def print_result(proj, libs, show=False):
    lib_tests = "".join(f"./{LIBS_DIR}/{l}/{l}.tests\n" for l in libs)
    template = f"""SUCCESS!

Now create a build directory in {ROOT_DIR}, name it 'build'.
Enter 'build' directory.

cd build

Once in build directory, run,

cmake .. -DCMAKE_BUILD_TYPE=Debug -G "Unix Makefiles" && make all

This will try to create build environment and then build.
If this stage succeeds, you should be able to run default demo executable:

./{APP_DIR}/{proj}.*.tsk

You should be able to run all tests by running

ctest

If you want to run individual library tests, you can run:

{lib_tests}

Thank you
"""
    if show:
        print(template)


def start():
    proj = "task"
    libs = ["liba", "libb", "libc"]
    ext_libs = ["googletest"]
    public_libs = []
    create_cmakelist_structure(proj=proj, libs=libs, ext_libs=ext_libs)
    fill_in_cmakelists(proj, libs, public_libs, ext_libs)
    create_program_files(proj, libs)
    print_result(proj, libs)


def cmake_build(src, bld, bld_t, gen_t, dev_warn, mk_opt):
    cmake_cmd = f"cmake -S '{src}' -B '{bld}' -DCMAKE_BUILD_TYPE='{bld_t}' -G '{gen_t}'"
    if dev_warn:
        cmake_cmd = f"{cmake_cmd} -Wdev"

    if mk_opt.lower() != "no":
        cmake_cmd = f"{cmake_cmd} && make {mk_opt} -C {bld}"

    os.system(cmake_cmd)


def cmake_list_targets(bld):
    cmd = f"cmake --build {bld} --target help"
    os.system(cmd)


@click.group()
def cli():
    pass


@cli.command()
@click.option("-p", "--project", prompt=("Project name"))
@click.option(
    "-l",
    "--lib",
    "libs",
    multiple=True,
    help="Library that will be developed in this project",
)
@click.option("-d", "--dep", "deps", multiple=True, help=)
@click.option("-v", "--verbose", count=True)
def init(project, libs, deps, verbose):
    print(locals())


@cli.command()
@click.option(
    "-s",
    "--source-root",
    type=click.Path(file_okay=False, dir_okay=True),
    default=".",
    help="CMake source root directory where top CMakeLists.txt is found",
    show_default=False,
)
@click.option(
    "-b",
    "--build-root",
    type=click.Path(file_okay=False, dir_okay=True),
    default="cmake-build",
    help="CMake build root directory",
    show_default=True,
)
@click.option(
    "-t",
    "--build-type",
    type=click.Choice(["Debug", "Release", "RelWithDebInfo", "MinSizeRel"]),
    default="Release",
    help="CMake build type",
    show_default=True,
)
@click.option(
    "-g",
    "--generator-type",
    type=click.Choice(["MinGW Makefiles", "Unix Makefiles"]),
    default="Unix Makefiles",
    help="Makefile generator type",
    show_default=True,
)
@click.option(
    "-w",
    "--dev-warning",
    is_flag=True,
    help="Enable dev warnings",
    show_default=True,
)
@click.option(
    "-m",
    "--make-option",
    type=click.Choice(
        ["no", "all", "clean", "depend", "install", "list_install_components", "test"]
    ),
    default="all",
    help="Make option, value 'no' skips make",
    show_default=True,
)
def build(
    source_root, build_root, build_type, generator_type, dev_warning, make_option
):
    print(locals())
    cmake_build(
        source_root, build_root, build_type, generator_type, dev_warning, make_option
    )


@cli.command()
@click.option(
    "-b",
    "--build-root",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default="cmake-build",
    help="CMake build directory with build artifacts",
    show_default=True,
)
def targets(build_root):
    cmake_list_targets(build_root)


if __name__ == "__main__":
    cli()
