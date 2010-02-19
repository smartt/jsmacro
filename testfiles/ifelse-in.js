//@define DEBUG 1

var foo = function() {
  //@if DEBUG
  alert('Debug is set');
  //@else
  alert('No debug for you');
  //@end

  var bar = "Hello World";
};
