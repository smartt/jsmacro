//@define FOO 1

var foo = function() {
  alert('//@ifdef FOO Foo is defined//@endifdef');
  alert('//@ifdef FOO Foo is defined//@else Foo is not defined//@endifdef');
};
