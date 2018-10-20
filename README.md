# md-ref-generator

This is a python3 command line utility to automate validating and generating section references for markdown documents currently intended to be used for [The Rust Programming Language Book](https://github.com/rust-lang/book).

* A section in markdown is considered any line that starts with 1 or more `#` followed by a space.

* Sections should be surrounded by mirrored curly double citation marks like so: `“Section Reference”` to be considered a candidate for evaluation. 

* The process is currently hardcoded to look for anything inside double citation marks and exclude any cited text that is already surrounded by square brackets, ex: `...[“Section Reference”]...` will be ignored.

* Anchor link generation tries to mirror [md-book](https://github.com/rust-lang-nursery/mdBook), see assertion tests for more details.

```
usage: generate_refs.py [-h] [-f] [-d] [-q] [-i] [-r]
                        [--generate-flaglist GENERATE_FLAGLIST]
                        md_directory [md_directory ...]

Create and validate rust-book mentions of other sections

positional arguments:
  md_directory          desired input filepath, can be any number of filepaths
                        and valid files

optional arguments:
  -h, --help            show this help message and exit
  -f, --flag-dead-links
                        flag links that potentially reference sections not
                        present in the book
  -d, --dry-run         print out references that will be replaced in the md
                        document
  -q, --quiet           do not print optional args to console
  -i, --ignore-md       ignore file endings when passing individual files
  -r, --references      display mapped dictionary of genereated references
  --generate-flaglist GENERATE_FLAGLIST
                        write a line separated list of all dead links to
                        specified filepath
```

## Examples
renerate references to and from 

```
python3 generate_refs.py src/ch18-01-all-the-places-for-patterns.md src/ch18-03-pattern-syntax.md --dry-run
```

produces an output where only references in both files are considered:

```
	ch18-01-all-the-places-for-patterns=#=#=#=#=#=#=#=#=#=#=#=#
	“Ignoring Values in a Pattern”
	 | | | | | | | | | | | | | | | | | | | |
	 v v v v v v v v v v v v v v v v v v v v
	[“Ignoring Values in a Pattern”][ignoring-values-in-a-pattern]
	
	
	“Ignoring Values in a Pattern”
	 | | | | | | | | | | | | | | | | | | | |
	 v v v v v v v v v v v v v v v v v v v v
	[“Ignoring Values in a Pattern”][ignoring-values-in-a-pattern]
	
	
	ch18-03-pattern-syntax=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
	“Extra
	Conditionals with Match Guards”
	 | | | | | | | | | | | | | | | | | | | |
	 v v v v v v v v v v v v v v v v v v v v
	[“Extra
	Conditionals with Match Guards”](#extra-conditionals-with-match-guards)
	
```
Provide a whitelist text file for passages to ignore and display all remaining potential dead links:

```
python3 generate_refs.py ./src -f --whitelist ./wlist.txt
```
