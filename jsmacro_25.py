#!/usr/bin/env python

#
#
# This older snapshot is Python 2.5 compatible, whereas the main jsmacro.py targets
# Python 2.6 and newer (including Python 3.)  There are no guarentees that this
# version will be kept feature-complete in the future, but it may buy you some time
# if you need jsmacro.py in production.
#
#

from datetime import datetime
import getopt
import os
import re
import sys

__author__ = "Erik Smartt"
__copyright__ = "Copyright 2010, Erik Smartt"
__license__ = "MIT"
__version__ = "0.2.11.2"
__usage__ = """Normal usage:
  jsmacro.py -f [INPUT_FILE_NAME] > [OUTPUT_FILE]

  Options:
     --def [VAR]   Sets the supplied variable to True in the parser environment.
     --file [VAR]  Same as -f; Used to load the input file.
     --help        Prints this Help message.
     --savefail    Saves the expected output of a failed test case to disk.
     --test        Run the test suite.
     --version     Print the version number of jsmacro being used."""



class MacroEngine(object):
  """
  The MacroEngine is where the magic happens. It defines methods that are called
  to handle the macros found in a document.
  """
  def __init__(self):
    self.save_expected_failures = False

    self.re_else_pattern = '//[\@|#]else'

    # Compile the main patterns
    self.re_define_macro = re.compile("(\s*\/\/[\@|#]define\s*)(\w*)\s*(\w*)", re.I)

    self.re_date_sub_macro = re.compile("[\@|#]\_\_date\_\_", re.I)
    self.re_time_sub_macro = re.compile("[\@|#]\_\_time\_\_", re.I)
    self.re_datetime_sub_macro = re.compile("[\@|#]\_\_datetime\_\_", re.I)

    self.re_stripline_macro = re.compile(".*\/\/[\@|#]strip.*", re.I)

    # A wrapped macro takes the following form:
    #
    # //@MACRO <ARGUMENTS>
    # ...some code
    # //@end
    self.re_wrapped_macro = re.compile("(\s*\/\/[\@|#])([a-z]+)\s+(\w*?\s)(.*?)(\s*\/\/[\@|#]end(if)?)", re.M|re.S)

    self.reset()

  def reset(self):
    self.env = {}

  def handle_define(self, key, value='1'):
    if (self.env.has_key(key)):
      return

    self.env[key] = eval(value)

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
    parts = re.split(self.re_else_pattern, text)

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
    parts = re.split(self.re_else_pattern, text)

    if (self.env.has_key(arg)):
      try:
        return "%s" % parts[1]
      except IndexError:
        return ''
    else:
      return "\n%s" % parts[0]

  def handle_macro(self, mo):
    method = mo.group(2)
    args = mo.group(3).strip()
    code = "\n%s" % mo.group(4)

    # This is a fun line.  We construct a method name using the
    # string found in the regex, and call that method on self
    # with the arguments we have.  So, we can dynamically call
    # methods... (and eventually, we'll support adding methods
    # at runtime :-)
    return getattr(self, "handle_%s" % method)(args, code)


  def parse(self, file_name):
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

        self.handle_define(k, v)

    # Delete the DEFINE statements
    text = self.re_define_macro.sub('', text)

    # Drop any lines containing a //@strip statement
    text = self.re_stripline_macro.sub('', text)

    # Do the magic...
    text = self.re_wrapped_macro.sub(self.handle_macro, text)

    return text

def scan_and_parse_dir(srcdir, destdir, parser):
    
  for root, dirs, files in os.walk(srcdir):
    for filename in files:
        
        if not(filename.endswith('.js')):
            continue
        
        dir = root[len(srcdir)+1:] 
        
        if srcdir != root:
            dir = dir + '/'
            
        inpath = "%s/%s" % (srcdir, dir)
        outpath = "%s/%s" % (destdir, dir)
        
        in_file_path = "%s%s" % (inpath, filename)
        out_file_path = "%s%s" % (outpath, filename)
        print("%s -> %s", in_file_path, out_file_path) 

        if not(os.path.exists(outpath)):
            os.mkdir(outpath)
            
        data = parser.parse(in_file_path)
        outfile = open(out_file_path,'w')
        outfile.write(data)
        outfile.close()

# ---------------------------------
#          MAIN
# ---------------------------------

def scan_for_test_files(dirname, parser):
  for root, dirs, files in os.walk(dirname):
    for in_filename in files:
      if in_filename.endswith('in.js'):
        in_file_path = "%s/%s" % (dirname, in_filename)
        out_file_path = "%s/%s" % (dirname, "%sout.js" % (in_filename[:-5]))

        in_parsed = parser.parse(in_file_path)

        out_file = open(out_file_path, 'r')
        out_target_output = out_file.read()
        out_file.close()

        if (out_target_output == in_parsed):
          print "PASS [%s]" % (in_file_path)
        else:
          print "FAIL [%s]" % (in_file_path)

          if parser.save_expected_failures:
            # Write the expected output file for local diffing
            fout = open('%s_expected' % out_file_path, 'w')
            fout.write(in_parsed)
            fout.close()

          else:
            print "\n-- EXPECTED --\n%s" % (out_target_output)
            print "\n-- GOT --\n%s" % (in_parsed)

        parser.reset()


# --------------------------------------------------
#               MAIN
# --------------------------------------------------
if __name__ == "__main__":
  p = MacroEngine()

  try:
    opts, args = getopt.getopt(sys.argv[1:],
                               "hf:s:d:",
                               ["help", "file=", "srcdir=","dstdir=", "test", "def=", "savefail", "version"])
  except getopt.GetoptError, err:
    print str(err)
    print __usage__
    sys.exit(2)


  # First handle commands that exit
  for o, a in opts:
    if o in ["-h", "--help"]:
      print __usage__
      sys.exit(0)

    if o in ["--version"]:
      print __version__
      sys.exit(0)


  # Next, handle commands that config
  for o, a in opts:
    if o in ["--def"]:
      p.handle_define(a)
      continue

    if o in ["--savefail"]:
      p.save_expected_failures = True
      continue

  srcdir = None
  dstdir = None
  # Now handle commands the execute based on the config
  for o, a in opts:
      
    if o in ["-s", "--srcdir"]:
        srcdir = a
        
    if o in ["-d", "--dstdir"]:
        dstdir = a
        if srcdir == None:
            raise Exception("you must set the srcdir when setting a dstdir.")
        else:
            scan_and_parse_dir(srcdir, dstdir, p)
        break
        
    if o in ["-f", "--file"]:
      print p.parse(a)
      break

    if o in ["--test"]:
      print "Testing..."
      scan_for_test_files("testfiles", p)
      print "Done."
      break

  sys.exit(0)
