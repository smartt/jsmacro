#!/usr/bin/env python

from datetime import datetime
import getopt
import os
import re
import shutil
import sys

__author__ = "Erik Smartt"
__copyright__ = "Copyright 2010-2011, Erik Smartt"
__license__ = "MIT"
__version__ = "0.2.18"

__usage__ = """Normal usage:
  jsmacro.py -f [INPUT_FILE_NAME] > [OUTPUT_FILE]

  Options:
   --def [VAR[=VALUE]]    Defines the supplied variable (with a default value of 0) in the parser environment.
   -f|--file [FILE]       Used to load a single input file.
   -s|--srcdir [DIR]      Used to process all files in the specified directory. Use with -d|--dstdir
   -d|--dstdir [DIR]      Used to output files processed using -s|--srcdir into the specified directory.
   -e|--exclude [DIR]     Exclude the files in [DIR] (relative to the directory given in -s|--srcdir).
   --help                 Prints this Help message.
   --savefail             Saves the parsed output of a failed test case to disk.
   --testall              Run the test suite.
   --test [NUM]           Run test number NUM only.
   --version              Print the version number of jsmacro being used.
"""

__credits__ = [
    'aliclark <https://github.com/aliclark>',
    'Rodney Lopes Gomes <https://github.com/rlgomes>',
    'Elan Ruusamae <https://github.com/glensc>',
]

DEFINE_DEFAULT = '0'


class MacroEngine(object):
    """
    The MacroEngine is where the magic happens. It defines methods that are called
    to handle the macros found in a document.
    """
    def __init__(self):
        self.save_failure_output = False

        self.re_else_pattern = '[\t ]*//[@#]else[\r]?[\n]'

        # Compile the main patterns
        self.re_define_macro = re.compile("([\t ]*//[@#]define[\t ]+)(\w+)([\t ]+(\w+))?[\r]?[\n]", re.I)
        self.re_define_cmdline_macro = re.compile("(\w+)[\=](\w+)", re.I)
        self.re_include_macro = re.compile("([\t ]*//[@#]include[\t ]+)([^\r\n]+)[\r]?[\n]", re.I)

        self.re_date_sub_macro = re.compile("[@#]__date__", re.I)
        self.re_time_sub_macro = re.compile("[@#]__time__", re.I)
        self.re_datetime_sub_macro = re.compile("[@#]__datetime__", re.I)
        self.re_file_sub_macro = re.compile("[@#]__file__", re.I)
        self.re_line_sub_macro = re.compile("[@#]__line__", re.I)

        self.re_stripline_macro = re.compile(".*//[@#]strip.*[\r]?[\n]", re.I)

        # A wrapped macro takes the following form:
        #
        # //@MACRO <ARGUMENTS>
        # ...some code
        # //@end
        self.re_wrapped_macro = re.compile("([\t ]*//[@#])([a-z]+)\s+([\w_]*?\s)(.*?)([\t ]*//[@#]end(if)?)\s*?[\r]?[\n]", re.M | re.S)

        self.reset()

    def reset(self):
        self.env = {}

    def do_define(self, key, value=DEFINE_DEFAULT):
        if key in self.env:
            return

        self.env[key] = eval(value)

    def do_include(self, mo):
        """
        Used to include an external (JavaScript) file.
        """
        arg = mo.group(2).strip()

        # open the file (relative to the src file we're working with)
        # run the parser over it
        # return the output
        return self.parse(os.path.realpath('{base}/{arg}'.format(base=self._basepath, arg=arg)))

    def handle_if(self, arg, text):
        """
        Returns the text to output based on the value of 'arg'.  E.g., if arg evaluates to false,
        expect to get an empty string back.

        @param    arg    String    Statement found after the 'if'. Currently expected to be a variable (i.e., key) in the env dictionary.
        @param    text   String    The text found between the macro statements
        """
        # To handle the '//@else' statement, we'll split text on the statement.
        parts = re.split(self.re_else_pattern, text)

        try:
            if self.env[arg]:
                return "{s}".format(s=parts[0])

            else:
                try:
                    return "{s}".format(s=parts[1])

                except IndexError:
                    return ''

        except KeyError:
            print("  Error: {a} is not defined, using unmodified block.".format(a=arg))
            return "{s}".format(s=text)

    def handle_ifdef(self, arg, text):
        """
        @param    arg    String    Statement found after the 'ifdef'. Currently expected to be a variable (i.e., key) in the env dictionary.
        @param    text   String    The text found between the macro statements

        An ifdef is true if the variable 'arg' exists in the environment, regardless of whether
        it resolves to True or False.
        """
        parts = re.split(self.re_else_pattern, text)

        if arg in self.env:
            return "{s}".format(s=parts[0])

        else:
            try:
                return "{s}".format(s=parts[1])

            except IndexError:
                return ''

    def handle_ifndef(self, arg, text):
        """
        @param    arg    String    Statement found after the 'ifndef'. Currently expected to be a variable (i.e., key) in the env dictionary.
        @param    text   String    The text found between the macro statements

        An ifndef is true if the variable 'arg' does not exist in the environment.
        """
        parts = re.split(self.re_else_pattern, text)

        if arg in self.env:
            try:
                return "{s}".format(s=parts[1])

            except IndexError:
                return ''

        else:
            return "{s}".format(s=parts[0])

    def handle_macro(self, mo):
        method = mo.group(2)
        args = mo.group(3).strip()
        code = mo.group(4)

        # This is a fun line.  We construct a method name using the string found in the regex, and call that method on self
        # with the arguments we have.  So, we can dynamically call methods... (and eventually, we'll support adding methods
        # at runtime :-)
        return getattr(self, "handle_{m}".format(m=method))(args, code)

    def parse(self, file_name):
        now = datetime.now()

        # Save this for the @import implementation
        self._basepath = os.path.realpath(os.path.dirname(file_name))

        fp = open(file_name, 'r')
        text = fp.read()
        fp.close()

        # Replace supported __foo__ statements
        # Start with __line__ because it needs the un-preprocessed line number.
        # This code is more complicated than I would like.
        line_num = 1
        prevnl = -1
        while True:
            nextnl = text.find('\n', prevnl + 1)
            if nextnl < 0: break
            # split into before, after and curline
            before = text[:prevnl+1]
            after = text[nextnl+1:]
            curline = text[prevnl+1:nextnl+1]
            # do the replacement
            curline = self.re_line_sub_macro.sub('{l}'.format(l=line_num), curline)
            # put it back together
            text = before + curline + after
            # search again for the next newline since the line number is probably not as long as @__line__
            nextnl = text.find('\n', prevnl + 1)
            # set up next loop iteration
            prevnl = nextnl
            line_num = line_num + 1
        
        # Now replace all other __foo__ statements.
        # This is for __file__
        file_name_slashes = file_name
        file_name_slashes.replace('\\', '/')

        text = self.re_date_sub_macro.sub('{s}'.format(s=now.strftime("%b %d, %Y")),
            self.re_time_sub_macro.sub('{s}'.format(s=now.strftime("%I:%M%p")),
            self.re_datetime_sub_macro.sub('{s}'.format(s=now.strftime("%b %d, %Y %I:%M%p")),
            self.re_file_sub_macro.sub('{f}'.format(f=file_name_slashes), text))))

        # Parse for DEFINE statements
        for mo in self.re_define_macro.finditer(text):
            if mo:
                k = mo.group(2)  # key
                v = mo.group(3)  # value

                if v is None:
                    v = DEFINE_DEFAULT

                self.do_define(k, v)
                
        # Parse include statements
        text = self.re_include_macro.sub(self.do_include, text)

        # Delete the DEFINE statements
        text = self.re_define_macro.sub('', text)

        # Drop any lines containing a //@strip statement
        text = self.re_stripline_macro.sub('', text)

        # Do the magic...
        text = self.re_wrapped_macro.sub(self.handle_macro, text)

        return text


def scan_and_parse_dir(srcdir, destdir, excludes, parser):
    count = 0

    for root, dirs, files in os.walk(srcdir):
        dir = root[len(srcdir) + 1:]
        dir = dir.replace("\\","/")     # slash works just as well for Windows.

        # check if the dir is in excludes
        skip = False
        for e in excludes:
            if dir == e or dir.startswith(e + "/"):
                skip = True
                break
        
        if skip:
            continue
        
        in_path = srcdir
        out_path = destdir
        if dir != "":
            in_path = "{s}/{d}".format(s=srcdir, d=dir)
            out_path = "{s}/{d}".format(s=destdir, d=dir)

        for filename in files:
            
            in_file_path = "{p}/{f}".format(p=in_path, f=filename)
            out_file_path = "{p}/{f}".format(p=out_path, f=filename)

            if not(os.path.exists(out_path)):
                os.makedirs(out_path)

            # Copy non-js files to the output dir, even though we're not going to process them.  This is useful in
            # production environments where you might have other needed media files mixed-in with your JavaScript.
            if not(filename.endswith('.js')):
                shutil.copy(in_file_path, out_file_path)
                print("Copying {i} -> {o}".format(i=in_file_path, o=out_file_path))
                continue

            print(("Processing {i} -> {o}".format(i=in_file_path, o=out_file_path)))

            data = parser.parse(in_file_path)
            outfile = open(out_file_path, 'w')
            outfile.write(data)
            outfile.close()

            count += 1

    print(("Processed {c} files.".format(c=count)))


# ---------------------------------
#          TEST
# ---------------------------------
def scan_for_test_files(dirname, parser, test_index):
    num_pass = 0
    num_fail = 0
    num_tests = 0
    for root, dirs, files in os.walk(dirname):
        for in_filename in files:
            if in_filename.endswith('in.js'):
                num_tests = num_tests + 1
                if test_index >= 0:
                    if test_index != (num_tests - 1):
                        continue
                    
                in_file_path = "{d}/{f}".format(d=dirname, f=in_filename)
                out_file_path = "{d}/{f}out.js".format(d=dirname, f=in_filename[:-5])

                in_parsed = parser.parse(in_file_path)

                out_file = open(out_file_path, 'r')
                out_target_output = out_file.read()
                out_file.close()

                expect_failure = False
                if "always_fail" in in_file_path:
                    expect_failure = True

                if out_target_output == in_parsed:
                    if expect_failure:
                        print(("Test {n} - FAIL [{s}]".format(n=num_tests-1,s=in_file_path)))
                        num_fail = num_fail+1
                    else:
                        print(("Test {n} - PASS [{s}]".format(n=num_tests-1,s=in_file_path)))
                        num_pass = num_pass+1
                else:
                    if expect_failure:
                        print(("Test {n} - PASS [{s}]".format(n=num_tests-1,s=in_file_path)))
                        num_pass = num_pass+1
                    else:
                        print(("Test {n} - FAIL [{s}]".format(n=num_tests-1,s=in_file_path)))
                        num_fail = num_fail+1

                if (out_target_output == in_parsed) == expect_failure:
                    if parser.save_failure_output:
                        # Write the expected output file for local diffing
                        fout = open('{s}_expected'.format(s=out_file_path), 'w')
                        fout.write(in_parsed)
                        fout.close()

                    else:
                        print(("\n-- EXPECTED --\n{s}".format(s=out_target_output)))
                        print(("-- GOT --\n{s}".format(s=in_parsed)))

                parser.reset()

    print(("\n{t} tests - {r}% passed ({p} passed, {f} failed)".format(t=num_pass + num_fail, p=num_pass, f=num_fail, r=(num_pass / float(num_pass + num_fail) * 100.0))))



# --------------------------------------------------
#               MAIN
# --------------------------------------------------
if __name__ == "__main__":
    p = MacroEngine()

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                               "hf:s:d:e:",
                               ["help", "file=", "srcdir=", "dstdir=", "exclude=", "test=", "testall", "def=", "savefail", "version"])

    except getopt.GetoptError as err:
        print((str(err)))
        print(__usage__)

        sys.exit(2)

    # First handle commands that exit
    for o, a in opts:
        if o in ["-h", "--help"]:
            print(__usage__)

            sys.exit(0)

        if o in ["--version"]:
            print(__version__)

            sys.exit(0)

    # Next, handle commands that config
    for o, a in opts:
        if o in ["--def"]:
            res = p.re_define_cmdline_macro.match(a)
            p.do_define(res.group(1), res.group(2))
            continue

        if o in ["--savefail"]:
            p.save_failure_output = True
            continue

    srcdir = None
    dstdir = None
    excludes = []

    for o, a in opts:
        if o in ["-e", "--exclude"]:
            excludes.append(a)
    
    # Now handle commands the execute based on the config
    for o, a in opts:
        if o in ["-s", "--srcdir"]:
            srcdir = a

        if o in ["-d", "--dstdir"]:
            dstdir = a

            if srcdir == None:
                raise Exception("you must set the srcdir when setting a dstdir.")

            else:
                scan_and_parse_dir(srcdir, dstdir, excludes, p)

            break

        if o in ["-f", "--file"]:
            print((p.parse(a)))

            break

        if o in ["--test"]:
            print("Running only test {a}.".format(a=a))
            scan_for_test_files("testfiles", p, int(a))
            print("Done.")
            break

        if o in ["--testall"]:
            print("Running all tests.")
            scan_for_test_files("testfiles", p, -1)
            print("Done.")
            break

    sys.exit(0)
