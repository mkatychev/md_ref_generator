#! /usr/local/bin/python3
import re
import os
from os.path import join as pjoin
import argparse
import sys
from pprint import pprint
from collections import defaultdict
from itertools import chain

# This python script is meant to autogenerate markdown links
# and validate section references for the markdown rust-book


def format_anchor(line):
    return re.sub(r'[^\w-]+', '', '-'.join(line.split())).lower()


def normalize_header(header):
    return re.sub(r'(\n>)?\s+', ' ', header)


def create_entry(header, fname):
    return {
        normalize_header(header): {
            'filename': fname,
            'anchor-id': format_anchor(header)
        }
    }


def gather_reference(fname,
                     page,
                     ref_list,
                     header_pattern,
                     common_headers=['Summary'],
                     **kwargs):
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
    # if piping to unit test or other module
    page_modified = False
    dead_refs = []
    dry_runs = []
    replaced = set()
    link_bank = set()
    for quoted_match in re.finditer(section_pattern, page):
        quoted_string = quoted_match.group(0)
        match_key = normalize_header(quoted_string).strip('“”')
        # ignore section reference if starts with lowercase
        # ignore string if in white list
        if match_key[0].islower() or (kwargs.get('whitelist')
                                      and match_key in kwargs['whitelist']):
            continue
        if match_key in ref_list and quoted_string in page:
            # create '#standalone_id' link if reference is on the same page
            section_id = ref_list[match_key]['anchor-id']
            if fname == ref_list[match_key]['filename']:
                section_link = f'#{section_id}'
                replace_as = f'[{quoted_string}]({section_link})\n'
            else:
                external_section_link = (
                    f'{ref_list[match_key]["filename"]}.html#{section_id}')
                replace_as = f'[{quoted_string}]\n[{section_id}]\n'
                # append external links to bottom page as last step
                link_bank.add(f'[{section_id}]:\n{external_section_link}')
            # handle dry run optional arg
            if kwargs.get('dry_run'):
                dry_runs.append((quoted_string, replace_as))
            else:
                page = re.sub(f'(?<!\[){re.escape(quoted_string)}\s?',
                              replace_as, page, 1, re.MULTILINE)
                # print(f'"{quoted_string}"', file=sys.stdout)
                # print(f'"{replace_as}"', file=sys.stdout)
                replaced.add(quoted_string)
                page_modified = True
        # handle optional flagging of dead links
        elif kwargs.get('flag_dead_refs') or kwargs.get('save_flags'):
            dead_refs.append(quoted_string)
    if not kwargs.get('quiet') and kwargs.get('dry_run'):
        if dry_runs:
            # for now handle any filenames longer than 60 char with abs values
            filler = abs(60 - len(fname)) // 2
            print(fname + '=#' * filler)
            for replacement in dry_runs:
                print(replacement[0])
                print(' |' * 20)
                print(' v' * 20)
                print(replacement[1])
                print('\n')
    if dead_refs:
        normalized_dead = set(normalize_header(i) for i in dead_refs)
        if kwargs.get('flag_dead_refs'):
            print(fname + ' dead links:')
            for link in dead_refs:
                print(f'[{link}] is possibly a dead reference')
        if kwargs.get('save_flags'):
            return normalized_dead
    elif page_modified:
        return page + '\n' + '\n'.join(sorted(link_bank)) + '\n'


# # # # # # # # # # # # # # #
# regex patterns
# # # # # # # # # # # # # # #

# identify headers starting with one to three hashes
re_header = re.compile(r'^#{1,4} (?:Appendix [A-Z]: )?(.+)\n?$')
assert re.search(
    re_header,
    '## Appendix C: Derivable Traits\n').groups() == ('Derivable Traits', )
# identify passages surrounded by culry quotes
re_section = re.compile(r'(?<!\[)“[^”]+”(?!\])', re.MULTILINE)
section_test = ['“Too high”', '“Too\nslow”', '“Too low”']
assert re.findall(re_section,
                  '“Too high” or “Too\nslow” or “Too low”') == section_test


def main(src_input, **kwargs):
    # generate array of tuples with each markdown absolute filepath
    # and filename stripped of extension
    src = []

    def generate_filepaths(in_paths):
        return ((file.name.rstrip('.md'), pjoin(in_paths, file))
                for file in os.scandir(in_paths)
                if file.name.endswith('.md') and file.is_file())

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
        result = insert_reference(fname, heading_list, str_page, re_section,
                                  **kwargs)
        if result:
            if kwargs.get('save_flags'):
                flaglist_set.update(result)
            # if this is not a dry run or a flaglist is generated and there are results
            elif kwargs.get('dry_run') is False:
                with open(doc, 'w') as file:
                    file.write(result)
        del result
    # if a nonzero flaglist collection exists
    if flaglist_set:
        save_flags(flaglist_set, kwargs['save_flags'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=(
            'Create and validate rust-book mentions of other sections'))
    parser.add_argument(
        'md_directory',
        nargs='+',
        type=str,
        help=
        'desired input path(s), can be any combination of valid directories and files'
    )
    parser.add_argument(
        '-f',
        '--flag-dead-refs',
        action='store_true',
        help=
        'flag references that are not an exact match for any sections present in md_directory'
    )
    parser.add_argument(
        '-d',
        '--dry-run',
        action='store_true',
        help=
        'print out references that would have been replaced in provided md files'
    )
    parser.add_argument(
        '-q',
        '--quiet',
        action='store_true',
        help='do not print optional args to console')
    parser.add_argument(
        '-i',
        '--ignore-md',
        action='store_true',
        help='ignore file endings when passing individual files')
    parser.add_argument(
        '-r',
        '--references',
        action='store_true',
        help='display mapped dictionary of genereated references')
    parser.add_argument(
        '--save-flags',
        type=str,
        action='store',
        help=
        'save output that would have been generated by --flag-dead-refs to provided filepath'
    )
    parser.add_argument(
        '--whitelist',
        type=str,
        action='store',
        help=
        'path to file containig newline separated list of strings to ignore')

    def rel_path(in_str):
        if in_str:
            return os.path.realpath(in_str)

    args = parser.parse_args()
    args.save_flags = rel_path(args.save_flags)
    args.whitelist = rel_path(args.whitelist)

    main(
        args.md_directory,
        flag_dead_refs=args.flag_dead_refs,
        dry_run=args.dry_run,
        quiet=args.quiet,
        ignore_md=args.ignore_md,
        references=args.references,
        save_flags=args.save_flags,
        whitelist=args.whitelist)
