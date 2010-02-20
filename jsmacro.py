#!/usr/bin/env python

__author__ = "Erik Smartt"
__copyright__ = "Copyright 2010, Erik Smartt"
__license__ = "MIT"
__version__ = "0.2.4"

from datetime import datetime
import getopt
import hashlib
import os
import re
import sys

class MacroEngine(object):
  """
  The MacroEngine is where the magic happens. It defines methods that are called
  to handle the macros found in a document.
  """
  def __init__(self, macro_char):
    self.reset()
    self.macro_char = macro_char

  def reset(self):
    self.env = {}

  def handle_define(self, key, value=1):
    self.env[key] = eval(value)

  def handle_if(self, arg, text):
    """
    Returns the text to output based on the value of 'arg'.  E.g., if arg evaluates to false,
    expect to get an empty string back.

    @param    arg    String    Statement found after the 'if'. Currently expected to be a variable (i.e., key) in the env dictionary.
    @param    text   String    The text found between the macro statements
    """
    # To handle the '//@else' statement, we'll split text on the statement.
    parts = text.split('//%selse' % (self.macro_char))

    try:
      if (self.env[arg]):
        return "\n%s" % parts[0]
      else:
        try:
          return "%s" % parts[1]
        except IndexError:
          return ''
    except KeyError:
      return "\n%s" % text

  def handle_ifdef(self, arg, text):
    """
    @param    arg    String    Statement found after the 'ifdef'. Currently expected to be a variable (i.e., key) in the env dictionary.
    @param    text   String    The text found between the macro statements
    
    An ifdef is true if the variable 'arg' exists in the environment, regardless of whether
    it resolves to True or False.
    """
    parts = text.split('//%selse' % (self.macro_char))

    if (self.env.has_key(arg)):
      return "\n%s" % parts[0]
    else:
      try:
        return "%s" % parts[1]
      except IndexError:
        return ''

  def handle_ifndef(self, arg, text):
    """
    @param    arg    String    Statement found after the 'ifndef'. Currently expected to be a variable (i.e., key) in the env dictionary.
    @param    text   String    The text found between the macro statements
    
    An ifndef is true if the variable 'arg' does not exist in the environment.
    """
    parts = text.split('//%selse' % (self.macro_char))

    if (self.env.has_key(arg)):
      try:
        return "%s" % parts[1]
      except IndexError:
        return ''
    else:
      return "\n%s" % parts[0]

  def handle_macro(self, mo):
    #print "1: %s" % mo.group(1)
    #print "2: %s" % mo.group(2)
    #print "3: %s" % mo.group(3)
    #print "4: %s" % mo.group(4)
    #print "5: %s" % mo.group(5)
    method = mo.group(2)
    args = mo.group(3).strip()
    code = "\n%s" % mo.group(4)

    #print "call handle_%s(%s)" % (method, args)

    # This is a fun line.  We construct a method name using the
    # string found in the regex, and call that method on self
    # with the arguments we have.  So, we can dynamically call
    # methods... (and eventually, we'll support adding methods
    # at runtime :-)
    return getattr(self, "handle_%s" % method)(args, code)

class Parser(object):
  def __init__(self, macro_char='@', save_expected_failures=0):
    self.macro_char = macro_char # This allows overridding (possibly using '#' instead)

    self.macro_engine = MacroEngine(self.macro_char)

    self.save_expected_failures = save_expected_failures

    # Now that we know the macro_char, we can compile the main patterns
    self.re_define_macro = re.compile("(\s*\/\/\%sdefine\s*)(\w*)\s*(\w*)" % (self.macro_char), re.I)
    
    self.re_date_sub_macro = re.compile("%s\_\_date\_\_" % (self.macro_char))
    self.re_time_sub_macro = re.compile("%s\_\_time\_\_" % (self.macro_char))
    self.re_datetime_sub_macro = re.compile("%s\_\_datetime\_\_" % (self.macro_char))

    # A wrapped macro takes the following form:
    #
    # //@MACRO <ARGUMENTS>
    # ...some code
    # //@end
    self.re_wrapped_macro = re.compile("(\s*\/\/\%s)([a-z]+)\s+(\w*?\s)(.*?)(\s*\/\/\%send)" % (self.macro_char, self.macro_char), re.M|re.S)

  def _scan_for_test_files(self, arg, dirname, names):
    for in_filename in names:
      if in_filename.endswith('in.js'):
        in_file_path = "%s/%s" % (dirname, in_filename)
        out_file_path = "%s/%s" % (dirname, "%sout.js" % (in_filename[:-5]))

        in_parsed = self.parse(in_file_path)
        
        out_file = open(out_file_path, 'r')
        out_target_output = out_file.read()
        out_file.close()

        # Hopefully this doesn't come back to bite me, but I'm using a hash of the
        # output to compare it with the known TEST PASS state.  The odds of a false
        # positive are pretty slim...
        if (hashlib.sha224(out_target_output).hexdigest() == hashlib.sha224(in_parsed).hexdigest()):
          print "PASS [%s]" % (in_file_path)
        else:
          print "FAIL [%s]" % (in_file_path)
          
          if self.save_expected_failures:
            # Write the expected output file for local diffing
            fout = open('%s_expected' % out_file_path, 'w')
            fout.write(in_parsed)
            fout.close()

          else:
            print "\n-- EXPECTED --\n%s" % (out_target_output)
            print "\n-- GOT --\n%s" % (in_parsed)

  def test(self):
    print "Testing..."
    os.path.walk('testfiles', self._scan_for_test_files, None)
    print "Done."

  def parse(self, file_name):
    self.macro_engine.reset()
    
    now = datetime.now()

    fp = open(file_name, 'r')
    text = fp.read()
    fp.close()

    # Replace supported __foo__ statements
    text = self.re_date_sub_macro.sub('%s' % (now.strftime("%b %d, %Y")),
      self.re_time_sub_macro.sub('%s' % (now.strftime("%I:%M%p")),
      self.re_datetime_sub_macro.sub('%s' % (now.strftime("%b %d, %Y %I:%M%p")), text)))

    # Parse for DEFINE statements
    for mo in self.re_define_macro.finditer(text):
      if mo:
        k = mo.group(2) # key
        v = mo.group(3) # value

        self.macro_engine.handle_define(k, v)

    # Delete the DEFINE statements
    text = self.re_define_macro.sub('', text)

    # Do the magic...
    text = self.re_wrapped_macro.sub(self.macro_engine.handle_macro, text)

    return text


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
  input_file = 0
  run_tests = False
  mc = '@'
  predefined = []
  save_expected_failures = False

  try:
    opts, args = getopt.getopt(sys.argv[1:], "hf:", ["help", "file=", "doc", "hash", "test", "todo", "def=", "savefail"])
  except getopt.GetoptError, err:
    print str(err)
    usage()
    sys.exit(2)

  for o,a in opts:
    if o in ["-h", "--help"]:
      usage()
      sys.exit(2)

    if o in ["--hash"]:
      mc = '#'
      continue

    if o in ["--doc"]:
      print __doc__
      sys.exit(2)

    if o in ["--todo"]:
      print __todo__
      sys.exit(2)

    if o in ["-f", "--file"]:
      input_file = a
      continue

    if o in ["--test"]:
      run_tests = True
      continue

    if o in ["--def"]:
      predefined.append(a)
      continue

    if o in ["--savefail"]:
      save_expected_failures = True
      continue

    else:
      assert False, "unhandled option"
      usage()
      sys.exit(2)

  p = Parser(macro_char=mc, save_expected_failures=save_expected_failures)
  
  for v in predefined:
    # This is a little ugly
    p.macro_engine.env[v] = 1

  if (run_tests):
    p.test()
  elif (input_file):
    print p.parse(input_file)


if __name__ == "__main__":
  main()
