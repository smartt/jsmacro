//@define FOO 1

var foo = function() {
  //@ifndef FOO
  alert('Foo is NOT defined');
  //@else
  alert('Foo is defined');
  //@end

  //@ifdef DEBUG
  alert("Debug is defined -- which it shouldn't be!");
  //@end
};
