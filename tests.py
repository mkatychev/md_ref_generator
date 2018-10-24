import sys
import unittest
import generate_refs as ref


class TestAnchor(unittest.TestCase):
    # format_achor unit test
    def test_anchor(self):
        self.assertEqual(ref.format_anchor(
            'Preventing Reference Cycles: Turning an Rc<T> into a Weak<T>'),
                    'preventing-reference-cycles-turning-an-rct-into-a-weakt')
    # it is necessary to strip nonalphas after the hypens to mirror present mdbook
    # functionality when a header string ends with a spaced separated nonalpha
    def anchor_nonalpha_end(self):
        self.assertEqual(ref.format_anchor('Specify multiple traits with +'),
                     'specify-multiple-traits-with-')


class TestEntry(unittest.TestCase):
    # create_entry unit test
    def test_entry(self):
        _in = ('Using `Result<T, E>`\n in tests',
                             'ch11-01-writing-tests')
        _out = {
            'Using `Result<T, E>` in tests': {
                'filename': 'ch11-01-writing-tests',
                'anchor-id': 'using-resultt-e-in-tests'
            }
        }

        self.assertEqual(ref.create_entry(*_in), _out)


class TestInsertReference(unittest.TestCase):

    def line_differ(self, func_in, expected_out):
        for func, out in zip(func_in.splitlines(), expected_out.splitlines()):
            if func != out:
                print('function out:')
                print(func)
                print('expected output:')
                print(out)

    def test_insert_ref(self):
        self.maxDiff = None
        _in = ('ch11-01-writing-test', {
            'Concatenation with the `+` Operator or the `format!` Macro': {
                'filename': 'ch08-02-strings',
                'anchor-id': 'concatenation-with-the--operator-or-the-format-macro'
            }
        }, ("""You can also add a custom message to be printed with the failure message as
optional arguments to the `assert!`, `assert_eq!`, and `assert_ne!` macros. Any
arguments specified after the one required argument to `assert!` or the two
required arguments to `assert_eq!` and `assert_ne!` are passed along to the
`format!` macro (discussed in Chapter 8 in the “Concatenation with the `+`
Operator or the `format!` Macro” section), so you can pass a format string that
contains `{}` placeholders and values to go in those placeholders. Custom
messages are useful to document what an assertion means; when a test fails,
you’ll have a better idea of what the problem is with the code.[“Concatenation
with the `+` Operator or the `format!` Macro”]
"""))
        expected = ("""You can also add a custom message to be printed with the failure message as
optional arguments to the `assert!`, `assert_eq!`, and `assert_ne!` macros. Any
arguments specified after the one required argument to `assert!` or the two
required arguments to `assert_eq!` and `assert_ne!` are passed along to the
`format!` macro (discussed in Chapter 8 in the [“Concatenation with the `+`
Operator or the `format!` Macro”]
[concatenation-with-the--operator-or-the-format-macro]
section), so you can pass a format string that
contains `{}` placeholders and values to go in those placeholders. Custom
messages are useful to document what an assertion means; when a test fails,
you’ll have a better idea of what the problem is with the code.[“Concatenation
with the `+` Operator or the `format!` Macro”]

[concatenation-with-the--operator-or-the-format-macro]:
ch08-02-strings.html#concatenation-with-the--operator-or-the-format-macro
""")
        result = ref.insert_reference(*_in, ref.re_section)
        # self.line_differ(result, expected)
        try:
            self.assertEqual(result, expected)
        except AssertionError as e:
            # print(expected)
            raise e



# print(line_differ(insert_reference(*(test_insert), re_section), insert_out))

if __name__ == '__main__':
    unittest.main()
