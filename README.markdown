jsmacro
=======

Introduction
------------
jsmacro is pre-processor designed for use with JavaScript (where "macro" currently leans more toward the C definition of a macro than the Lisp definition.)

This tool was developed to meet a desire to strip Debug and Test code from production JavaScript files in an automated manner (thus reducing a little burden on developers, and encouraging the inclusion of tests in one's code.)

### Example 1: DEBUG set to True. The macro definitions are removed, but the debug code is left in-tact.

#### Source JavaScript
    //@define DEBUG 1

    var foo = function() {
      //@if DEBUG
      alert('This.');
      alert('That.');
      //@end

      print "Hi";
    };


#### Resulting JavaScript

    var foo = function() {
      alert('This.');
      alert('That.');

      print "Hi";
    };

### Example 2: DEBUG set to False. The macro definitions and contents are removed.

#### Source JavaScript
    //@define DEBUG 0

    var foo = function() {
      //@if DEBUG
      alert('This.');
      alert('That.');
      //@end

      print "Hi";
    };


#### Resulting JavaScript

    var foo = function() {

      print "Hi";
    };


jsmacro doesn't bother to clean up extra whitespace or line-breaks that result in macro parsing, since that's the job of a JavaScript minifier (which in my case, is the tool that runs next in my build process, right after jsmacro.)
  
Supported Macros
----------------

jsmacro currently supports:

 - //@define
 - //@if (with optional //@else)
 - //@ifdef (with optional //@else)
 - //@ifndef (with optional //@else)
 - //@strip

(Note that all macros can be written with a '//#' instead of a '//@', if that makes you more comfortable.)


Why bother?
-----------
1. Conditional "compiling" allows one to leave in test/debug/logging/etc. for development and debugging, and have it automatically removed in production builds.  Used well, it can offer a productivity boost.  Alternatively, one can use jsmacro to build target-specific JavaScript (e.g., perhaps doing string concatenation differently on IE6 than on Chrome.)
2. Traditional C-preprocessor syntax isn't valid JavaScript.  The "//@" syntax used by jsmacro is valid JavaScript, thus source files run just fine in the browser without needing preprocssing.  (i.e., The original source files are what you use in development, and crunch with jsmacro only for creating production releases.)


Why Python?
-----------
Besides being fun to use, Python is available on all of the development and deployment environments that I've used in the past who-knows-how-many years.  This is important, since it means not installing something new on servers (which might not be mine.)  While it might be fun to write this tool in another language, the one's I'm interested in aren't practical for a wider audience.  Perl, Python, and to some degree, Java, are a pretty safe bet for general use.

Note though, that the tool intentionally isn't called "pyjsmacro".  I'm perfectly happy having implementations in other languages, provided they all pass the same test cases.


Future Ideas
------------
 - A macro to define new macros at runtime (e.g., defining a macro within the source JavaScript)
 - The ability to use define for replacements
 - Handle_inline (replacing calls to a function with inline code)
 - Recursive macro expansion for nested macros


Changes
-------
v0.2.14

 - jsmacro.py now runs on Python 3.  Testing environments include: Python 2.6, Python 2.7, PyPy 1.6 (which is Python 2.7.1), and Python 3.2.

v0.2.10

 - Fixed a bug where a DEFINE on the command-line wasn't overriding a DEFINE in the input file.

v0.2.7 - v0.2.9

 - Pulled testing code out of the parser object and into functions that call the parser instead.
 - Merged the Parser and MacroEngine class, now that the test runner is no longer part of the parser.
 - Updated USAGE string to match recent changes.

v0.2.6

 - Added a //@strip macro that clears the containing line. Handy if you want to remove a line here or there, but don't want the visual clutter of the @if...@end wrappers.

v0.2.5

 - Dropped the "--hash" command-line flag, and instead, added '#' as a part of the regex.  (Meaning, both //@ and //# are supported by default.)

v0.2.4

 - Supports @\_\_date\_\_, @\_\_time\_\_, and @\_\_datetime\_\_ substitutions anywhere in the code

v0.2.3

 - Added support for @else clauses to @if, @ifdef, and @ifndef macros.

v0.2.2

 - Test files are now picked-up automatically when named correctly. This makes it painless to add more tests.
 - Added support for setting DEFINE flags from the command-line. Handy if you automate builds for different environments (like IE6 vs. the rest of the world.)
 - Added support for #ifdef and #ifndef
