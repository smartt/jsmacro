//@define FOO 1

var foo = function() {
  //@ifdef FOO
  alert('Foo is defined');
  //@else
  alert('Foo is NOT defined');
  //@end

  //@ifdef DEBUG
  alert("Debug is defined -- which it shouldn't be!");
  //@end
};
