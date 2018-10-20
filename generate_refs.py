#! /usr/local/bin/python3
import re
import os
from os.path import join as pjoin
import argparse
import sys
from pprint import pprint
from collections import defaultdict

# This python script is meant to autogenerate markdown links
# and validate section references for the markdown rust-book


def format_anchor(line):
    return re.sub('[^\w-]+', '', '-'.join(line.split())).lower()


def normalize_header(header):
    return re.sub('(\n>)?\s+', ' ', header)


def create_entry(header, fname):
    return { normalize_header(header): {
        'filename': fname,
        'anchor-id': format_anchor(header)}
            }

def gather_reference(fname, page, ref_list, header_pattern, common_headers=['Summary'], **kwargs):
    inside_codeblock = False
    for line in page:
        # strip indention
        line = line.lstrip('> ')
        # avoid scraping codeblock comments
        if line.startswith('```'):
            # turn on/off gathering
            inside_codeblock = inside_codeblock ^ True

        if inside_codeblock is False and re.match(header_pattern, line):
            formatted_title = re.match(header_pattern, line).group(1)
            if formatted_title not in common_headers:
                yield create_entry(formatted_title, fname)
    return


def insert_reference(fname, ref_list, page, section_pattern, **kwargs):
    page_modified = False
    replaced = set()
    link_bank = set()
    dead_links = []
    dry_runs = []
    for quoted_match in re.finditer(section_pattern, page):
        quoted_string = quoted_match.group(0)
        match_key = normalize_header(quoted_string).strip('“”')
        # ignore section reference if starts with lowercase
        # ignore string if white list exists and string in it
        # if (not kwargs.get('whitelist') or
                # quoted_string not in kwargs.get('whitelist')):
        if any([match_key[0].islower(),
            quoted_string in replaced,
            (kwargs.get('whitelist') and match_key in kwargs['whitelist'])]):
            continue
        if match_key in ref_list and quoted_string in page:
            # create '#standalone_id' link if reference is on the same page
            section_id = ref_list[match_key]['anchor-id']
            if fname == ref_list[match_key]['filename']:
                section_link = f'#{section_id}'
                replace_as = f'[{quoted_string}]({section_link})'
            else:
                external_section_link = (
                    f'{ref_list[match_key]["filename"]}.html#{section_id}')
                replace_as = f'[{quoted_string}][{section_id}]'
                # append external links to bottom page as last step
                link_bank.add(f'[{section_id}]: {external_section_link}')
            # handle dry run optional arg
            if kwargs.get('dry_run'):
                dry_runs.append((quoted_string, replace_as))
            else:
                page = page.replace(quoted_string, replace_as)
                replaced.add(quoted_string)
                page_modified = True
        # handle optional flagging of dead links
        elif kwargs.get('flag_dead_links') or kwargs.get('save_flags'):
            dead_links.append(quoted_string)
    if not kwargs.get('quiet') and kwargs.get('dry_run'):
        if dry_runs:
            # for now handle any filenames longer than 60 char with abs values
            filler = abs(60 - len(fname))//2
            print(fname + '=#'*filler)
            for replacement in dry_runs:
                print(replacement[0])
                print(' |'*20)
                print(' v'*20)
                print(replacement[1])
                print('\n')
    if dead_links:
        normalized_dead = set(normalize_header(i) for i in dead_links)
        if kwargs.get('flag_dead_links'):
            print(fname + ' dead links:')
            for link in dead_links:
                print(f'[{link}] is possibly a dead link')
        if kwargs.get('save_flags'):
            return normalized_dead
    elif page_modified:
        return page + '\n'.join(sorted(link_bank)) + '\n'

# # # # # # # # # # # # # # #   
# regex patterns
# # # # # # # # # # # # # # #   

# identify headers starting with one to three hashes
re_header = re.compile('^#{1,4} (?:Appendix [A-Z]: )?(.+)\n?$')
assert re.search(re_header, '## Appendix C: Derivable Traits\n'
                 ).groups() == ('Derivable Traits',)
# identify passages surrounded by culry quotes
re_section = re.compile('(?<!\[)“[^”]+”(?!\])', re.MULTILINE)
section_test = ['“Too high”', '“Too\nslow”', '“Too low”']
assert re.findall(
    re_section, '“Too high” or “Too\nslow” or “Too low”') == section_test

# # # # # # # # # # # # # # #   
# Assertion Tests
# # # # # # # # # # # # # # #   

# format_achor unit test
assert format_anchor(
    'Preventing Reference Cycles: Turning an Rc<T> into a Weak<T>') == (
        'preventing-reference-cycles-turning-an-rct-into-a-weakt')
# it is necessary to strip nonalphas after the hypens to mirror present mdbook
# functionality when a header string ends with a spaced separated nonalpha
assert format_anchor(
    'Specify multiple traits with +') == (
        'specify-multiple-traits-with-')
# create_entry unit test
create_e_str = 'Using `Result<T, E>`\n in tests'
create_e_fname = 'ch11-01-writing-tests'
create_entry_out = {
    'Using `Result<T, E>` in tests': {
        'filename': 'ch11-01-writing-tests',
        'anchor-id': 'using-resultt-e-in-tests'
    }
}
assert create_entry(create_e_str, create_e_fname) == create_entry_out
# insert_reference unit test
test_insert = (
    'ch11-01-writing-test',
    {'Concatenation with the `+` Operator or the `format!` Macro': {
        'filename': 'ch08-02-strings',
        'anchor-id': 'concatenation-with-the--operator-or-the-format-macro'
    }
     }, ( """You can also add a custom message to be printed with the failure message as
optional arguments to the `assert!`, `assert_eq!`, and `assert_ne!` macros. Any
arguments specified after the one required argument to `assert!` or the two
required arguments to `assert_eq!` and `assert_ne!` are passed along to the
`format!` macro (discussed in Chapter 8 in the “Concatenation with the `+`
Operator or the `format!` Macro” section), so you can pass a format string that
contains `{}` placeholders and values to go in those placeholders. Custom
messages are useful to document what an assertion means; when a test fails,
you’ll have a better idea of what the problem is with the code.[“Concatenation
with the `+` Operator or the `format!` Macro”]
""")
)
insert_out = ("""You can also add a custom message to be printed with the failure message as
optional arguments to the `assert!`, `assert_eq!`, and `assert_ne!` macros. Any
arguments specified after the one required argument to `assert!` or the two
required arguments to `assert_eq!` and `assert_ne!` are passed along to the
`format!` macro (discussed in Chapter 8 in the [“Concatenation with the `+`
Operator or the `format!` Macro”][concatenation-with-the--operator-or-the-format-macro] section), so you can pass a format string that
contains `{}` placeholders and values to go in those placeholders. Custom
messages are useful to document what an assertion means; when a test fails,
you’ll have a better idea of what the problem is with the code.[“Concatenation
with the `+` Operator or the `format!` Macro”]
[concatenation-with-the--operator-or-the-format-macro]: ch08-02-strings.html#concatenation-with-the--operator-or-the-format-macro
""")

def line_differ(func_in, expected_out):
    for func, out in zip(func_in.splitlines(), expected_out.splitlines()):
        if func != out:
            print('function out:')
            print(func)
            print('expected output:')
            print(out)

# print(line_differ(insert_reference(*(test_insert), re_section), insert_out))
assert insert_reference(*(test_insert), re_section) == insert_out


def main(src_input, **kwargs):
    # generate array of tuples with each markdown absolute filepath
    # and filename stripped of extension
    src = []

    def generate_filepaths(in_paths):
        return ((file.name.rstrip('.md'), pjoin(in_paths, file))
                for file in os.scandir(in_paths) if
                file.name.endswith('.md') and file.is_file())

    def parse_whitelist(in_doc):
        if os.path.exists(in_doc) is False:
            raise FileNotFoundError('Specified filepath does not exist')
        with open(in_doc, 'r') as file:
            whitelist_collection = []
            for line in file.readlines():
                line = line.strip()
                if line.startswith('“') and line.endswith('”'):
                    whitelist_collection.append(line.strip('“”'))
            return whitelist_collection

    if kwargs.get('whitelist'):
        kwargs['whitelist'] = parse_whitelist(kwargs['whitelist'])

    def save_flags(array, out_file):
        assert type(array) != str
        if os.path.exists(out_file):
            raise FileExistsError('there is already a file present')
        with open(out_file, 'w') as file:
            # write flaglist entry as commented
            file.writelines(f'# {i}\n' for i in sorted(array))

    for path in src_input:
        if os.path.isdir(path):
            src.extend(list(generate_filepaths(path)))
        elif os.path.isfile(path):
            split_p = os.path.splitext(path)
            if split_p[1] != '.md' and kwargs.get('ignore_md'):
                raise Exception(path + 'is not indicated as a markdown file')
            src.append((os.path.basename(split_p[0]), path))
        else:
            raise FileNotFoundError(path)

    # File parsing starts here
    heading_list = defaultdict(dict)
    flaglist_set = set()
    for fname, doc in src:
        with open(doc, 'r') as file:
            pagelines = file.readlines()
        for ref in gather_reference(fname, pagelines, heading_list, re_header):
            heading_list.update(ref)

    if kwargs.get('references'):
        pprint(heading_list)

    for fname, doc in src:
        with open(doc, 'r') as file:
            str_page = file.read()
        result = insert_reference(fname, heading_list, str_page, re_section, **kwargs)
        if kwargs.get('save_flags') and result:
            flaglist_set.update(result)
        # if this is not a dry run or a flaglist is generated and there are results
        elif kwargs.get('dry_run') is False and result:
            with open(doc, 'w') as file:
                file.write(result)
        del result
    # if a nonzero flaglist collection exists
    if flaglist_set:
        save_flags(flaglist_set, kwargs['save_flags'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser( description=(
        'Create and validate rust-book mentions of other sections'))
    parser.add_argument('md_directory', nargs='+', type=str,
        help='desired input filepath, can be any number of filepaths and valid files')
    parser.add_argument('-f', '--flag-dead-links', action='store_true',
        help='flag links that potentially reference sections not present in the book')
    parser.add_argument('-d', '--dry-run', action='store_true',
        help='print out references that will be replaced in the md document')
    parser.add_argument('-q', '--quiet', action='store_true',
        help='do not print optional args to console')
    parser.add_argument('-i', '--ignore-md', action='store_true',
        help='ignore file endings when passing individual files')
    parser.add_argument( '-r', '--references', action='store_true',
        help='display mapped dictionary of genereated references')
    parser.add_argument('--save-flags', type=str, action='store',
        help='write a line separated list of all dead links to specified filepath')
    parser.add_argument('--whitelist', type=str, action='store',
        help='filepath to list of ignored curly quote passages')

    def rel_path(in_str):
        if in_str:
            return os.path.realpath(in_str)

    args = parser.parse_args()
    args.save_flags = rel_path(args.save_flags)
    args.whitelist = rel_path(args.whitelist)

    main(args.md_directory,
         flag_dead_links=args.flag_dead_links,
         dry_run=args.dry_run,
         quiet=args.quiet,
         ignore_md=args.ignore_md,
         references=args.references,
         save_flags=args.save_flags,
         whitelist=args.whitelist)
