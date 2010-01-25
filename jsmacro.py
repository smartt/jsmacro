#!/usr/bin/env python

__author__ = "Erik Smartt"
__copyright__ = "Copyright 2010, Erik Smartt"
__license__ = "MIT"
__version__ = "0.1"
__doc__ = """  jsmacro is pre-processor for JavaScript.  (Where "macro" leans more toward
  the C definition of a macro than the Lisp definition.)

  This library has nothing glamorous to offer, but does it's job.  It goes
  line-by-line, top-to-bottom, scanning each line and deciding what to do next.

  This tool was (quickly) developed to meet a desire to strip Debug and Test
  code from production JavaScript files in an automated manner (thus reducing
  a little burden on developers, and encouraging the inclusion of tests in
  one's code.)

  = Example 1: DEBUG set to True. The macro definitions are removed, but the
  debug code is left in-tact. =
  == Source JavaScript ==
  //@define DEBUG 1

  var foo = function() {
    //@if DEBUG
    alert('This.');
    alert('That.');
    //@end

    print "Hi";
  };


  == Resulting JavaScript ==
  var foo = function() {
    alert('This.');
    alert('That.');

    print "Hi";
  };


  = Example 2: DEBUG set to False. The macro definitions and contents are
  removed. =
  == Source JavaScript ==
  //@define DEBUG 0

  var foo = function() {
    //@if DEBUG
    alert('This.');
    alert('That.');
    //@end

    print "Hi";
  };


  == Resulting JavaScript ==
  var foo = function() {

    print "Hi";
  };


  jsmacro doesn't bother to clean up extra whitespace or linebreaks that result
  in macro parsing, since that's the job of a JavaScript minifier (which in my
  case, is the tool that runs next in my build process, right after jsmacro.)
  
  jsmacro currently only supports @define and @if statements.  (Which can also
  be written as #define and #if, if that makes you more comfortable, but you'll
  need to pass the --hash argument from the command-line.)
  
  = Why bother =
  (1) Conditional "compiling" allows one to leave in test/debug/logging/etc. 
  for development and debugging, and have it automatically removed in production
  builds.  Used well, it can offer a productivity boost.
  
  (2) Traditional C-preprocessor syntax isn't valid JavaScript.  The "//@"
  syntax used by jsmacro is valid JavaScript, thus source files run just fine
  in the browser without needing preprocssing.  (i.e., The original source
  files are what you use in development, and crunch with jsmacro only for
  creating production releases.)


"""
import getopt
import re
import sys

MACRO_CHAR = '@'

re_define_macro = None
re_if_macro = None
re_end_macro = None

ENV = {}

echo_line = True
is_in_block = False # Used by macro that acts on multiline statements (like @if...@end)
ignore_next_end_tag = False

def init():
  # Using a bunch of globals is lame, but what's the alternative? An Object
  # is overkill, and just using a global dictionary is seems wasteful.
  global ENV
  global MACRO_CHAR
  global re_define_macro, re_if_macro, re_end_macro

  ENV = {}

  # //@define FOO 1
  re_define_macro = re.compile("(\s*\/\/\%sdefine\s*)(\w*)\s*(\w*)" % (MACRO_CHAR), re.I)

  # //@if FOO
  re_if_macro = re.compile("(\s*\/\/\%sif\s*)(\w*)" % (MACRO_CHAR), re.I)

  # //@end
  re_end_macro = re.compile("\s*\/\/\%send" % (MACRO_CHAR), re.I)


def parse_define_macros(line):
  """
  The parser builds a dictionary of environment variables (which can be defined
  in a config file, on the command line, or via @define statements.)  @define
  adds to the environment variables, and will override pre-existing variable
  values.

  Format:
    //@define <var> (<value>)

  Example:
    //@define DEBUG 1

  """
  global ENV
  global re_define_macro

  # Look for the pattern on the line.  If found, extract the key and value, and
  # save to the global environment.
  mo = re_define_macro.search(line)

  if mo:
    k = mo.group(2)
    v = mo.group(3)

    if (v == '0'):
      v = 0
    elif (v == '1'):
      v = 1

    ENV[k] = v
    # False test the file parser *not* to include this line in the output
    return False

  # True tells the file parser to include this line in the output
  return True


def parse_if_statements(line):
  """
  Look for @if <var> ... and @end macros.  If the if-statement resolved to
  true, strip the macro, but leave the code between it and the @end.  If the
  if-statement resolves to false, strip the macro AND the code between it and
  the @end.

  If the variable in the if-statement is undefined, leave the macro and all
  code between it and the next @end.  (The assumption being that this macro
  might be for another system to parse.)
  """
  global is_in_block
  global ENV
  global ignore_next_end_tag
  global re_if_macro, re_end_macro

  # True tells the file parser to include this line in the output
  mo_if = re_if_macro.search(line)

  # If we got a match, decide what to do next by looking up the
  # key in the environment.
  if mo_if:
    try:
      val = ENV[mo_if.group(2)]
    except KeyError:
      # We don't have enaough info to process this line, so leave it be
      ignore_next_end_tag = True
      return True

    # If we got here, than we have a value for this...  Test it...
    if (val):
      # Leave this block in, but omit the macro line
      return False
    else:
      # Take this block out
      is_in_block = True
      return False

  else:
    # If we didn't see an @if statement, look for an @end statement
    mo_end = re_end_macro.search(line)

    if mo_end:
      if (ignore_next_end_tag):
        # We're in a mode that's ignoring this @end tag, so skip it
        ignore_next_end_tag = False
        return True

      # We're done with the block...
      is_in_block = False
      # But not ready to output this line
      return False

  return True

def parse_file(filename):
  global ENV

  init()

  output = []
  fp = open(filename, 'r')

  for l in fp.readlines():
    echo_line = parse_define_macros(l)

    # If it was a define macro, skip this line
    if not(echo_line):
      continue

    # Now look for @if macros
    echo_line = parse_if_statements(l)

    if (echo_line and not(is_in_block)):
      output.append(l)

  fp.close()

  return ''.join(output)

# ----------------------------
#          TESTING
# ----------------------------
def test():
  import hashlib

  def run_test_files(inf, outf):
    in_parsed = parse_file(inf)
    fp = open(outf ,'r')
    out_target_output = fp.read()
    fp.close()

    # Hopefully this doesn't come back to bite me, but I'm using a hash of the
    # output to compare it with the known TEST PASS state.  The odds of a false
    # positive are pretty slim...
    if (hashlib.sha224(out_target_output).hexdigest() == hashlib.sha224(in_parsed).hexdigest()):
      print "PASS [%s]" % (inf)
    else:
      print "FAIL [%s]" % (inf)
      print "\n-- EXPECTED --\n%s" % (out_target_output)
      print "\n-- GOT --\n%s" % (in_parsed)

  print "----------\nTESTING....\n-----------"
  # This really needs to be rewritten to just find every *-in.js file and
  # compare it's parsed output to the matching *-out.js file.  Manually
  # listing the test cases is lame.
  run_test_files("testfiles/no-macros-in.js", "testfiles/no-macros-out.js")
  run_test_files("testfiles/basic-debug-true-in.js", "testfiles/basic-debug-true-out.js")
  run_test_files("testfiles/basic-debug-false-in.js", "testfiles/basic-debug-false-out.js")
  run_test_files("testfiles/redefine-env-var-in.js", "testfiles/redefine-env-var-out.js")
  run_test_files("testfiles/unknown-if-var-in.js", "testfiles/unknown-if-var-out.js")

  print "----------\nDone.\n-----------"

# ---------------------------------
#          MAIN
# ---------------------------------
def usage():
  print "Normal usage:"
  print "   jsmacro.py -f INPUT_FILE_NAME > OUTPUT_FILE"
  print " "
  print "Options:"
  print "   --doc    Prints the module documentation."
  print "   --file   Same as -f; Used to load the input file."
  print "   --hash   Changes the macro indicator from '@' to '#' (i.e., more C-like.)"
  print "   --help   Prints this Help message."
  print "   --test   Run the test suite."


def main():
  global MACRO_CHAR

  input_file = 0

  try:
    opts, args = getopt.getopt(sys.argv[1:], "hf:", ["help", "file=", "doc", "hash", "test"])
  except getopt.GetoptError, err:
    print str(err)
    usage()
    sys.exit(2)

  for o,a in opts:
    if o in ["-h", "--help"]:
      usage()
      sys.exit(2)

    if o in ["--hash"]:
      MACRO_CHAR = '#'
      continue

    if o in ["--doc"]:
      print __doc__
      sys.exit(2)

    elif o in ["-f", "--file"]:
      input_file = a
      continue

    if o in ["--test"]:
      test()
      sys.exit(2)

    else:
      assert False, "unhandled option"
      usage()
      sys.exit(2)


  if (input_file):
    init()
    print parse_file(input_file)

if __name__ == "__main__":
  main()
