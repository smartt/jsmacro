//@define FOO 1
//@define BAR 1

var foo = function() {
  //@ifdef FOO
  alert('Foo is defined');
  //@endifdef

  //@ifdef FOO or DEBUG
  alert('Foo or DEBUG is defined');
  //@endifdef

  //@ifdef DEBUG
  alert("Debug is defined -- which it shouldn't be!");
  //@endifdef

  //@ifdef FOO or BAR
  alert('Foo or Bar is defined');
  //@end

  //@ifdef DEBUG or BAR
  alert('Bar is defined');
  //@endifdef
};
