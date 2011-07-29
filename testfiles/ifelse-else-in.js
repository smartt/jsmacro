//@define DEBUG 0

var foo = function() {
  //@if DEBUG
  alert('Debug is set');
  //@else
  alert('No debug for you');
  //@end

  // Testing with @endif (new in 0.2.11)
  //@if DEBUG
  alert('Debug is set');
  //@else
  alert('No debug for you');
  //@endif

  var bar = "Hello World";
};
