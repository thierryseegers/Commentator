# Commentator

Beginner programming students have asked me "We're required to comment our code. What makes good comments?"
Answering this question is always difficult.
What constitutes good comments is often quite subjective and there is no definite answer.
We just hammer the idea in the students' minds that they need to write comments.
Then we judge them on what they have written with rules like "Explain the why, not the how." and "Be succint but not too much."

I still don't have a perfect answer but here's a different approach: "Do your comments tell a story?"
If we were to strip your source file of all its code and retain only the comments, could we read what's left and still understand what is going on?
Of course, we wouldn't exactly expect a coherent story but I think it's a avenue worth exploring.

OK, so how *do* you strip a source file of its code? You could use your imagination... or you could use software. Enter `commentator`.

`commentator` is a command line tools used to strip files of C or C++ source code from the code they contain, leaving whitespace in its place and preserving only the comments.
For a given file `source.c` it produces a file `source.comments.c` with only the whitespace and comments retained.
The code it contained is converted to whitespace.
Though it may look weird to look at "Swiss cheese" produced by the code's absence, I think it is interesting nonetheless from the perspective of "comments as a story".

For the time being, I expect I'll be the only one using this tool for my grading benefits.
For it to be as painless as possible to use for students, I can imagine it being turned into a web API and corresponding friendly site.

## Usage

`commentator` uses [libclang](https://clang.llvm.org/docs/Tooling.html) and its [Python bindings](https://github.com/llvm-mirror/clang/blob/master/bindings/python/clang/cindex.py) to parse files of C and C++ source code.
Install the `clang` front-end compiler package for your platform (e.g. on macOS, this was done through `>brew install llvm` which automatically installs `clang`).
Afterwards, follow the short set up instructions found on [this](https://eli.thegreenplace.net/2011/07/03/parsing-c-in-python-with-clang#setting-up) helpful page.

### Arguments

- `paths`: Path(s) to file(s), folder(s) or a [glob expression](https://en.wikipedia.org/wiki/Glob_(programming)). All files with extensions typical of C or C++ headers and source will be analyzed.
- `-c`, `--compress`: Leaves no newlines between comments preserving their indentation.
- `-d`, `--dry-run`: Analyze input source file(s) but produce no output file(s). Useful when combined with `--stats`.
- `-l`, `--left-justify`: Justifies all coments to the left.
- `-p`, `--parallel`: Runs on many processes as there are cores to accalerate the analysis of large sets of files.
- `-r`, `--recursive`: If path(s) given is a/are folder(s), recursively analyze all the files in the folder(s).
- `-s`, `--stats`: Prints the percentage of lines that contain comments, per file and for all files.

## Example

Given an input file `source.c` that looks like this:

```
/*
 * File: source.c
 * Author: Thierry Seegers
 * License: Public Domain
 */

#include <stdio.h> // For printf

// Prints on screen double the value of the given argument.
void print_double(int const i)
{
    printf("%d\n", i * 2);
}

int main()
{
    /* Calls the print_double function with 22, 33 and 44 as arguments. */
    print_double(22);
    print_double(33);
    print_double(44);

    return 0;
}
```

`commentator` will produce a file `source.comments.c` that looks like this:

```
/*
 * File: source.c
 * Author: Thierry Seegers
 * License: Public Domain
 */

                   // For printf

// Prints on screen double the value of the given argument.







    /* Calls the print_double function with 22, 33 and 44 as arguments. */
```

If the amount of whitespace throws you off, you can use the `--compress` and/or the `--left-justify` arguments but then you lose the flow produced by the spacing and/or indentation.
In the committed files, you'll see examples of more pathological cases of comments that are correctly processed with respect to whitespace.

The file's extensions are preserved so that the output files can be opened in an IDE and the comments' colorization remain as one is used to.