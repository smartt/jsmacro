//@define FOO 1
//@define BAR 0

var foo = function() {
  //@if (FOO or BAR)
  alert('PASS. Foo or Bar');
  //@end

  //@if (FOO and BAR)
  alert('FAIL. Foo and Bar');
  //@end

  //@if (FOO > BAR)
  alert('Pass. Foo > Bar');
  //@else
  alert('Fail. Foo > Bar');
  //@endif

  //@if (FOO < BAR)
  alert('Fail. Foo < Bar.');
  //@else
  alert('Pass. Foo < Bar.');
  //@end

  //@if (FOO == BAR)
  alert('Fail. Foo == Bar');
  //@else
  alert('Pass. Foo == Bar');
  //@endif
};
