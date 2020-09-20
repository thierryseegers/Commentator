#!python3

import argparse
import clang.cindex
import pathlib
import re

ARGPARSER = argparse.ArgumentParser()
ARGPARSER.add_argument('paths', nargs='+', type=str, help='Path(s) of file(s), folder(s) or glob expression.')
ARGPARSER.add_argument('-c', '--compress', dest='compress', action='store_true', default=False,
                       help='Leaves white space but no newlines between comments.')
ARGPARSER.add_argument('-d', '--dry-run', dest='dry_run', action='store_true', default=False,
                       help='Doesn\'t write \"comments\" files. (Useful for --stats')
ARGPARSER.add_argument('-r', '--recursive', dest='recursive', action='store_true', default=False,
                       help='Recursively navigates folders.')
ARGPARSER.add_argument('-s', '--stats', dest='stats', action='store_true', default=False,
                       help='Prints percentage of lines of comments per file.')
ARGS = ARGPARSER.parse_args()

# Returns true for files with the expected extension that are not purely comment files already.
def is_c_cpp(path):
    return path.suffix in ['.h', '.hh', '.hpp', '.hxx', '.c', '.cc', '.cpp', '.cxx'] and not path.stem.endswith('comments')

# Used to collect statistics on all files analyzed.
total_lines = 0
total_comment_lines = 0

# Uses libclang to parse a file and generate a .comments file where code is converted to whitespace and all whitespace 
# and comments are kept intact.
def comment(path):
    # We really only need lexing done on the source file rather than lexing and parsing but I don't know if that's possible. 
    # At least, I used option(s) to help reduce workload.
    tu = clang.cindex.TranslationUnit.from_source(path, options=clang.cindex.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES)

    text = open(path).readlines() # Because parsing throws away whitespace information, we'll need to retrieve it from the original file.
    comments = str()    # Holds the contents of the .comments file to be later written.

    comment_lines = 0
    previous_comment_token = None

    # For all lexed tokens, we analyze the comments.
    for token in tu.cursor.get_tokens():
        if token.kind is clang.cindex.TokenKind.COMMENT:
            # In order to perfectly take pathological cases in to account, we compute the number of newlines to prefix 
            # this comment with and, if any, the text preceding it based on the placement of the previous comment token 
            # (none, earlier line or same line). Existing whitespace is kept as is, all other text is converted to space.
            # If ARGS.compress is True, we minimize the ammount newlines and comments are left justified.
            # We also keep tabs on the comment's number of lines for statistics purposes.
            newlines = 0
            preceding_text = str()
            if previous_comment_token is None:
                if ARGS.compress:
                    newlines = 0
                else:
                    newlines = token.extent.start.line - 1
                    preceding_text = text[token.extent.start.line - 1][:token.extent.start.column - 1]
                comment_lines += token.extent.end.line - token.extent.start.line + 1
            elif previous_comment_token.extent.end.line != token.extent.start.line:
                if ARGS.compress:
                    newlines = 1
                else:
                    newlines = token.extent.start.line - previous_comment_token.extent.end.line
                    preceding_text = text[token.extent.start.line - 1][:token.extent.start.column - 1]
                comment_lines += token.extent.end.line - token.extent.start.line + 1
            else:
                preceding_text = text[token.extent.start.line - 1][previous_comment_token.extent.end.column - 1:token.extent.start.column - 1]
                comment_lines += token.extent.end.line - token.extent.start.line

            comments += '\n' * newlines + re.sub(r'\S', ' ', preceding_text) + (re.sub(r'\n\s+', '\n', token.spelling) if ARGS.compress else token.spelling)
            previous_comment_token = token

    # Actually produce a file if required.
    # TODO: be even more efficient and do not have a 'comments' variable.
    if not ARGS.dry_run:
        destination = open(path.parent.joinpath(path.stem + '.comments' + path.suffix), 'w')
        destination.write(comments)

    # Print statistics for this file and update global statistics.
    if ARGS.stats and len(text) > 0:
        print("{} {:.2%}".format(path, comment_lines / len(text)))

        global total_comment_lines
        global total_lines
        total_comment_lines += comment_lines
        total_lines += len(text)

if __name__ == "__main__":
    for path in [pathlib.Path(p) for p in ARGS.paths]:
        if path.is_dir():
            for path in filter(is_c_cpp, path.rglob('*') if ARGS.recursive else path.glob('*')):
                comment(path)
        elif path.is_file() and is_c_cpp(path):
            comment(path)

    # Print global statistics for all files analyzed.
    if ARGS.stats:
        print("{:.2%}".format(total_comment_lines / total_lines))
