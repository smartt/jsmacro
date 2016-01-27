//@define FOO 1
//@define BAR 0

var foo = function() {
  //@if (FOO or BAR)
  alert('PASS. Foo or Bar');
  //@end
};
