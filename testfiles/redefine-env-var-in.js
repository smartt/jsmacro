//@define DEBUG 0

var foo = function() {
  //@if DEBUG
  alert('starting...');
  //@end

  var bar = "Hello World";

  // This second define will be ignored
  //@define DEBUG 1

  //@if DEBUG
  alert('This.');
  alert('That.');
  //@end
};
