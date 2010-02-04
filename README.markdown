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
  
jsmacro currently only supports @define and @if statements.  (Which can also be written as #define and #if, if that makes you more comfortable, but you'll need to pass the --hash argument from the command-line.)


Why bother
----------
1. Conditional "compiling" allows one to leave in test/debug/logging/etc. for development and debugging, and have it automatically removed in production builds.  Used well, it can offer a productivity boost.
2. Traditional C-preprocessor syntax isn't valid JavaScript.  The "//@" syntax used by jsmacro is valid JavaScript, thus source files run just fine in the browser without needing preprocssing.  (i.e., The original source files are what you use in development, and crunch with jsmacro only for creating production releases.)


To Do
-----
 - allow defining variables from command-line. (useful for producing different builds, e.g., an IE6 build vs. big-boy browsers)
 - a macro to define new macros at runtime (e.g., defining a macro within the source JavaScript)
 - handle_ifdef (which is very similar to handle_if)
 - handle_ifndef
 - handle else statements
 - ability to use define for replacements
 - handle_inline (replacing calls to a function with inline code)
 - handle __date__, __time__, and __timestamp__
