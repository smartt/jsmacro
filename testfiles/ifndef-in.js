//@define FOO 1

var foo = function() {
  //@ifndef FOO
  alert("Foo is defined -- so this shouldn't be here!");
  //@end

  //@ifndef DEBUG
  alert("Debug is not defined -- so we're cool.");
  //@end
};
