// kitchen-sink-in.js line 1

// Blah PASS

var foo = function() {
  alert('A basic define value. This line should be in the output.');

  var bar = "This line has no macro influencing it, thus should be visible.";

  alert('Foo or BAR is defined so this line should be in the output.');
};
