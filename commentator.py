#!python3

import argparse
import clang.cindex
import concurrent.futures
import functools
import os
import pathlib
import re
import threading

ARGPARSER = argparse.ArgumentParser()
ARGPARSER.add_argument('paths', nargs='+', type=str, help='Path(s) of file(s), folder(s) or glob expression.')
ARGPARSER.add_argument('-c', '--compress', dest='compress', action='store_true', default=False,
                       help='Leaves no newlines between comments preserving their indentation.')
ARGPARSER.add_argument('-d', '--dry-run', dest='dry_run', action='store_true', default=False,
                       help='Doesn\'t write \"comments\" files. (Useful for --stats')
ARGPARSER.add_argument('-l', '--left-justify', dest='left_justify', action='store_true', default=False,
                       help='Justifies all coments to the left.')
ARGPARSER.add_argument('-p', '--parallel', dest='parallel', action='store_true', default=False,
                       help='Analyzes multiple files in parallel.')
ARGPARSER.add_argument('-r', '--recursive', dest='recursive', action='store_true', default=False,
                       help='Recursively navigates folders.')
ARGPARSER.add_argument('-s', '--stats', dest='stats', action='store_true', default=False,
                       help='Prints percentage of lines of comments per file.')
ARGS = ARGPARSER.parse_args()

# Uses libclang to parse a file and generate a .comments file where code is converted to whitespace and all whitespace 
# and comments are kept intact.
def comment(path):
    source = open(path, errors='replace', mode='r').readlines() # Because parsing throws away whitespace information, we'll need to retrieve it from the original file.

    # We really only need lexing done on the source file rather than lexing and parsing but I don't know if that's possible. 
    # At least, I used option(s) to help reduce workload.
    tu = clang.cindex.TranslationUnit.from_source(path, unsaved_files=[(path, ''.join(source))], options=clang.cindex.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES)

    comments = str()    # Holds the contents of the .comments file to be later written.

    comment_lines = 0
    previous_comment_token = None

    # For all lexed tokens, we analyze the comments.
    for token in tu.cursor.get_tokens():
        if token.kind is clang.cindex.TokenKind.COMMENT:
            # Some comments may contain incorrect codepoints. Re-decode and replace offending codepoints.
            try:
                spelling = token.spelling
            except UnicodeDecodeError as ude:
                spelling = ude.object.decode(errors='replace')

            # In order to perfectly take pathological cases in to account, we compute the number of newlines to prefix 
            # this comment with and, if any, the text preceding it based on the placement of the previous comment token 
            # (none, earlier line or same line). Existing whitespace is kept as is, all other text is converted to space.
            # If ARGS.compress is True, we minimize the ammount newlines.
            # If ARGS.left_justify is True, comments are left justified.
            # We also keep tabs on the comment's number of lines for statistics purposes.
            newlines = 1
            preceding_text = ''
            if previous_comment_token is None:
                if ARGS.compress:
                    newlines = 0
                else:
                     newlines = token.extent.start.line - 1
                if not ARGS.left_justify:
                    preceding_text = source[token.extent.start.line - 1][:token.extent.start.column - 1]
                comment_lines += token.extent.end.line - token.extent.start.line + 1
            elif previous_comment_token.extent.end.line != token.extent.start.line:
                if not ARGS.compress:
                    newlines = token.extent.start.line - previous_comment_token.extent.end.line
                if not ARGS.left_justify:
                    preceding_text = source[token.extent.start.line - 1][:token.extent.start.column - 1]
                comment_lines += token.extent.end.line - token.extent.start.line + 1
            else:
                newlines = 0
                preceding_text = source[token.extent.start.line - 1][previous_comment_token.extent.end.column - 1:token.extent.start.column - 1]
                comment_lines += token.extent.end.line - token.extent.start.line

            # Best effort left-justification for multiline comments. Imperfect when tabs are used.
            if ARGS.left_justify:
                spelling = re.sub(r'\n\s{' + str(token.extent.start.column - 1) + '}', '\n', spelling)

            comments += '\n' * newlines + re.sub(r'\S', ' ', preceding_text) + spelling
            previous_comment_token = token

    # Actually produce a file if required.
    # TODO: be even more efficient and do not have a 'comments' variable.
    if not ARGS.dry_run:
        destination = open(path.parent.joinpath(path.stem + '.comments' + path.suffix), 'w')
        destination.write(comments)
        destination.close()

    # Return this data for stats collection.
    return len(source), comment_lines

def update_total_stats(path, total_lines, total_comments, f):
    lines, comments = f.result()

    total_lines[0] += lines
    total_comments[0] += comments

def print_stats(path, f):
    lines, comments = f.result()
    print("{} {:.2%}".format(path, comments / lines if lines > 0 else 0))

if __name__ == "__main__":
    total_lines = [0]   # As lists so they get mutated in the update_total_stats callback.
    total_comments = [0]

    # Returns true for files with the expected extension that are not purely comment files already.
    def is_c_cpp(path):
        return path.suffix in ['.h', '.hh', '.hpp', '.hxx', '.c', '.cc', '.cpp', '.cxx'] and not path.stem.endswith('comments')

    def analyze(executor, path, total_lines, total_comments):
        f = executor.submit(comment, path)
        if ARGS.stats:
            f.add_done_callback(functools.partial(print_stats, path))
            f.add_done_callback(functools.partial(update_total_stats, path, total_lines, total_comments))

    with concurrent.futures.ProcessPoolExecutor(max_workers=os.cpu_count() if ARGS.parallel else 1) as executor:
        for path in [pathlib.Path(p) for p in ARGS.paths]:
            if path.is_dir():
                for path in filter(is_c_cpp, path.rglob('*') if ARGS.recursive else path.glob('*')):
                    analyze(executor, path, total_lines, total_comments)
            elif path.is_file() and is_c_cpp(path):
                analyze(executor, path, total_lines, total_comments)

    executor.shutdown(wait=True)

    # Print global statistics for all files analyzed.
    if ARGS.stats and total_lines[0] > 0:
        print("{:.2%}".format(total_comments[0] / total_lines[0]))