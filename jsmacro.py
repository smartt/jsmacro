#!/usr/bin/env python

__author__ = "Erik Smartt"
__copyright__ = "Copyright 2010, Erik Smartt"
__license__ = "MIT"
__version__ = "0.2.1"

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
  def __init__(self):
    self.reset()

  def reset(self):
    self.env = {}
    #print "MacroEngine.env is now: %s" % (self.env)

  def handle_define(self, key, value):
    self.env[key] = eval(value)
    #print "MacroEngine.env is now: %s" % (self.env)

  def handle_if(self, arg, text):
    """
    @param    arg    String    Statement found after the 'if'. Currently expected to be a variable (i.e., key) in the env dictionary.
    @param    text   String    The text found between the macro statements
    """
    # Basically, we evaluate 'arg', and if it's True, we keep 'text'.  If not,
    # 'text' is stripped from the output.  Since we want to do this without
    # side-effects, we'll return 'text' arg is True, otherwise we return an
    # empty string.  In other words, we return the text to output based on how
    # we process the macro.
    #print "MacroEngine::handle_if(arg='%s')" % (arg)
    
    try:
      #print "self.env[arg] -> %s" % (self.env[arg])
      
      if (self.env[arg]):
        return "\n%s" % text
      else:
        return ''
    except KeyError:
      return "\n%s" % text

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
    # methods... (and evantually, we'll be adding methods at
    # runtime :-)
    return getattr(self, "handle_%s" % method)(args, code)

class Parser(object):
  def __init__(self, macro_char='@'):
    self.macro_engine = MacroEngine()
    
    self.macro_char = macro_char # This allows overridding (possibly using '#' instead)

    # Now that we know the macro_char, we can compile the main patterns
    self.re_define_macro = re.compile("(\s*\/\/\%sdefine\s*)(\w*)\s*(\w*)" % (self.macro_char), re.I)

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
          print "\n-- EXPECTED --\n%s" % (out_target_output)
          print "\n-- GOT --\n%s" % (in_parsed)

  def test(self):
    print "Testing..."
    os.path.walk('testfiles', self._scan_for_test_files, None)
    print "Done."

  def parse(self, file_name):
    #print "\n-----------------\nParser::parse(%s)" % (file_name)

    self.macro_engine.reset()

    fp = open(file_name, 'r')
    text = fp.read()
    fp.close()

    # Parse for DEFINE statements
    for mo in self.re_define_macro.finditer(text):
      #mo = self.re_define_macro.search(text)

      if mo:
        k = mo.group(2) # key
        v = mo.group(3) # value

        #print "MacroEngine::handle_define(): %s -> %s" % (k, v)
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

  try:
    opts, args = getopt.getopt(sys.argv[1:], "hf:", ["help", "file=", "doc", "hash", "test", "todo"])
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

    elif o in ["-f", "--file"]:
      input_file = a
      continue

    if o in ["--test"]:
      run_tests = True
      continue

    else:
      assert False, "unhandled option"
      usage()
      sys.exit(2)

  p = Parser(macro_char=mc)

  if (run_tests):
    p.test()
  elif (input_file):
    print p.parse(input_file)


if __name__ == "__main__":
  main()
