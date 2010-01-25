//@define DEBUG 0

var foo = function() {
  //@if DEBUG
  alert('starting...');
  //@end

  var bar = "Hello World";

  //@if DEBUG
  alert('This.');
  alert('That.');
  //@end
};
