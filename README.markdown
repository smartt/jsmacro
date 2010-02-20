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
  
jsmacro currently only supports @define, @if, @ifdef, and @ifndef statements.  @if, @ifdef, and @ifndef also support @else clauses.  (All of which can be written with a '#' instead of a '@', if that makes you more comfortable, but you'll need to pass the --hash argument from the command-line.)


Why bother
----------
1. Conditional "compiling" allows one to leave in test/debug/logging/etc. for development and debugging, and have it automatically removed in production builds.  Used well, it can offer a productivity boost.  Alternatively, one can use jsmacro to build target-specific JavaScript (e.g., perhaps doing string concatenation differently on IE6 than on Chrome.)
2. Traditional C-preprocessor syntax isn't valid JavaScript.  The "//@" syntax used by jsmacro is valid JavaScript, thus source files run just fine in the browser without needing preprocssing.  (i.e., The original source files are what you use in development, and crunch with jsmacro only for creating production releases.)


To Do
-----
 - a macro to define new macros at runtime (e.g., defining a macro within the source JavaScript)
 - ability to use define for replacements
 - handle_inline (replacing calls to a function with inline code)

Changes
-------
v0.2.4
 - Supports @__date__, @__time__, and @__datetime__ substitutions anywhere in the code

v0.2.3

 - Added support for @else clauses to @if, @ifdef, and @ifndef macros.

v0.2.2

 - Test files are now picked-up automatically when named correctly. This makes it painless to add more tests.
 - Added support for setting DEFINE flags from the command-line. Handy if you automate builds for different environments (like IE6 vs. the rest of the world.)
 - Added support for #ifdef and #ifndef
