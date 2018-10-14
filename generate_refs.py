import re
import os
from collections import defaultdict

# pattern wher match is “term” that is not surrounded by [ ]
src_path = '/Users/mickerus/Documents/book/2018-edition/src'
src =  ((file.rstrip('.md'), os.path.join(src_path, file))
        for file in os.listdir(src_path) if file.endswith('.md'))
heading_list = defaultdict(dict)


def format_anchor(line):
   return re.sub('[^\w-]+', '', '-'.join(line.split())).lower()


# format test
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

# create_entry test
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
        # determine if this is a chapter start heading, this is to avoid scraping comment files
        if line.startswith('```'):
            # turn on/off gathering
            inside_codeblock = inside_codeblock ^ True
        if inside_codeblock is True and re.match(re_header, line):
            return create_entry(line.lstrip('# ', fname))


re_section = re.compile(r'(?<!\[)?“.+\n?.+\n?”(?!\])', re.MULTILINE)
def insert_reference(fname, ref_list, page, section_pattern, **kwargs):
    link_bank = set()
    for index, quoted_match in enumerate(re.finditer(section_pattern, page)):
        # strip any whitespace to be replaced with a newline
        quoted_string = quoted_match.group(index)
        match_key = quoted_match.group(index).strip('“”').replace('\n', ' ')
        # ignore section reference if starts with lowercase
        if match_key[0].islower():
            continue
        if match_key in ref_list:
            # create '#standalone_id' link if reference is on the same page
            section_id = ref_list[match_key]['anchor-id']
            if fname == ref_list[match_key]['filename']:
                section_link = f'#{section_id}'
                replace_as = f'[{quoted_string}]({section_link})'
            else:
                section_link = f'{ref_list[match_key]["filename"]}.html#{section_id}'
                replace_as = f'[{quoted_string}][{section_id}]'
                link_bank.add(f'[{section_id}][{section_link}]')
            if kwargs.get('dry-run'):
                print(quoted_string, ' -> ', replace_as)
            else:
                page = page.replace(quoted_string, replace_as, 1)
        elif kwargs.get('flag_dead_links'):
            print(f'{quoted_match}: possible reference to non-existent section')
        return page + '\n' + '\n'.join(link_bank)

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
[concatenation-with-the--operator-or-the-format-macro][ch08-02-strings.html#concatenation-with-the--operator-or-the-format-macro]""")
insert_in = insert_reference(*(test_insert), re_section)
# for _in, _out in zip(insert_in.splitlines(), insert_out.splitlines()):
    # if _in != _out:
        # print(_in)
        # print(_out)
assert insert_reference(*(test_insert), re_section) == insert_out
# for fname, doc in list(src)[:2]:
    # print(doc)
    # with open(doc, 'r') as file:
        # page = file.readlines()
    # gather_reference(fname, page, chapter_dict)

# for fname, doc in list(src)[:2]:
    # with open(doc, 'r') as file:
        # page = file.read()
    # match_reference(fname, page, chapter_dict, pattern)
