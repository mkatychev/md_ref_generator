#! /usr/local/bin/python3
import re
import os
import argparse
from pprint import pprint
from collections import defaultdict


# This python script is meant to autogenerate markdown links
# and validate section references for the markdown rust-book
def format_anchor(line):
   return re.sub('[^\w-]+', '', '-'.join(line.split())).lower()


# format_achor unit test
assert format_anchor(
    'Preventing Reference Cycles: Turning an Rc<T> into a Weak<T>') == (
    'preventing-reference-cycles-turning-an-rct-into-a-weakt')
# it is necessary to strip nonalphas after the hypens to mirror present mdbook
# functionality when a header string ends with a spaced separated nonalpha
assert format_anchor(
    'Specify multiple traits with +') == (
    'specify-multiple-traits-with-')


def create_entry(line, fname):
    return { line: {
        'filename': fname,
        'anchor-id': format_anchor(line)}
        }


# create_entry unit test
create_e_str = 'Using `Result<T, E>` in tests'
create_e_fname = 'ch11-01-writing-tests'
create_entry_out = {
    'Using `Result<T, E>` in tests': {
        'filename': 'ch11-01-writing-tests',
        'anchor-id': 'using-resultt-e-in-tests'
        }
    }
assert create_entry(create_e_str, create_e_fname) == create_entry_out


re_header = re.compile('^#{1,3} .+\n?$')
def gather_reference(fname, page, ref_list, header_pattern):
    inside_codeblock = False
    for line in page:
        # determine if this is a chapter start heading
        # this is to avoid scraping codeblock comments
        if line.startswith('```'):
            # turn on/off gathering
            inside_codeblock = inside_codeblock ^ True
        if inside_codeblock is False and re.match(re_header, line):
            yield create_entry(line.lstrip('# ').rstrip('\n'), fname)
    return


re_section = re.compile(r'(?<!\[)?“.+\n?.+\n?”(?!\])', re.MULTILINE)
def insert_reference(fname, ref_list, page, section_pattern, **kwargs):
    modified = False
    link_bank = set()
    dead_links = []
    dry_runs = []
    for quoted_match in re.finditer(section_pattern, page):
        # strip any whitespace to be replaced with a newline
        quoted_string = quoted_match.group()
        match_key = quoted_match.group().strip('“”').replace('\n', ' ')
        # ignore section reference if starts with lowercase
        if match_key[0].islower():
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
                link_bank.add(f'[{section_id}]: {external_section_link}')
            # handle dry run optional arg
            if kwargs.get('dry_run'):
                dry_runs.append((quoted_string, replace_as))
            else:
                page = page.replace(quoted_string, replace_as, 1)
                modified = True
        # handle optional flagging of dead links
        elif kwargs.get('flag_dead_links'):
            dead_links.append(quoted_string)
    if dry_runs and kwargs.get('quiet') is False:
        filler = (60 - len(fname))//2
        print(fname + '=#'*filler)
        for replacement in dry_runs:
            print(replacement[0])
            print(' |'*20)
            print(' v'*20)
            print(replacement[1])
            print('\n')
    if dead_links and kwargs.get('quiet') is False:
        print(fname + ' dead links:')
        for link in dead_links:
            print(f'[{link}] is possibly a dead link')
    if modified:
        return page + '\n' + '\n'.join(link_bank)

# insert_reference unit test
test_insert = (
    'ch11-01-writing-test',
    {'Concatenation with the `+` Operator or the `format!` Macro': {
        'filename': 'ch08-02-strings',
        'anchor-id': 'concatenation-with-the--operator-or-the-format-macro'
        }
    }, (
"""You can also add a custom message to be printed with the failure message as
optional arguments to the `assert!`, `assert_eq!`, and `assert_ne!` macros. Any
arguments specified after the one required argument to `assert!` or the two
required arguments to `assert_eq!` and `assert_ne!` are passed along to the
`format!` macro (discussed in Chapter 8 in the “Concatenation with the `+`
Operator or the `format!` Macro” section), so you can pass a format string that
contains `{}` placeholders and values to go in those placeholders. Custom
messages are useful to document what an assertion means; when a test fails,
you’ll have a better idea of what the problem is with the code.[“Concatenation
with the `+` Operator or the `format!` Macro”]""")
)
insert_out = (
"""You can also add a custom message to be printed with the failure message as
optional arguments to the `assert!`, `assert_eq!`, and `assert_ne!` macros. Any
arguments specified after the one required argument to `assert!` or the two
required arguments to `assert_eq!` and `assert_ne!` are passed along to the
`format!` macro (discussed in Chapter 8 in the [“Concatenation with the `+`
Operator or the `format!` Macro”][concatenation-with-the--operator-or-the-format-macro] section), so you can pass a format string that
contains `{}` placeholders and values to go in those placeholders. Custom
messages are useful to document what an assertion means; when a test fails,
you’ll have a better idea of what the problem is with the code.[“Concatenation
with the `+` Operator or the `format!` Macro”]
[concatenation-with-the--operator-or-the-format-macro]: ch08-02-strings.html#concatenation-with-the--operator-or-the-format-macro""")
assert insert_reference(*(test_insert), re_section) == insert_out


def main(src_path, **kwargs):
    # generate array of tuples with each markdown absolute filepath
    # and filename stripped of extension
    src =  [(file.rstrip('.md'), os.path.join(src_path, file))
            for file in os.listdir(src_path) if file.endswith('.md')]
    heading_list = defaultdict(dict)
    for fname, doc in src:
        with open(doc, 'r') as file:
            pagelines = file.readlines()
        for ref in gather_reference(fname, pagelines, heading_list, re_header):
            heading_list.update(ref)

    if kwargs.get('print_references'):
        pprint(heading_list)
    for fname, doc in src:
        with open(doc, 'r') as file:
            str_page = file.read()
        result = insert_reference(fname, heading_list, str_page, re_section, **kwargs)
        if kwargs.get('dry_run') is False and result:
            with open(doc, 'w') as file:
                file.write(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=(
            'Create and validate rust-book mentions of other sections'))
    parser.add_argument('md_directory', type=str,
            help='desired input filepath')
    parser.add_argument(
        '--flag-dead-links', action='store_true',
        help='flag links that potentially reference sections not present in the book')
    parser.add_argument(
        '--dry-run', action='store_true',
         help='print out references that will be replaced in the md document')
    parser.add_argument(
        '--quiet', action='store_true',
         help='do not print optional args to console')
    args = parser.parse_args()
    main(args.md_directory, flag_dead_links=args.flag_dead_links, dry_run=args.dry_run, quiet=args.quiet)
