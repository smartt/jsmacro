//@define FOO 1

var foo = function() {
  //@ifdef FOO
  alert('Foo is defined -- so we should see this line');
  //@end

  //@ifndef FOO
  alert('Foo is defined -- so we should NOT see this line');
  //@end

  //@ifdef DEBUG
  alert("Debug is not defined -- so we should not see this line");
  //@end

  //@ifndef DEBUG
  alert("Debug is not defined -- so we should see this line");
  //@end
};
